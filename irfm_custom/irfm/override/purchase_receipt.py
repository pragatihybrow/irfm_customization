import frappe

@frappe.whitelist()
def create_purchase_invoice_from_grn(doc, method):
    # Create a new Shipment
    shipment = frappe.new_doc("Purchase Invoice")
    shipment.supplier = supplier  # Link the Shipment to the Delivery Note
    shipment.company = doc.company
    # Append the shipment delivery note
    for item in doc.items:
        sales_invoice.append("items", {
            "item_code": item.item_code,
            "qty": item.qty,
            "custom_box_barcode":item.custom_box_barcode,
            "uom": item.uom,
            "warehouse": item.warehouse,
            "rate": item.rate,
            "amount": item.amount,
            "description": item.description,
            "cost_center": item.cost_center,
            "delivery_note":doc.name,
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

