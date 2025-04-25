import frappe
import json
from frappe.utils import flt
from frappe.utils import today, add_days, getdate
from irfm_custom.utils.stock_utils import custom_get_available_batches

@frappe.whitelist()
def create_sales_order(doc, method):
    if isinstance(doc, str):
        doc = frappe.get_doc("Purchase Order", doc)

    # Check if the Purchase Order is approved
    if doc.custom_states_ != "Approved":
        frappe.throw("Purchase Order is not fully approved. Cannot create Sales Order.")

    supplier_details = frappe.get_value("Supplier", doc.supplier, ["represents_company", "is_internal_supplier"], as_dict=True)
    
    if not supplier_details or not supplier_details.is_internal_supplier:
        return

    represents_company = supplier_details.represents_company
    if not represents_company:
        frappe.throw(f"Supplier {doc.supplier} does not have a represents_company set.")

    # Get company abbreviations
    po_abbr = frappe.db.get_value("Company", doc.company, "abbr")
    so_abbr = frappe.db.get_value("Company", represents_company, "abbr")

    # Adjust the tax template if needed
    taxes_template = doc.taxes_and_charges
    if taxes_template and po_abbr and so_abbr:
        taxes_template = taxes_template.replace(f"- {po_abbr}", f"- {so_abbr}")

    # Create the Sales Order
    so = frappe.new_doc("Sales Order")
    so.update({
        "customer": doc.custom_customers,
        "company": represents_company,
        "po_no": doc.name,
        "po_date": doc.transaction_date,
        "transaction_date": doc.transaction_date,
        "delivery_date": doc.schedule_date,
        "currency": doc.currency,
        "set_warehouse": doc.custom_warehouse,
        "taxes_and_charges": taxes_template,
    })

    # Add items to the Sales Order
    for item in doc.items:
        so.append("items", {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "description": item.description,
            "custom_item_barcode": item.custom_item_barcode,
            "qty": item.qty,
            "uom": item.uom,
            "rate": item.rate,
            "amount": item.amount,
            "warehouse": item.custom_supplier_warehouse,
            "purchase_order": doc.name,
            "purchase_order_item":item.name,
            "custom_bundle_sizeuom": item.custom_bundle_sizeuom,
            "custom_pack_size": item.custom_pack_size,
            "custom_no_of_packs": item.custom_no_of_packs,
            "custom_batch_no":item.custom_batch_no
        })

    # Add taxes to the Sales Order if taxes_template exists
    if taxes_template:
        tax_details = frappe.get_all("Sales Taxes and Charges", 
                                     filters={"parent": taxes_template}, 
                                     fields=["charge_type", "account_head", "rate", "description"])

        for tax in tax_details:
            so.append("taxes", {
                "charge_type": tax.charge_type,
                "account_head": tax.account_head,
                "rate": tax.rate,
                "description": tax.description
            })

    # Set the tax category based on the state comparison
    if doc.custom_company_state and doc.custom_state:
        so.tax_category = "In State" if doc.custom_company_state == doc.custom_state else "Out State"

    # Insert the Sales Order, save, and submit
    so.insert(ignore_permissions=True)
    so.save()
    so.submit()

    # Display a success message
    frappe.msgprint(f"Sales Order {so.name} created successfully for company {represents_company}!", alert=True)




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

#     for item in list(doc.items):  # Iterate over a copy of the items list
#         item_code = item.item_code
#         requested_qty = item.qty
#         qty_used = 0
#         remaining_qty = requested_qty
#         fifo_combo = []

#         # Fetch FIFO-wise stock entries by posting_date, grouped by pack size
#         stock_entries = frappe.db.sql("""
#             SELECT sle.pack_size, SUM(sle.actual_qty) AS stock_qty, sle.warehouse, MIN(sle.posting_date) AS posting_date
#             FROM `tabStock Ledger Entry` sle
#             WHERE sle.item_code = %(item_code)s
#               AND sle.warehouse IN %(warehouses)s
#               AND sle.is_cancelled = 0
#             GROUP BY sle.pack_size, sle.warehouse
#             ORDER BY posting_date ASC
#         """, {
#             "item_code": item_code,
#             "warehouses": tuple(company_warehouses)
#         }, as_dict=True)

#         # If qty is exactly 1, just take the first available pack size
#         if requested_qty == 1 and stock_entries:
#             entry = stock_entries[0]
#             pack_size = entry.pack_size
#             stock_qty = entry.stock_qty
#             warehouse = entry.warehouse
#             pack_qty = frappe.get_value("Pack Size", pack_size, "quantity")

