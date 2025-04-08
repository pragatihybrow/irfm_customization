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


import math
import frappe

@frappe.whitelist()
def update_custom_states(doc, method):
    supplier_company = frappe.get_value("Supplier", doc.supplier, "custom_company")
    if not supplier_company:
        frappe.throw(f"Supplier {doc.supplier} does not have a linked company.")

    company_warehouses = frappe.get_all("Warehouse", filters={"company": supplier_company}, pluck="name")
    if not company_warehouses:
        frappe.throw(f"No warehouses found for company {supplier_company}")

    all_items_available = True
    some_items_available = False
    available_count = 0
    total_items = len(doc.items)

    for item in doc.items:
        pack_size = item.custom_pack_size  # now correctly using the field from Purchase Order Item

        if not pack_size or pack_size <= 0:
            frappe.throw(f"Pack Size (custom_pack_size) is not set or invalid for item {item.item_code}")

        # Adjust qty to be multiple of pack size
        if item.qty % pack_size != 0:
            original_qty = item.qty
            item.qty = math.ceil(item.qty / pack_size) * pack_size
            frappe.msgprint(f"Quantity for item {item.item_code} adjusted from {original_qty} to {item.qty} to match pack size {pack_size}.")

        # Set number of packs
        item.custom_no_of_packs = item.qty / pack_size

        # Fetch stock with specific pack size
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
                "pack_size": item.custom_bundle_sizeuom,  # assuming this links to Pack Size doctype
            }
        )

        stock_qty = stock_data[0][0] or 0
        item.custom_available_qty = stock_qty

        if stock_qty >= item.qty:
            item.custom_stock = "Available"
            some_items_available = True
            available_count += 1
        else:
            item.custom_stock = "Unavailable"
            all_items_available = False

    if total_items > 0:
        doc.custom_states_ = "Approved" if available_count == total_items else "Pending For Approval"



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
