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
            "custom_pack_size" :item.custom_pack_size
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


    
# @frappe.whitelist()
# def update_custom_states(doc, method):
#     """Update custom_states_ and stock availability fields when saving the Purchase Order"""

#     # Fetch the supplier's company using the correct field name
#     supplier_company = frappe.get_value("Supplier", doc.supplier, "custom_company")

#     if not supplier_company:
#         frappe.throw(f"Supplier {doc.supplier} does not have a linked company. Please check the Supplier record.")

#     # Fetch all warehouses linked to this company
#     company_warehouses = frappe.get_all(
#         "Warehouse",
#         filters={"company": supplier_company},
#         pluck="name"
#     )

#     if not company_warehouses:
#         frappe.throw(f"No warehouses found for company {supplier_company}")

#     # Track stock availability
#     all_items_available = True  # Assume all items are available
#     some_items_available = False  # Track if at least one item is available
#     available_count = 0  # Count of available items
#     total_items = len(doc.items)

#     # Check stock for all items in the PO
#     for item in doc.items:
#         # Sum stock from all warehouses belonging to the supplier's company
#         stock_qty = frappe.db.sql(
#             """
#             SELECT SUM(actual_qty) FROM `tabBin`
#             WHERE warehouse IN %(warehouses)s AND item_code = %(item_code)s
#             """,
#             {"warehouses": company_warehouses, "item_code": item.item_code}
#         )[0][0] or 0

#         # Set custom_available_qty to show total stock across all warehouses
#         item.custom_available_qty = stock_qty

#         # Set custom_stock field
#         if stock_qty >= item.qty:
#             item.custom_stock = "Available"
#             some_items_available = True
#             available_count += 1  # Count available items
#         else:
#             item.custom_stock = "Unavailable"
#             all_items_available = False  # If any item is out of stock, mark it

#     # Set custom state before saving
#     if total_items > 0:
#         if available_count == total_items:
#             doc.custom_states_ = "Approved"
#         elif available_count > 0:
#             doc.custom_states_ = "Pending For Approval"
#         else:
#             doc.custom_states_ = "Pending For Approval"  # No items are available



@frappe.whitelist()
def update_custom_states(doc, method):
    supplier_company = frappe.get_value("Supplier", doc.supplier, "custom_company")
    if not supplier_company:
        frappe.throw(f"Supplier {doc.supplier} does not have a linked company.")

    # Get all warehouses of the supplier's company
    company_warehouses = frappe.get_all("Warehouse", filters={"company": supplier_company}, pluck="name")
    if not company_warehouses:
        frappe.throw(f"No warehouses found for company {supplier_company}")

    all_items_available = True
    some_items_available = False
    available_count = 0
    total_items = len(doc.items)

    for item in doc.items:
        # Fetch relevant stock from Stock Ledger Entry with matching pack size
        pack_size = item.custom_bundle_sizeuom  # assuming this holds the selected Pack Size (Link to Pack Size doctype)

        stock_data = frappe.db.sql(
            """
            SELECT SUM(actual_qty) FROM `tabStock Ledger Entry`
            WHERE item_code = %(item_code)s
            AND warehouse IN %(warehouses)s
            AND pack_size = %(pack_size)s
            AND is_cancelled = 0
            """,
            {
                "item_code": item.item_code,
                "warehouses": tuple(company_warehouses),
                "pack_size": pack_size,
            }
        )

        stock_qty = stock_data[0][0] or 0
        item.custom_available_qty = stock_qty

        # Check availability for that pack size
        if stock_qty >= item.qty:
            item.custom_stock = "Available"
            available_count += 1
            some_items_available = True
        else:
            item.custom_stock = "Unavailable"
            all_items_available = False

    # Final state logic
    if total_items > 0:
        if available_count == total_items:
            doc.custom_states_ = "Approved"
        else:
            doc.custom_states_ = "Pending For Approval"


# @frappe.whitelist()
# def update_custom_states(doc, method):
#     """Update custom_states_ and stock availability fields when saving the Purchase Order"""

#     # Track stock availability
#     all_items_available = True  # Assume all items are available
#     some_items_available = False  # Track if at least one item is available
#     available_count = 0  # Count of available items
#     total_items = len(doc.items)

#     # Check stock for all items in the PO
#     for item in doc.items:
#         stock_qty = frappe.get_value(
#             "Bin", 
#             {"warehouse": item.custom_supplier_warehouse, "item_code": item.item_code}, 
#             "actual_qty"
#         ) or 0

#         # Set custom_available_qty
#         item.custom_available_qty = stock_qty

#         # Set custom_stock field
#         if stock_qty >= item.qty:
#             item.custom_stock = "Available"
#             some_items_available = True
#             available_count += 1  # Count available items
#         else:
#             item.custom_stock = "Unavailable"
#             all_items_available = False  # If any item is out of stock, mark it

#     # Set custom state before saving
#     if total_items > 0:
#         if available_count == total_items:
#             doc.custom_states_ = "Approved"
#         elif available_count > 0:
#             doc.custom_states_ = "Pending For Approval"
#         else:
#             doc.custom_states_ = "Pending For Approval"  # No items are available




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

#     return next_schedule_day

# @frappe.whitelist()
# def get_available_qty_for_item_pack(item_code, warehouse, pack_size, from_date=None, to_date=None):
# 	from_date = getdate(from_date) if from_date else getdate("2000-01-01")
# 	to_date = getdate(to_date) if to_date else getdate()

# 	filters = {
# 		"item_code": item_code,
# 		"warehouse": warehouse,
# 		"pack_size": pack_size,
# 		"from_date": from_date,
# 		"to_date": to_date,
# 	}

# 	float_precision = cint(frappe.db.get_default("float_precision")) or 3
# 	iwb_map = get_item_warehouse_batch_map(filters, float_precision)

# 	total_qty = 0
# 	for batch_data in iwb_map.get(item_code, {}).get(warehouse, {}).values():
# 		qty_dict = batch_data.get(pack_size or "") or {}
# 		total_qty += flt(qty_dict.get("bal_qty", 0.0), float_precision)

# 	return total_qty
