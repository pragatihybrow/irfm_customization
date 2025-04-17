// frappe.ui.form.on('Purchase Order Item', {
//     item_code: function(frm, cdt, cdn) {
//         let row = locals[cdt][cdn];

//         if (row.item_code && row.custom_supplier_warehouse && row.custom_bundle_sizeuom) {
//             frappe.call({
//                 method: "irfm_custom.irfm.override.purchase_order.get_batch_fifo_wise",
//                 args: {
//                     item_code: row.item_code,
//                     warehouse: row.custom_supplier_warehouse,
//                     pack_size: row.custom_bundle_sizeuom
//                 },
//                 callback: function(response) {
//                     if (response.message && response.message.length > 0) {
//                         frappe.model.set_value(cdt, cdn, 'custom_batch_no', response.message[0].batch_no);
//                     } else {
//                         frappe.model.set_value(cdt, cdn, 'custom_batch_no', '');
//                         frappe.msgprint(__('No batches available for the selected item, warehouse, and pack size.'));
//                     }
//                 }
//             });
//         }
//     }
// });


frappe.ui.form.on('Purchase Order Item', {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.item_code && row.custom_supplier_warehouse && row.custom_bundle_sizeuom) {
            fetch_batch_fifo(row, cdt, cdn);
        }
    },
    custom_bundle_sizeuom: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.item_code && row.custom_supplier_warehouse && row.custom_bundle_sizeuom) {
            fetch_batch_fifo(row, cdt, cdn);
        }
    }
});

function fetch_batch_fifo(row, cdt, cdn) {
    frappe.call({
        method: "irfm_custom.irfm.override.purchase_order.get_batch_fifo_wise",
        args: {
            item_code: row.item_code,
            warehouse: row.custom_supplier_warehouse,
            pack_size: row.custom_bundle_sizeuom
        },
        callback: function(response) {
            if (response.message && response.message.length > 0) {
                frappe.model.set_value(cdt, cdn, 'custom_batch_no', response.message[0].batch_no);
            } else {
                frappe.model.set_value(cdt, cdn, 'custom_batch_no', '');
                frappe.msgprint(__('No batches available for the selected item, warehouse, and pack size.'));
            }
        }
    });
}
