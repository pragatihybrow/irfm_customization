import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.stock.doctype.pick_list.pick_list import PickList


import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.stock.doctype.pick_list.pick_list import PickList
from frappe.utils import cint
import json
from collections import OrderedDict, defaultdict
from itertools import groupby

import frappe
from frappe import _, bold
from frappe.model.document import Document
from frappe.model.mapper import map_child_doc
from frappe.query_builder import Case
from frappe.query_builder.custom import GROUP_CONCAT
from frappe.query_builder.functions import Coalesce, Locate, Replace, Sum
from frappe.utils import ceil, cint, floor, flt, get_link_to_form
from frappe.utils.nestedset import get_descendants_of

from erpnext.selling.doctype.sales_order.sales_order import (
	make_delivery_note as create_delivery_note_from_sales_order,
)
from erpnext.stock.doctype.serial_and_batch_bundle.serial_and_batch_bundle import (
	get_auto_batch_nos,
	get_picked_serial_nos,
)
from erpnext.stock.get_item_details import get_conversion_factor
from erpnext.stock.serial_batch_bundle import (
	SerialBatchCreation,
	get_batches_from_bundle,
	get_serial_nos_from_bundle,
)


import frappe
from frappe.model.document import Document
from frappe import _

@frappe.whitelist()
def create_delivery_note_from_picklist(doc, method):
    """Create a Delivery Note when a Pick List is submitted."""

    # Create a new Delivery Note
    delivery_note = frappe.new_doc("Delivery Note")
    delivery_note.pick_list = doc.name  # Link Pick List
    delivery_note.customer = doc.customer
    delivery_note.set_warehouse = doc.parent_warehouse
    delivery_note.company = doc.company
    delivery_note.delivery_date = frappe.utils.today()

    # Get the first Sales Order to copy taxes
    if doc.locations:
        first_item = doc.locations[0]
        sales_order_doc = frappe.get_doc("Sales Order", first_item.sales_order)
        delivery_note.taxes_and_charges = sales_order_doc.taxes_and_charges

    # Store items and link them correctly
    for item in doc.locations:
        sales_order_doc = frappe.get_doc("Sales Order", item.sales_order)

        # Find Sales Order Item ID (so_detail)
        sales_order_item = None
        for soi in sales_order_doc.items:
            if soi.item_code == item.item_code:
                sales_order_item = soi.name  # Sales Order Item ID
                break  # Stop once found

        if not sales_order_item:
            frappe.throw(f"Sales Order Item not found for Item {item.item_code} in Sales Order {item.sales_order}")

        delivery_note.append("items", {
            "item_code": item.item_code,
            "qty": item.picked_qty,
            "uom": item.stock_uom,
            "warehouse": item.warehouse,
            "custom_box_barcode": item.custom_barcode,
            "custom_barcode_image": item.custom_barcode_image,
            "against_sales_order": item.sales_order,  # Ensure this is set correctly
            "so_detail": sales_order_item  # Correctly linked to Sales Order Item ID
        })

    # Copy Taxes from Sales Order
    for tax_entry in sales_order_doc.get("taxes", []):
        delivery_note.append("taxes", {
            "charge_type": tax_entry.charge_type,
            "account_head": tax_entry.account_head,
            "description": tax_entry.description,
            "rate": tax_entry.rate,
            "tax_amount": tax_entry.tax_amount
        })

    # Save and Submit Delivery Note
    delivery_note.insert(ignore_permissions=True)
    delivery_note.save(ignore_permissions=True)

    frappe.msgprint(_("Delivery Note {0} created successfully").format(delivery_note.name))


# @frappe.whitelist()
# def get_status(doc, docstatus, update_modified=True):
#     if doc.docstatus == 0:
#         doc.status = "Open"
#     elif doc.docstatus == 1:
#         doc.status = "Completed"
#     elif doc.docstatus == 2:
#         doc.status = "Cancelled"
    
#     doc.save(ignore_permissions=True)
#     frappe.db.commit()
#     return doc.status

@frappe.whitelist()
def get_status(doc, docstatus, update_modified=True):
    """Update status field based on docstatus after submission."""

    # Determine status based on docstatus
    if doc.docstatus == 0:
        new_status = "Open"
    elif doc.docstatus == 1:
        new_status = "Completed"
    elif doc.docstatus == 2:
        new_status = "Cancelled"

    frappe.db.set_value(doc.doctype, doc.name, "status", new_status, update_modified=update_modified)
    
    return new_status




