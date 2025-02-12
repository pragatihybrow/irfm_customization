import frappe
import math
from frappe import _
from datetime import datetime, timedelta
@frappe.whitelist()
def validate_sales_order(doc, method):
    customer = doc.customer
    today = datetime.today().date()  # Convert to date
    overdue_threshold = today - timedelta(days=2)  # Ensure this is a date object

    # Query for all unpaid sales invoices for this customer that are past due
    sales_invoices = frappe.get_all('Sales Invoice', 
                                    filters={'customer': customer, 'docstatus': 1},  # docstatus = 1 means Open/Submitted
                                    fields=['name', 'due_date', 'outstanding_amount'])  # Fetch due_date and outstanding_amount
    
    for invoice in sales_invoices:
        due_date = invoice.get('due_date')  # Get due_date directly from Sales Invoice
        outstanding_amount = invoice.get('outstanding_amount')  # Get outstanding_amount
        
        # Check if the invoice is overdue (due date has passed) and still has an outstanding amount
        if due_date and outstanding_amount > 0 and due_date < overdue_threshold:
            frappe.throw(_("Cannot create a new sales order as the customer has overdue payments."))


@frappe.whitelist()
def update_custom_stock(doc, method):
    for item in doc.items:
        if item.actual_qty > 0:
            item.custom_stock = "Available"
        else:
            item.custom_stock = "Unavailable"

@frappe.whitelist()
def create_pick_list(doc, method):
    pick_list = frappe.new_doc("Pick List")
    pick_list.sales_order = doc.name
    pick_list.customer = doc.customer
    pick_list.company = doc.company
    pick_list.purpose = "Delivery"
    pick_list.parent_warehouse = doc.set_warehouse
    pick_list.custom_sales_order = doc.name

    for item in doc.items:
        if item.custom_total_pack:  # Ensure this condition is correctly indented
            remaining_qty = item.qty  # Start with the total quantity
            
            # Fetch the first barcode from the Item doctype
            item_doc = frappe.get_doc("Item", item.item_code)  # Get the Item document
            first_barcode = item_doc.barcodes[0].barcode if item_doc.barcodes else None  # Get first barcode
            
            for i in range(int(item.custom_total_pack)):  # Iterate for each pack
                # Assign qty to the current row
                current_pack_qty = min(item.custom_pack_of, remaining_qty)
                pick_list.append("locations", {
                    "item_code": item.item_code,
                    "qty": current_pack_qty,  # Set current pack qty
                    "stock_uom": item.stock_uom,
                    "warehouse": item.warehouse,
                    "stock_qty": current_pack_qty,  # Adjust stock_qty
                    "picked_qty": 0,  # Default to 0 for picked_qty
                    "sales_order": doc.name,
                    "custom_item_barcode": first_barcode,  # Use first barcode
                })
                remaining_qty -= current_pack_qty  # Reduce remaining quantity

    pick_list.save(ignore_permissions=True)


@frappe.whitelist()
def update_custom_states(doc, method):
    available_count = 0
    total_items = len(doc.items)

    # Iterate through the items in the child table
    for item in doc.items:
        if item.custom_stock == "Available":
            available_count += 1

    # Update custom_states based on the availability
    if available_count == total_items:
        # All items are available
        doc.custom_states = "Approved"
    elif available_count > 0:
        # Some items are available
        doc.custom_states = "Pending For Approval"
    else:
        # No items are available
        doc.custom_states = "Stock Unavailable"



@frappe.whitelist()
def on_submit_send_email(doc, method):
    if doc.doctype == "Sales Order":
        if doc.custom_states == "Approved":
        # Send email to customer
            customer_email = frappe.db.get_value('Customer', doc.customer, 'email_id')
            warehouse_email = frappe.db.get_value('Warehouse', doc.set_warehouse, 'email_id')
            supplier_email = frappe.db.get_value('Supplier', doc.custom_transporter, 'email_id')

            
            if customer_email:
                subject = f"Sales Order #{doc.name} - Your Order Details"
                message = f"Dear {doc.customer_name},\n\nYour Sales Order #{doc.name} has been submitted successfully.\n\nThank you for your business.\n\n"
                message += f"<a href=\"{frappe.utils.get_url_to_form('Sales Order', doc.name)}\">Click here to view the Sales Order</a>"
                
                # Sending the email to the customer
                frappe.sendmail(
                    recipients=customer_email,
                    subject=subject,
                    message=message,
                    now=True
                )

            if warehouse_email:
                subject = f"Sales Order #{doc.name} - Your Order Details set_warehouse"
                message = f"Dear {doc.set_warehouse},\n\nYour Sales Order #{doc.name} has been submitted successfully.\n\nThank you for your business.\n\n"
                message += f"<a href=\"{frappe.utils.get_url_to_form('Sales Order', doc.name)}\">Click here to view the Sales Order</a>"
                
                # Sending the email to the warehouse
                frappe.sendmail(
                    recipients=warehouse_email,
                    subject=subject,
                    message=message,
                    now=True
                )

            if supplier_email:
                subject = f"Sales Order #{doc.name} - Your Order Details trans"
                message = f"Dear {doc.custom_transporter},\n\nYour Sales Order #{doc.name} has been submitted successfully.\n\nThank you for your business.\n\n"
                message += f"<a href=\"{frappe.utils.get_url_to_form('Sales Order', doc.name)}\">Click here to view the Sales Order</a>"
                
                # Sending the email to the supplier
                frappe.sendmail(
                    recipients=supplier_email,
                    subject=subject,
                    message=message,
                    now=True
                )
 

       
@frappe.whitelist()
def on_submit_send_email_for_pending_approval(doc, method):
    if doc.doctype == "Sales Order":
        if doc.custom_states == "Pending For Approval":
            customer_email = frappe.db.get_value('Customer', doc.customer, 'email_id')
            warehouse_email = frappe.db.get_value('Warehouse', doc.set_warehouse, 'email_id')

            if customer_email:
                subject = f"Sales Order #{doc.name} - Unsufficient Stock"
                message = f"Dear {doc.customer_name},\n\nYour Sales Order #{doc.name} has been submitted successfully.\n\nThank you for your business.\n\n"
                message += f"<a href=\"{frappe.utils.get_url_to_form('Sales Order', doc.name)}\">Click here to view the Sales Order</a>"
                
                # Sending the email to the customer
                frappe.sendmail(
                    recipients=customer_email,
                    subject=subject,
                    message=message,
                    now=True
                )

            if warehouse_email:
                subject = f"Sales Order #{doc.name} - Unsufficient Stock"
                message = f"Dear {doc.set_warehouse},\n\nYour Sales Order #{doc.name} has been submitted successfully.\n\nThank you for your business.\n\n"
                message += f"<a href=\"{frappe.utils.get_url_to_form('Sales Order', doc.name)}\">Click here to view the Sales Order</a>"
                
                # Sending the email to the warehouse
                frappe.sendmail(
                    recipients=warehouse_email,
                    subject=subject,
                    message=message,
                    now=True
                )

       