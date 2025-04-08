frappe.ui.form.on('Stock Entry Detail', {
    item_code: function(frm, cdt, cdn) {
        apply_pack_size_filter(frm, cdt, cdn);
    }
});

function apply_pack_size_filter(frm, cdt, cdn) {
    let row = locals[cdt][cdn];

    if (!row.item_code) {
        return;
    }

    frappe.call({
        method: "irfm_custom.irfm.override.stock_entry.get_valid_pack_sizes",
        args: {
            item_code: row.item_code  // Passing item_code from Stock Entry Detail
        },
        callback: function(response) {
            if (response.message) {
                let valid_pack_sizes = response.message;
                
                frm.fields_dict["items"].grid.get_field("to_pack_size").get_query = function() {
                    return {
                        filters: [["name", "in", valid_pack_sizes]]
                    };
                };
            }
        }
    });
}
