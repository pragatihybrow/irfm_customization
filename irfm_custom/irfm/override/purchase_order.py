import frappe
import json
from frappe.utils import flt
from frappe.utils import today, add_days, getdate

@frappe.whitelist()
def create_sales_order(doc, method):
    """Create a Sales Order when a Purchase Order is submitted, only if stock is fully available"""

    # Ensure SO is created only if PO is approved
    if doc.custom_states_ != "Approved":
        frappe.throw("Purchase Order is not fully approved. Cannot create Sales Order.")

    # Fetch the represents_company and is_internal_supplier field from Supplier
    supplier_details = frappe.get_value("Supplier", doc.supplier, ["represents_company", "is_internal_supplier"], as_dict=True)

    if not supplier_details:
        frappe.throw(f"Supplier {doc.supplier} not found.")

    represents_company = supplier_details.get("represents_company")
    is_internal_supplier = supplier_details.get("is_internal_supplier")

    # If is_internal_supplier is not checked, do not create the Sales Order
    if not is_internal_supplier:
        return  # Do nothing, let it follow the core functionality

    if not represents_company:
        frappe.throw(f"Supplier {doc.supplier} does not have a represents_company set.")

    # Get the default Sales Taxes and Charges Template for the represents_company
    taxes_template = frappe.get_value("Sales Taxes and Charges Template", 
                                      {"company": represents_company}, "name")

    # Create new Sales Order
    sales_order = frappe.get_doc({
        "doctype": "Sales Order",
        "customer": doc.custom_customers,  
        "company": represents_company,
        "po_no": doc.name,
        "po_date":doc.transaction_date,
        "transaction_date": doc.transaction_date,
        "delivery_date": doc.schedule_date,
        "currency": doc.currency,
        "taxes_and_charges": taxes_template,
        "set_warehouse": doc.custom_warehouse,
        "items": [],
        "taxes": []
    })

    # Ensure `set_warehouse` applies correctly
    sales_order.set_warehouse = doc.custom_warehouse

    # Map Purchase Order items to Sales Order items
    for item in doc.items:
        sales_order.append("items", {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "custom_item_barcode": item.custom_item_barcode,
            "description": item.description,
            "qty": item.qty,
            "uom": item.uom,
            "rate": item.rate,
            "amount": item.amount,
            "warehouse": item.custom_supplier_warehouse,
            "purchase_order": doc.name,
            "custom_bundle_sizeuom":item.custom_bundle_sizeuom,
            "custom_pack_size" :item.custom_pack_size,
            "custom_no_of_packs": item.custom_no_of_packs
        })

    # If a tax template is found, fetch and apply the taxes
    if taxes_template:
        tax_details = frappe.get_all("Sales Taxes and Charges", 
                                     filters={"parent": taxes_template}, 
                                     fields=["charge_type", "account_head", "rate", "description"])

        for tax in tax_details:
            sales_order.append("taxes", {
                "charge_type": tax.charge_type,
                "account_head": tax.account_head,
                "rate": tax.rate,
                "description": tax.description
            })

    # Save and submit the Sales Order
    sales_order.insert()
    sales_order.db_set("set_warehouse", doc.custom_warehouse)
    sales_order.save()
    sales_order.submit()

    frappe.msgprint(f"Sales Order {sales_order.name} created successfully for company {represents_company}!", alert=True)



