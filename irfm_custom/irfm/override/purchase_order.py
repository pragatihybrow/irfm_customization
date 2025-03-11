import frappe
from frappe.utils import flt

# @frappe.whitelist()
# def create_sales_order(doc, method):
#     """Create a Sales Order when a Purchase Order is submitted, only if stock is available"""

#     # Fetch the represents_company field from Supplier
#     represents_company = frappe.get_value("Supplier", doc.supplier, "represents_company")

#     if not represents_company:
#         frappe.throw(f"Supplier {doc.supplier} does not have a represents_company set.")

#     # Get the default Sales Taxes and Charges Template for the represents_company
#     taxes_template = frappe.get_value("Sales Taxes and Charges Template", 
#                                       {"company": represents_company}, "name")

#     # Create new Sales Order
#     sales_order = frappe.get_doc({
#         "doctype": "Sales Order",
#         "customer": doc.custom_customers,  
#         "company": represents_company,
#         "transaction_date": doc.transaction_date,
#         "delivery_date": doc.transaction_date,
#         "currency": doc.currency,
#         "taxes_and_charges": taxes_template,
#         "items": [],
#         "taxes": []
#     })

#     # Map Purchase Order items to Sales Order items
#     for item in doc.items:
#         stock_qty = frappe.get_value("Bin", 
#                                      {"warehouse": item.custom_supplier_warehouse, "item_code": item.item_code}, 
#                                      "actual_qty") or 0
        
#         if stock_qty < item.qty:
#             frappe.throw(f"Insufficient stock for item {item.item_code} in warehouse {item.custom_supplier_warehouse}. Required: {item.qty}, Available: {stock_qty}")

#         sales_order.append("items", {
#             "item_code": item.item_code,
#             "item_name": item.item_name,
#             "description": item.description,
#             "qty": item.qty,
#             "uom": item.uom,
#             "rate": item.rate,
#             "amount": item.amount,
#             "warehouse": item.custom_supplier_warehouse,
#             "purchase_order": doc.name
#         })

#     # If a tax template is found, fetch and apply the taxes
#     if taxes_template:
#         tax_details = frappe.get_all("Sales Taxes and Charges", 
#                                      filters={"parent": taxes_template}, 
#                                      fields=["charge_type", "account_head", "rate", "description"])

#         for tax in tax_details:
#             sales_order.append("taxes", {
#                 "charge_type": tax.charge_type,
#                 "account_head": tax.account_head,
#                 "rate": tax.rate,
#                 "description": tax.description
#             })

#     # Save and submit the Sales Order
#     sales_order.insert()
#     sales_order.submit()

#     frappe.msgprint(f"Sales Order {sales_order.name} created successfully for company {represents_company}!", alert=True)



# @frappe.whitelist()
# def update_custom_states(doc, method):
#     available_count = 0
#     total_items = len(doc.items)

#     # Iterate through the items in the child table
#     for item in doc.items:
#         if item.custom_stock == "Available":
#             available_count += 1

#     # Update custom_states based on the availability
#     if available_count == total_items:
#         # All items are available
#         doc.custom_states_ = "Approved"
#     elif available_count > 0:
#         # Some items are available
#         doc.custom_states_ = "Pending For Approval"
#     else:
#         # No items are available
#         doc.custom_states_ = "Stock Unavailable"


@frappe.whitelist()
def create_sales_order(doc, method):
    """Create a Sales Order when a Purchase Order is submitted, only if stock is fully available"""

    # Ensure SO is created only if PO is approved
    if doc.custom_states_ != "Approved":
        frappe.throw("Purchase Order is not fully approved. Cannot create Sales Order.")

    # Fetch the represents_company field from Supplier
    represents_company = frappe.get_value("Supplier", doc.supplier, "represents_company")

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
        "transaction_date": doc.transaction_date,
        "delivery_date": doc.transaction_date,
        "currency": doc.currency,
        "taxes_and_charges": taxes_template,
        "items": [],
        "taxes": []
    })

    # Map Purchase Order items to Sales Order items
    for item in doc.items:
        sales_order.append("items", {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "description": item.description,
            "qty": item.qty,
            "uom": item.uom,
            "rate": item.rate,
            "amount": item.amount,
            "warehouse": item.custom_supplier_warehouse,
            "purchase_order": doc.name
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
    sales_order.submit()

    frappe.msgprint(f"Sales Order {sales_order.name} created successfully for company {represents_company}!", alert=True)





def update_custom_states(doc, method):
    """Update custom_states_ based on stock availability when saving the Purchase Order"""

    # Track stock availability
    all_items_available = True  # Assume all items are available
    some_items_available = False  # Track if at least one item is available

    # Check stock for all items in the PO
    for item in doc.items:
        stock_qty = frappe.get_value("Bin", 
                                     {"warehouse": item.custom_supplier_warehouse, "item_code": item.item_code}, 
                                     "actual_qty") or 0

        if stock_qty >= item.qty:
            some_items_available = True
        else:
            all_items_available = False  # If any item is out of stock, mark it

    # Set custom state before saving
    if all_items_available:
        doc.custom_states_ = "Approved"
    elif some_items_available:
        doc.custom_states_ = "Pending For Approval"
    else:
        doc.custom_states_ = "Pending For Approval"  # Default to Pending if none are available
