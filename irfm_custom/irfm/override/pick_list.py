import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.stock.doctype.pick_list.pick_list import PickList

@frappe.whitelist()
def create_delivery_note_from_picklist(doc, method):
    # Create a new Delivery Note
    delivery_note = frappe.new_doc("Delivery Note")
    delivery_note.pick_list = doc.name  # Link the delivery note to the Pick List
    delivery_note.customer = doc.customer
    delivery_note.set_warehouse = doc.parent_warehouse
    delivery_note.company = doc.company
    delivery_note.delivery_date = frappe.utils.today()  # Set delivery date as today's date
    sales_doc = frappe.get_doc("Sales Order", doc.custom_sales_order)
    delivery_note.taxes_and_charges = sales_doc.taxes_and_charges

    # Store tax details from Sales Order
    for item in doc.locations:
        sales_order_doc = frappe.get_doc("Sales Order", item.sales_order)
        
        delivery_note.append("items", {
            "item_code": item.item_code,
            "qty": item.picked_qty,  
            "uom": item.stock_uom,   
            "warehouse": item.warehouse,
        })
 
        # Fetch taxes_and_charges from Sales Order
        for tax_entry in sales_order_doc.get('taxes'):
            delivery_note.append("taxes", {
                "charge_type": tax_entry.charge_type,
                "account_head": tax_entry.account_head,
                "description": tax_entry.description,
                "rate": tax_entry.rate,
                "tax_amount": tax_entry.tax_amount
            })

    delivery_note.save(ignore_permissions=True)
    frappe.msgprint(_("Delivery Note {0} created successfully").format(delivery_note.name))




class  location_ct(Document):
    @frappe.whitelist()
    def aggregate_item_qty(self):
        locations = self.get("locations")
        self.item_count_map = {}
        
        # Iterate through locations to process items
        for item in locations:
            if not item.item_code:
                frappe.throw(f"Row #{item.idx}: Item Code is Mandatory")

            # Skip non-stock items unless part of a valid product bundle
            if not cint(
                frappe.get_cached_value("Item", item.item_code, "is_stock_item")
            ) and not frappe.db.exists("Product Bundle", {"new_item_code": item.item_code, "disabled": 0}):
                continue

            # Maintain count of each item (useful to limit get query)
            self.item_count_map.setdefault(item.item_code, 0)
            self.item_count_map[item.item_code] += item.qty

        return locations