@frappe.whitelist()
def update_custom_states(doc, method):
    import math
    doc = frappe.get_doc(doc) if isinstance(doc, str) else doc

    supplier_company = frappe.get_value("Supplier", doc.supplier, "custom_company")
    if not supplier_company:
        frappe.throw(f"Supplier {doc.supplier} does not have a linked company.")

    company_warehouses = frappe.get_all("Warehouse", filters={"company": supplier_company}, pluck="name")
    if not company_warehouses:
        frappe.throw(f"No warehouses found for company {supplier_company}")

    new_items = []

    for item in list(doc.items):  # Iterate over a copy
        item_code = item.item_code
        requested_qty = item.qty

        # Get all pack sizes and their stock
        stock_entries = frappe.db.sql(
            """
            SELECT pack_size, SUM(actual_qty) AS total_qty
            FROM `tabStock Ledger Entry`
            WHERE item_code = %(item_code)s
              AND warehouse IN %(warehouses)s
              AND is_cancelled = 0
            GROUP BY pack_size
            """,
            {
                "item_code": item_code,
                "warehouses": tuple(company_warehouses),
            },
            as_dict=True
        )

        pack_options = []
        for stock in stock_entries:
            pack_size = stock.pack_size
            stock_qty = stock.total_qty or 0
            pack_qty = frappe.get_value("Pack Size", pack_size, "quantity")
            if not pack_qty:
                continue
            num_packs = math.floor(stock_qty / pack_qty)
            total_pack_stock = num_packs * pack_qty
            pack_options.append({
                "pack_size": pack_size,
                "pack_qty": pack_qty,
                "stock_qty": stock_qty,
                "available_packs": num_packs,
                "total_pack_stock": total_pack_stock,
            })

        # Step 1: Try exact match with a single pack size
        exact_match_found = False
        for p in sorted(pack_options, key=lambda x: x["pack_qty"]):
            if requested_qty % p["pack_qty"] == 0:
                packs_needed = requested_qty // p["pack_qty"]
                if packs_needed <= p["available_packs"]:
                    new_item = item.as_dict().copy()
                    new_item["qty"] = requested_qty
                    new_item["custom_bundle_sizeuom"] = p["pack_size"]
                    new_item["custom_no_of_packs"] = packs_needed
                    new_item["custom_available_qty"] = p["stock_qty"]
                    new_item["custom_pack_size"] = p["pack_qty"]
                    new_item["custom_stock"] = "Available"
                    new_items.append(new_item)
                    doc.remove(item)
                    exact_match_found = True
                    break

        if exact_match_found:
            continue

        # Step 2: Try finding best combination <= requested_qty
        best_combo = []
        qty_used = 0
        remaining_qty = requested_qty

        for p in sorted(pack_options, key=lambda x: -x["pack_qty"]):  # largest pack size first
            if remaining_qty <= 0:
                break
            packs_to_use = min(math.floor(remaining_qty / p["pack_qty"]), p["available_packs"])
            if packs_to_use <= 0:
                continue
            used_qty = packs_to_use * p["pack_qty"]
            best_combo.append({
                "pack_size": p["pack_size"],
                "pack_qty": p["pack_qty"],
                "packs": packs_to_use,
                "qty": used_qty,
                "stock_qty": p["stock_qty"]
            })
            qty_used += used_qty
            remaining_qty -= used_qty

        if qty_used == 0:
            # No stock available at all
            unavailable_item = item.as_dict().copy()
            unavailable_item["qty"] = requested_qty
            unavailable_item["custom_bundle_sizeuom"] = None
            unavailable_item["custom_no_of_packs"] = 0
            unavailable_item["custom_available_qty"] = 0
            unavailable_item["custom_pack_size"] = 0
            unavailable_item["custom_stock"] = "Unavailable"
            new_items.append(unavailable_item)
            doc.remove(item)
            continue

        if qty_used != requested_qty:
            frappe.throw(
                f"To fulfill item {item_code}, please update quantity from {requested_qty} to {qty_used} to match available pack sizes."
            )

        # Step 3: Apply best combo
        doc.remove(item)
        for row in best_combo:
            new_item = item.as_dict().copy()
            new_item["qty"] = row["qty"]
            new_item["custom_bundle_sizeuom"] = row["pack_size"]
            new_item["custom_no_of_packs"] = row["packs"]
            new_item["custom_available_qty"] = row["stock_qty"]
            new_item["custom_pack_size"] = row["pack_qty"]
            new_item["custom_stock"] = "Available"
            new_items.append(new_item)

    # Replace existing items
    doc.set("items", [])
    for i in new_items:
        doc.append("items", i)

    total_items = len(doc.items)
    available_count = sum(1 for i in doc.items if i.custom_stock == "Available")
    doc.custom_states_ = "Approved" if available_count == total_items else "Pending For Approval"