class location_ct(Document):
    @frappe.whitelist()
    def set_item_locations(self, save=False):
        self.validate_for_qty()
        items = self.aggregate_item_qty()
        picked_items_details = self.get_picked_items_details(items)
        self.item_location_map = frappe._dict()

        from_warehouses = [self.parent_warehouse] if self.parent_warehouse else []
        if self.parent_warehouse:
            from_warehouses.extend(get_descendants_of("Warehouse", self.parent_warehouse))

        # Create replica before resetting, to handle empty table on update after submit.
        locations_replica = self.get("locations")

        # Reset locations with zero picked_qty
        reset_rows = []
        for row in self.get("locations"):
            if not row.picked_qty:
                reset_rows.append(row)

        for row in reset_rows:
            self.remove(row)

        updated_locations = frappe._dict()
        for item_doc in items:
            item_code = item_doc.item_code

            self.item_location_map.setdefault(
                item_code,
                get_available_item_locations(
                    item_code,
                    from_warehouses,
                    self.item_count_map.get(item_code),
                    self.company,
                    picked_item_details=picked_items_details.get(item_code),
                    consider_rejected_warehouses=self.consider_rejected_warehouses,
                ),
            )

            locations = get_items_with_location_and_quantity(item_doc, self.item_location_map, self.docstatus)

            item_doc.idx = None
            item_doc.name = None

            for row in locations:
                location = item_doc.as_dict()
                location.update(row)
                key = (
                    location.item_code,
                    location.warehouse,
                    location.uom,
                    location.batch_no,
                    location.serial_no,
                    location.sales_order_item or location.material_request_item,
                )

                if key not in updated_locations:
                    updated_locations.setdefault(key, location)
                else:
                    updated_locations[key].qty += location.qty
                    updated_locations[key].stock_qty += location.stock_qty

        for location in updated_locations.values():
            if location.picked_qty > location.stock_qty:
                location.picked_qty = location.stock_qty

            self.append("locations", location)

        # If table is empty on update after submit, set stock_qty and picked_qty to 0 so that the indicator is red
        if not self.get("locations") and self.docstatus == 1:
            for location in locations_replica:
                location.stock_qty = 0
                location.picked_qty = 0
                self.append("locations", location)
            frappe.msgprint(
                _(
                    "Please restock items and update the Pick List to continue. To discontinue, cancel the Pick List."
                ),
                title=_("Out of Stock"),
                indicator="red",
            )

        if save:
            self.save()

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
    

    def validate_for_qty(self):
        if self.purpose == "Material Transfer for Manufacture" and (self.for_qty is None or self.for_qty == 0):
            frappe.throw(_("Qty of Finished Goods Item should be greater than 0."))
    
    def get_picked_items_details(self, items):
            picked_items = frappe._dict()

            if not items:
                return picked_items

            items_data = self._get_pick_list_items(items)

            for item_data in items_data:
                key = (item_data.warehouse, item_data.batch_no) if item_data.batch_no else item_data.warehouse
                serial_no = [x for x in item_data.serial_no.split("\n") if x] if item_data.serial_no else None

                if item_data.serial_and_batch_bundle:
                    if not serial_no:
                        serial_no = get_serial_nos_from_bundle(item_data.serial_and_batch_bundle)

                    if not item_data.batch_no and not serial_no:
                        bundle_batches = get_batches_from_bundle(item_data.serial_and_batch_bundle)
                        for batch_no, batch_qty in bundle_batches.items():
                            batch_qty = abs(batch_qty)

                            key = (item_data.warehouse, batch_no)
                            if item_data.item_code not in picked_items:
                                picked_items[item_data.item_code] = {key: {"picked_qty": batch_qty}}
                            else:
                                picked_items[item_data.item_code][key]["picked_qty"] += batch_qty

                        continue

                if item_data.item_code not in picked_items:
                    picked_items[item_data.item_code] = {}

                if key not in picked_items[item_data.item_code]:
                    picked_items[item_data.item_code][key] = frappe._dict(
                        {
                            "picked_qty": 0,
                            "serial_no": [],
                            "batch_no": item_data.batch_no or "",
                            "warehouse": item_data.warehouse,
                        }
                    )

                picked_items[item_data.item_code][key]["picked_qty"] += item_data.picked_qty
                if serial_no:
                    picked_items[item_data.item_code][key]["serial_no"].extend(serial_no)

            return picked_items

    def _get_pick_list_items(self, items):
        pi = frappe.qb.DocType("Pick List")
        pi_item = frappe.qb.DocType("Pick List Item")
        query = (
			frappe.qb.from_(pi)
			.inner_join(pi_item)
			.on(pi.name == pi_item.parent)
			.select(
				pi_item.item_code,
				pi_item.warehouse,
				pi_item.batch_no,
				pi_item.serial_and_batch_bundle,
				pi_item.serial_no,
				(Case().when(pi_item.picked_qty > 0, pi_item.picked_qty).else_(pi_item.stock_qty)).as_(
					"picked_qty"
				),
			)
			.where(
				(pi_item.item_code.isin([x.item_code for x in items]))
				& ((pi_item.picked_qty > 0) | (pi_item.stock_qty > 0))
				& (pi.status != "Completed")
				& (pi.status != "Cancelled")
				& (pi_item.docstatus != 2)
			)
		)

        if self.name:
            query = query.where(pi_item.parent != self.name)
        query = query.for_update()

        return query.run(as_dict=True)
