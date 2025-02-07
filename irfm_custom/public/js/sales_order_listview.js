frappe.listview_settings['Sales Order'] = {
    formatters: {
        name(val, d, f) {
            return `
                <a href="/printview?doctype=Sales Order&name=${val}&format=Print Format SO&no_letterhead=0" target="_blank"
                   class="btn btn-primary btn-xs" style="margin-right: 5px;">
                    View
                </a> 
                ${val}
            `;
        }
    }
};
