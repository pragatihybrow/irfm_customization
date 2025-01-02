import frappe

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
        pick_list.append("locations", {
            "item_code": item.item_code,
            "qty": item.qty,
            "stock_uom": item.stock_uom,
            "warehouse": item.warehouse,
            "stock_qty":item.stock_qty,
            "picked_qty":item.picked_qty,
            "sales_order":doc.name

        })
    pick_list.save(ignore_permissions=True)






@frappe.whitelist()
def update_custom_states(doc, method):
    available_count = 0

    # Iterate through the items in the child table
    for item in doc.items:
        if item.custom_stock == "Available":
            available_count += 1

    # Check if all rows have custom_stock marked as "Available"
    total_items = len(doc.items)
    if available_count == total_items:
        doc.custom_states = "Approved"
    elif available_count < total_items:
        doc.custom_states = "Pending For Approval"
    elif available_count == 0:
        doc.custom_states = "Pending For Approval"
        raise ValueError("Document cannot be submitted as no items are available. Please review before proceeding.")

      

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

       