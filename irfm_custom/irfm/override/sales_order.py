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


import random
import os
import frappe
import barcode
from barcode.writer import ImageWriter

@frappe.whitelist()
def create_pick_list(doc, method):
    """Create a Draft Pick List when a Sales Order is submitted."""

    pick_list = frappe.new_doc("Pick List")
    pick_list.sales_order = doc.name
    pick_list.customer = doc.customer
    pick_list.company = doc.company
    pick_list.purpose = "Delivery"
    pick_list.parent_warehouse = doc.set_warehouse
    pick_list.custom_sales_order = doc.name
    pick_list.save(ignore_permissions=True)  # Save early to get name for file linking

    for item in doc.items:
        item_doc = frappe.get_doc("Item", item.item_code)
        first_barcode = item_doc.barcodes[0].barcode if item_doc.barcodes else None

        no_of_packs = int(item.custom_no_of_packs or 0)

        for _ in range(no_of_packs):
            generated_barcode = generate_ean13_barcode()
            barcode_image_url = generate_and_save_barcode_image(generated_barcode, pick_list.name)

            pick_list.append("locations", {
                "item_code": item.item_code,
                "qty": item.custom_pack_size,
                "uom": item.uom,
                "stock_uom": item.stock_uom,
                "warehouse": item.warehouse,
                "stock_qty": item.custom_pack_size,
                "picked_qty": 0,
                "sales_order": doc.name,
                "custom_item_barcode": first_barcode,
                "custom_pack_size": item.custom_pack_size,
                "custom_no_of_packs": no_of_packs,
                "custom_uoms": item.custom_bundle_sizeuom,
                "use_serial_batch_fields": 1,
                "custom_purchase_order": item.purchase_order,
                "custom_purchase_order_item": item.purchase_order_item,
                "sales_order_item": item.name,
                "batch_no": item.custom_batch_no,
                "custom_barcode": generated_barcode,
                "custom_barcode_image":generated_barcode,
                "custom_attached_barcode": barcode_image_url
            })

    pick_list.save(ignore_permissions=True)
    frappe.msgprint(f"Draft Pick List {pick_list.name} created for Sales Order {doc.name}!", alert=True)

def generate_ean13_barcode():
    """Generate a valid EAN-13 barcode with India prefix (890)"""
    prefix = "890"
    random_part = ''.join([str(random.randint(0, 9)) for _ in range(9)])
    partial_barcode = prefix + random_part
    check_digit = calculate_ean13_check_digit(partial_barcode)
    return partial_barcode + str(check_digit)

def calculate_ean13_check_digit(barcode):
    """Calculate the EAN-13 check digit from the first 12 digits"""
    digits = list(map(int, barcode))
    total = sum(d if i % 2 == 0 else d * 3 for i, d in enumerate(digits))
    return (10 - (total % 10)) % 10

def generate_and_save_barcode_image(barcode_value, pick_list_name):
    """Generate a scannable EAN-13 barcode image and save it as a public file"""

    file_path_no_ext = frappe.utils.get_site_path('public', 'files', barcode_value)

    ean = barcode.get('ean13', barcode_value, writer=ImageWriter())
    full_path = ean.save(file_path_no_ext)

    file_url = f'/files/{barcode_value}.png'

    # Create File record in Frappe
    file = frappe.get_doc({
        'doctype': 'File',
        'file_name': f'{barcode_value}.png',
        'file_url': file_url,
        'attached_to_doctype': 'Pick List',
        'attached_to_name': pick_list_name,
        'is_private': 0
    })
    file.insert(ignore_permissions=True)

    return file_url



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

def validate_integer(value, fieldname):
    if not isinstance(value, int):
        frappe.throw(f"{fieldname} must be an integer.")

def validate_positive(value, fieldname):
    if value is None or value < 1:
        frappe.throw(f"{fieldname} must be greater than or equal to 1.")

# def validate_sales_order_item(doc, method):
#     for item in doc.items:
#         if not isinstance(item.custom_pack_of, int):
#             frappe.throw(f"No Of Packs must be an integer.")

#         # Validate custom_total_pack is an integer and greater than or equal to 1
#         if not (item.custom_total_pack.is_integer() and item.custom_total_pack >= 1):
#             frappe.throw("Number Of Packs must be an integer greater than or equal to 1.")

#         # Calculate qty
#         item.qty = item.custom_total_pack * item.custom_pack_of