# @frappe.whitelist()
# def update_custom_states(doc, method):
#     import math
#     doc = frappe.get_doc(doc) if isinstance(doc, str) else doc

#     supplier_company = frappe.get_value("Supplier", doc.supplier, "custom_company")
#     if not supplier_company:
#         frappe.throw(f"Supplier {doc.supplier} does not have a linked company.")

#     company_warehouses = frappe.get_all("Warehouse", filters={"company": supplier_company}, pluck="name")
#     if not company_warehouses:
#         frappe.throw(f"No warehouses found for company {supplier_company}")

#     new_items = []

#     for item in list(doc.items):  # Iterate over a copy
#         item_code = item.item_code
#         requested_qty = item.qty

#         # Get all pack sizes and their stock
#         stock_entries = frappe.db.sql(
#             """
#             SELECT pack_size, SUM(actual_qty) AS total_qty
#             FROM `tabStock Ledger Entry`
#             WHERE item_code = %(item_code)s
#               AND warehouse IN %(warehouses)s
#               AND is_cancelled = 0
#             GROUP BY pack_size
#             """,
#             {
#                 "item_code": item_code,
#                 "warehouses": tuple(company_warehouses),
#             },
#             as_dict=True
#         )

#         pack_options = []
#         for stock in stock_entries:
#             pack_size = stock.pack_size
#             stock_qty = stock.total_qty or 0
#             pack_qty = frappe.get_value("Pack Size", pack_size, "quantity")
#             if not pack_qty:
#                 continue
#             num_packs = math.floor(stock_qty / pack_qty)
#             total_pack_stock = num_packs * pack_qty
#             pack_options.append({
#                 "pack_size": pack_size,
#                 "pack_qty": pack_qty,
#                 "stock_qty": stock_qty,
#                 "available_packs": num_packs,
#                 "total_pack_stock": total_pack_stock,
#             })

#         # Step 1: Try exact match with a single pack size
#         exact_match_found = False
#         for p in sorted(pack_options, key=lambda x: x["pack_qty"]):
#             if requested_qty % p["pack_qty"] == 0:
#                 packs_needed = requested_qty // p["pack_qty"]
#                 if packs_needed <= p["available_packs"]:
#                     new_item = item.as_dict().copy()
#                     new_item["qty"] = requested_qty
#                     new_item["custom_bundle_sizeuom"] = p["pack_size"]
#                     new_item["custom_no_of_packs"] = packs_needed
#                     new_item["custom_available_qty"] = p["stock_qty"]
#                     new_item["custom_pack_size"] = p["pack_qty"]
#                     new_item["custom_stock"] = "Available"
#                     new_items.append(new_item)
#                     doc.remove(item)
#                     exact_match_found = True
#                     break

#         if exact_match_found:
#             continue

#         # Step 2: Try finding best combination <= requested_qty
#         best_combo = []
#         qty_used = 0
#         remaining_qty = requested_qty

#         for p in sorted(pack_options, key=lambda x: -x["pack_qty"]):  # largest pack size first
#             if remaining_qty <= 0:
#                 break
#             packs_to_use = min(math.floor(remaining_qty / p["pack_qty"]), p["available_packs"])
#             if packs_to_use <= 0:
#                 continue
#             used_qty = packs_to_use * p["pack_qty"]
#             best_combo.append({
#                 "pack_size": p["pack_size"],
#                 "pack_qty": p["pack_qty"],
#                 "packs": packs_to_use,
#                 "qty": used_qty,
#                 "stock_qty": p["stock_qty"]
#             })
#             qty_used += used_qty
#             remaining_qty -= used_qty

