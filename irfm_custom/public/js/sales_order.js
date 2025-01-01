frappe.ui.form.on('Sales Order', {
    customer: function(frm) {
        if (frm.doc.customer) {
            frappe.db.get_value('Customer', frm.doc.customer, 'custom_delivery_days', (r) => {
                if (r.custom_delivery_days) {
                    let delivery_date = frappe.datetime.add_days(frappe.datetime.get_today(), r.custom_delivery_days);
                    console.log('Custom Delivery Days:', r.custom_delivery_days);
                    console.log('Calculated Delivery Date:', delivery_date);
                    frm.set_value('delivery_date', delivery_date);
                } else {
                    console.log('No custom_delivery_days found for customer.');
                    frm.set_value('delivery_date', null);
                }
            });
        } else {
            console.log('Customer is not selected.');
            frm.set_value('delivery_date', null);
        }
    }
});


