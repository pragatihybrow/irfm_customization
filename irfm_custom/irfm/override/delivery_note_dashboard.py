from frappe import _

def get_dashboard_data(data):
    # Set custom delivery note mapping
    data["non_standard_fieldnames"]["Sales Order"] = "custom_delivery_note"
    
    # Loop through transactions to check and append "Sales Order"
    for transaction in data.get("transactions", []):
        if transaction.get("label") == _("Reference"):
            # Ensure "Sales Order" is not already in the items list before appending
            if "Sales Order" not in transaction["items"]:
                transaction["items"].append("Sales Order")
            break
    else:
        # If no matching transaction found, add a new one with "Sales Order"
        data["transactions"].append({
            "label": _("Reference"),
            "items": ["Sales Order"],
        })
    
    return data