#         if qty_used == 0:
#             # No stock available at all
#             unavailable_item = item.as_dict().copy()
#             unavailable_item["qty"] = requested_qty
#             unavailable_item["custom_bundle_sizeuom"] = None
#             unavailable_item["custom_no_of_packs"] = 0
#             unavailable_item["custom_available_qty"] = 0
#             unavailable_item["custom_pack_size"] = 0
#             unavailable_item["custom_stock"] = "Unavailable"
#             new_items.append(unavailable_item)
#             doc.remove(item)
#             continue

#         if qty_used != requested_qty:
#             available_pack_sizes = ", ".join([f"{p['pack_qty']} ({p['pack_size']})" for p in pack_options])
#             frappe.throw(
#                 f"To fulfill item {item_code}, please add quantities corresponding to the following available pack sizes: {available_pack_sizes}."
#             )

#         # Step 3: Apply best combo
#         doc.remove(item)
#         for row in best_combo:
#             new_item = item.as_dict().copy()
#             new_item["qty"] = row["qty"]
#             new_item["custom_bundle_sizeuom"] = row["pack_size"]
#             new_item["custom_no_of_packs"] = row["packs"]
#             new_item["custom_available_qty"] = row["stock_qty"]
#             new_item["custom_pack_size"] = row["pack_qty"]
#             new_item["custom_stock"] = "Available"
#             new_items.append(new_item)

#     # Replace existing items
#     doc.set("items", [])
#     for i in new_items:
#         doc.append("items", i)

#     total_items = len(doc.items)
#     available_count = sum(1 for i in doc.items if i.custom_stock == "Available")
#     doc.custom_states_ = "Approved" if available_count == total_items else "Pending For Approval"



def get_next_available_schedule_day(start_date, selected_days):
    """
    Find the next available schedule day based on selected delivery days.
    """
    from datetime import timedelta
    current_date = getdate(start_date)

    while current_date.weekday() not in selected_days:
        current_date += timedelta(days=1)

    return current_date

@frappe.whitelist()
def set_schedule_date(doc):
    """
    Set the schedule_date when a customer is selected.
    Returns the calculated date to update the form immediately.
    """
    # Ensure doc is a Python dictionary (convert from JSON if needed)
    if isinstance(doc, str):
        doc = json.loads(doc)  # Convert JSON string to Python dict

    if not doc.get("custom_customers"):
        frappe.msgprint("No customer selected. Clearing schedule date.")
        return None

    # Fetch customer details
    customer = frappe.get_doc("Customer", doc.get("custom_customers"))
    if not customer:
        frappe.msgprint("Customer not found. Please check the selection.")
        return None

    # Get deadline time from customer, default to "06:00:00"
    deadline_time = customer.get("custom_deadline_time") or "06:00:00"

    # ✅ Ensure deadline_time is a string
    if isinstance(deadline_time, (int, float)):  
        deadline_time = f"{int(deadline_time)}:00:00"  # Convert to HH:MM:SS format
    elif isinstance(deadline_time, frappe.utils.datetime.timedelta):
        deadline_time = "06:00:00"  # Default fallback for timedelta values

    deadline_hour = int(str(deadline_time).split(":")[0])

    # Order placement time
    order_date = getdate(doc.get("transaction_date") or today())

    # Check current system time
    from datetime import datetime
    current_hour = datetime.now().hour

    # If order is placed after the deadline, move to next day
    if current_hour >= deadline_hour:
        order_date = add_days(order_date, 1)

    # Apply a minimum 3-day gap
    min_schedule_date = add_days(order_date, 3)

    # Fetch selected delivery days from customer
    days_mapping = {
        "custom_sunday": 6,
        "custom_monday": 0,
        "custom_tuesday": 1,
        "custom_wednesday": 2,
        "custom_thursday": 3,
        "custom_friday": 4,
        "custom_saturday": 5,
    }

    selected_days = [days_mapping[key] for key in days_mapping if customer.get(key)]

    if not selected_days:
        frappe.msgprint("Please select at least one delivery day in the Customer record.")
        return None

    # Find the next available schedule day
    next_schedule_day = get_next_available_schedule_day(min_schedule_date, selected_days)

    return next_schedule_day