#             if pack_qty and stock_qty >= pack_qty:
#                 batches = get_batch_fifo_wise(item_code, warehouse, pack_size)
#                 new_item = item.as_dict().copy()
#                 new_item["qty"] = pack_qty
#                 new_item["custom_bundle_sizeuom"] = pack_size
#                 new_item["custom_no_of_packs"] = 1
#                 new_item["custom_available_qty"] = stock_qty
#                 new_item["custom_pack_size"] = pack_qty
#                 new_item["custom_stock"] = "Available"
#                 new_item["custom_batch_no"] = batches[0].batch_no if batches else ''
#                 new_item["custom_supplier_warehouse"] = warehouse
#                 new_items.append(new_item)
#                 continue  # skip the rest of logic for this item

#         # Standard handling for qty > 1
#         for entry in stock_entries:
#             pack_size = entry.pack_size
#             stock_qty = entry.stock_qty
#             warehouse = entry.warehouse
#             pack_qty = frappe.get_value("Pack Size", pack_size, "quantity")

#             if not pack_qty or stock_qty <= 0:
#                 continue

#             max_packs = math.floor(stock_qty / pack_qty)
#             usable_packs = min(math.floor(remaining_qty / pack_qty), max_packs)

#             if usable_packs <= 0:
#                 continue

#             used_qty = usable_packs * pack_qty
#             fifo_combo.append({
#                 "pack_size": pack_size,
#                 "pack_qty": pack_qty,
#                 "packs": usable_packs,
#                 "qty": used_qty,
#                 "stock_qty": stock_qty,
#                 "custom_supplier_warehouse": warehouse
#             })

#             qty_used += used_qty
#             remaining_qty -= used_qty

#             if remaining_qty <= 0:
#                 break

#         doc.remove(item)

#         if qty_used == 0:
#             # No usable stock found at all
#             unavailable_item = item.as_dict().copy()
#             unavailable_item["qty"] = requested_qty
#             unavailable_item["custom_bundle_sizeuom"] = None
#             unavailable_item["custom_no_of_packs"] = 0
#             unavailable_item["custom_available_qty"] = 0
#             unavailable_item["custom_pack_size"] = 0
#             unavailable_item["custom_stock"] = "Unavailable"
#             unavailable_item["custom_batch_no"] = ''
#             new_items.append(unavailable_item)
#             continue

#         # Use FIFO combo to create split items
#         for row in fifo_combo:
#             batches = get_batch_fifo_wise(item_code, row["custom_supplier_warehouse"], row["pack_size"])
#             new_item = item.as_dict().copy()
#             new_item["qty"] = row["qty"]
#             new_item["custom_bundle_sizeuom"] = row["pack_size"]
#             new_item["custom_no_of_packs"] = row["packs"]
#             new_item["custom_available_qty"] = row["stock_qty"]
#             new_item["custom_pack_size"] = row["pack_qty"]
#             new_item["custom_stock"] = "Available"
#             new_item["custom_batch_no"] = batches[0].batch_no if batches else ''
#             new_item["custom_supplier_warehouse"] = row["custom_supplier_warehouse"]
#             new_items.append(new_item)

#     # Replace items
#     doc.set("items", [])
#     for i in new_items:
#         doc.append("items", i)

#     total_items = len(doc.items)
#     available_count = sum(1 for i in doc.items if i.custom_stock == "Available")
#     doc.custom_states_ = "Approved" if available_count > 0 else "Pending For Approval"


