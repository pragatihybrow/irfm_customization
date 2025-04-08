import frappe

@frappe.whitelist()
def get_valid_pack_sizes(item_code):
    """Fetch valid pack sizes (bundle_size) from custom_item_pack_size child table for the given item_code."""
    if not item_code:
        return []

    bundle_sizes = frappe.get_all(
        "Item Pack Size CT",
        filters={"parent": item_code},  # Fetching bundle sizes linked to Item
        fields=["bundle_size"]
    )

    return [size["bundle_size"] for size in bundle_sizes]
