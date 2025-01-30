import frappe
from frappe import _
from datetime import datetime
from frappe.utils import today

@frappe.whitelist()
def create_sales_invoice_from_delivery_note(doc, method):
    # Create a new Sales Invoice
    sales_invoice = frappe.new_doc("Sales Invoice")
    sales_invoice.customer = doc.customer
    sales_invoice.company = doc.company
    sales_invoice.due_date = frappe.utils.add_days(frappe.utils.nowdate(), 30)  # Example: set due date 30 days from now
    sales_invoice.is_pos = 0  # Set this to 1 if it's a Point of Sale invoice
    sales_invoice.delivery_note = doc.name  # Link to the submitted Delivery Note

    # Transfer items from the Delivery Note to the Sales Invoice
    for item in doc.items:
        sales_invoice.append("items", {
            "item_code": item.item_code,
            "qty": item.qty,
            "has_item_scanned":item.has_item_scanned,
            "uom": item.uom,
            "warehouse": item.warehouse,
            "rate": item.rate,
            "amount": item.amount,
            "description": item.description,
            "cost_center": item.cost_center,
            "delivery_note":doc.name
        })

    # Add taxes from Delivery Note (if applicable)
    for tax in doc.taxes:
        sales_invoice.append("taxes", {
            "charge_type": tax.charge_type,
            "account_head": tax.account_head,
            "description": tax.description,
            "rate": tax.rate,
            "tax_amount": tax.tax_amount
        })

    # Save and submit the Sales Invoice
    sales_invoice.save(ignore_permissions=True)
    sales_invoice.submit()

    # Notify the user
    frappe.msgprint(_("Sales Invoice {0} created successfully from Delivery Note {1}").format(sales_invoice.name, doc.name))


@frappe.whitelist()
def create_shipment_from_delivery_note(doc, method):
    # Create a new Shipment
    shipment = frappe.new_doc("Shipment")
    shipment.delivery_note = doc.name  # Link the Shipment to the Delivery Note
    shipment.delivery_customer = doc.customer
    shipment.pickup_company = doc.company
    shipment.tracking_status = "In Progress"  # Initial status of the Shipment
    shipment.value_of_goods = doc.total
    shipment.pickup_date = today() 
    shipment.description_of_content = "_"
    shipment.delivery_address_name = doc.customer_address
    shipment.delivery_contact_person = doc.contact_person
    shipment.pickup_address_name = doc.company_address
    shipment.pickup_contact_person = doc.company_contact_person

    
    # Append the shipment delivery note
    shipment.append("shipment_delivery_note", {
        "delivery_note": doc.name, 
        "grand_total": doc.total, 
    })
    
    # Save and submit the Shipment
    shipment.save(ignore_permissions=True)
    frappe.msgprint(_("Shipment {0} created successfully from Delivery Note {1}").format(shipment.name, doc.name))

    return shipment  