@frappe.whitelist()
def update_custom_states(doc, method):
    import math
    doc = frappe.get_doc(doc) if isinstance(doc, str) else doc

    supplier_company = frappe.get_value("Supplier", doc.supplier, "custom_company")
    # if not supplier_company:
    #     frappe.throw(f"Supplier {doc.supplier} does not have a linked company.")

    company_warehouses = frappe.get_all("Warehouse", filters={"company": supplier_company}, pluck="name")
    # if not company_warehouses:
    #     frappe.throw(f"No warehouses found for company {supplier_company}")

    new_items = []

    for item in list(doc.items):  # Iterate over a copy of the items list
        item_code = item.item_code
        requested_qty = item.qty
        qty_used = 0
        remaining_qty = requested_qty
        fifo_combo = []

        # Fetch FIFO-wise stock entries by posting_date, grouped by pack size
        stock_entries = frappe.db.sql("""
            SELECT sle.pack_size, SUM(sle.actual_qty) AS stock_qty, sle.warehouse, MIN(sle.posting_date) AS posting_date
            FROM `tabStock Ledger Entry` sle
            WHERE sle.item_code = %(item_code)s
              AND sle.warehouse IN %(warehouses)s
              AND sle.is_cancelled = 0
            GROUP BY sle.pack_size, sle.warehouse
            ORDER BY posting_date ASC
        """, {
            "item_code": item_code,
            "warehouses": tuple(company_warehouses)
        }, as_dict=True)

        # If qty is exactly 1, just take the first available pack size
        if requested_qty == 1 and stock_entries:
            entry = stock_entries[0]
            pack_size = entry.pack_size
            stock_qty = entry.stock_qty
            warehouse = entry.warehouse
            pack_qty = frappe.get_value("Pack Size", pack_size, "quantity")

            if pack_qty and stock_qty >= pack_qty:
                batches = get_batch_fifo_wise(item_code, warehouse, pack_size)
                new_item = item.as_dict().copy()
                new_item["qty"] = pack_qty
                new_item["custom_bundle_sizeuom"] = pack_size
                new_item["custom_no_of_packs"] = 1
                new_item["custom_available_qty"] = stock_qty
                new_item["custom_pack_size"] = pack_qty
                new_item["custom_stock"] = "Available"
                new_item["custom_batch_no"] = batches[0].batch_no if batches else ''
                new_item["custom_supplier_warehouse"] = warehouse
                new_items.append(new_item)
                continue  # skip the rest of logic for this item

        # Standard handling for qty > 1
        for entry in stock_entries:
            pack_size = entry.pack_size
            stock_qty = entry.stock_qty
            warehouse = entry.warehouse
            pack_qty = frappe.get_value("Pack Size", pack_size, "quantity")

            if not pack_qty or stock_qty <= 0:
                continue

            # Ensure stock is updated after each deduction
            available_qty = stock_qty - qty_used  # Update based on remaining qty

            if available_qty <= 0:
                continue

            max_packs = math.floor(available_qty / pack_qty)
            usable_packs = min(math.floor(remaining_qty / pack_qty), max_packs)

            if usable_packs <= 0:
                continue

            used_qty = usable_packs * pack_qty
            fifo_combo.append({
                "pack_size": pack_size,
                "pack_qty": pack_qty,
                "packs": usable_packs,
                "qty": used_qty,
                "stock_qty": available_qty,  # Correct available stock quantity
                "custom_supplier_warehouse": warehouse
            })

            qty_used += used_qty
            remaining_qty -= used_qty

            if remaining_qty <= 0:
                break

        # Frappe throw for last stock (stock out)
        # if qty_used == 0 and requested_qty > 0:
        #     frappe.throw(f"Item {item_code} has insufficient stock after considering FIFO and stock-out.")

        # If no usable stock found, mark item as unavailable
        if qty_used == 0:
            unavailable_item = item.as_dict().copy()
            unavailable_item["qty"] = requested_qty
            unavailable_item["custom_bundle_sizeuom"] = None
            unavailable_item["custom_no_of_packs"] = 0
            unavailable_item["custom_available_qty"] = 0
            unavailable_item["custom_pack_size"] = 0
            unavailable_item["custom_stock"] = "Unavailable"
            unavailable_item["custom_batch_no"] = ''
            new_items.append(unavailable_item)
            continue

        # Use FIFO combo to create split items
        for row in fifo_combo:
            batches = get_batch_fifo_wise(item_code, row["custom_supplier_warehouse"], row["pack_size"])
            new_item = item.as_dict().copy()
            new_item["qty"] = row["qty"]
            new_item["custom_bundle_sizeuom"] = row["pack_size"]
            new_item["custom_no_of_packs"] = row["packs"]
            new_item["custom_available_qty"] = row["stock_qty"]
            new_item["custom_pack_size"] = row["pack_qty"]
            new_item["custom_stock"] = "Available"
            new_item["custom_batch_no"] = batches[0].batch_no if batches else ''
            new_item["custom_supplier_warehouse"] = row["custom_supplier_warehouse"]
            new_items.append(new_item)

    # Replace items in the document
    doc.set("items", [])
    for i in new_items:
        doc.append("items", i)

    total_items = len(doc.items)
    available_count = sum(1 for i in doc.items if i.custom_stock == "Available")
    doc.custom_states_ = "Approved" if available_count > 0 else "Pending For Approval"

    # Frappe throw for final stock status
   

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


@frappe.whitelist()
def get_batch_fifo_wise(item_code, warehouse, pack_size):
    if not pack_size:
        frappe.throw("Pack Size is required to fetch batches.")
    
    kwargs = {
        "item_code": item_code,
        "warehouse": warehouse,
        "pack_size": pack_size
    }
    batches = custom_get_available_batches(kwargs)
    return batches
