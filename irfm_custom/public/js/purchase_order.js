frappe.ui.form.on('Purchase Order Item', {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.item_code && row.custom_supplier_warehouse) {
            frappe.call({
                method: "irfm_custom.irfm.override.purchase_order.get_available_qty",
                args: {
                    item_code: row.item_code,
                    warehouse: row.custom_supplier_warehouse
                },
                callback: function(response) {
                    if (response.message) {
                        frappe.model.set_value(cdt, cdn, 'custom__available_quantity', response.message || 0);
                    }
                }
            });
        }
    }
});


