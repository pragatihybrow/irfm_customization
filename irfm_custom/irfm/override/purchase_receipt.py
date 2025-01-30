import frappe
from frappe import _

@frappe.whitelist()
def create_purchase_invoice_from_grn(doc, method):
    # Create a new Purchase Invoice
    grn = frappe.new_doc("Purchase Invoice")
    
    # Link the Purchase Invoice to the Supplier from the Purchase Receipt
    grn.supplier = doc.supplier  # Use doc.supplier, not 'supplier'
    grn.company = doc.company
    
    # Append the items from the Purchase Receipt to the Purchase Invoice
    for item in doc.items:
        grn.append("items", {
            "item_code": item.item_code,
            "qty": item.qty,
            "custom_box_barcode": item.custom_box_barcode,
            "uom": item.uom,
            "warehouse": item.warehouse,
            "rate": item.rate,
            "amount": item.amount,
            "description": item.description,
            "cost_center": item.cost_center,
            "purchase_receipt":doc.name
        })

    # Add taxes from the Purchase Receipt (if applicable)
    for tax in doc.taxes:
        grn.append("taxes", {
            "charge_type": tax.charge_type,
            "account_head": tax.account_head,
            "description": tax.description,
            "rate": tax.rate,
            "tax_amount": tax.tax_amount
        })

    # Save and submit the Purchase Invoice
    grn.save(ignore_permissions=True)
    grn.submit()

    # Notify the user
    frappe.msgprint(_("Purchase Invoice {0} created successfully from {1} Purchase Receipt").format(grn.name, doc.name))
