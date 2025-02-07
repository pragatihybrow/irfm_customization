app_name = "irfm_custom"
app_title = "IRFM"
app_publisher = "Pragati Dike"
app_description = "irfm_customization"
app_email = "pragati@mail.hybrowlabs.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "irfm_custom",
# 		"logo": "/assets/irfm_custom/logo.png",
# 		"title": "IRFM",
# 		"route": "/irfm_custom",
# 		"has_permission": "irfm_custom.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/irfm_custom/css/irfm_custom.css"
# app_include_js = "/assets/irfm_custom/js/irfm_custom.js"

# include js, css files in header of web template
# web_include_css = "/assets/irfm_custom/css/irfm_custom.css"
# web_include_js = "/assets/irfm_custom/js/irfm_custom.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "irfm_custom/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "irfm_custom/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "irfm_custom.utils.jinja_methods",
# 	"filters": "irfm_custom.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "irfm_custom.install.before_install"
# after_install = "irfm_custom.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "irfm_custom.uninstall.before_uninstall"
# after_uninstall = "irfm_custom.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "irfm_custom.utils.before_app_install"
# after_app_install = "irfm_custom.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "irfm_custom.utils.before_app_uninstall"
# after_app_uninstall = "irfm_custom.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "irfm_custom.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"irfm_custom.tasks.all"
# 	],
# 	"daily": [
# 		"irfm_custom.tasks.daily"
# 	],
# 	"hourly": [
# 		"irfm_custom.tasks.hourly"
# 	],
# 	"weekly": [
# 		"irfm_custom.tasks.weekly"
# 	],
# 	"monthly": [
# 		"irfm_custom.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "irfm_custom.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "irfm_custom.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "irfm_custom.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["irfm_custom.utils.before_request"]
# after_request = ["irfm_custom.utils.after_request"]

# Job Events
# ----------
# before_job = ["irfm_custom.utils.before_job"]
# after_job = ["irfm_custom.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"irfm_custom.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }


doc_events = {
    "Sales Order": {
        "validate": [
            "irfm_custom.irfm.override.sales_order.update_custom_stock",
            "irfm_custom.irfm.override.sales_order.update_custom_states",
            "irfm_custom.irfm.override.sales_order.validate_sales_order"
        ],
        "on_submit": [
            "irfm_custom.irfm.override.sales_order.create_pick_list",
            "irfm_custom.irfm.override.sales_order.on_submit_send_email",
            "irfm_custom.irfm.override.sales_order.on_submit_send_email_for_pending_approval"
        ],
    },
    "Pick List": {
        "on_submit":[ "irfm_custom.irfm.override.pick_list.create_delivery_note_from_picklist",
        "irfm_custom.irfm.override.pick_list.get_status"]
    },
    "Delivery Note": {
        "on_submit":[ "irfm_custom.irfm.override.delivery_note.create_sales_invoice_from_delivery_note",
                      "irfm_custom.irfm.override.delivery_note.create_shipment_from_delivery_note",        ],
        "validate":"irfm_custom.irfm.override.delivery_note.on_submit_of_delivery_note",
    },

     "Purchase Receipt": {
        "on_submit": "irfm_custom.irfm.override.purchase_receipt.create_purchase_invoice_from_grn"
    },
    "Customer":
    { 
        "before_save":["irfm_custom.irfm.override.customer.check_box"
                    #   "irfm_custom.irfm.override.customer.calculate_time_difference" ]
        ],
    
     "on_update":["irfm_custom.irfm.override.customer.calculate_time_difference_in_custom_timezone"
     ]
    }
}


override_doctype_class = {
	"Pick List": "irfm_custom.irfm.override.pick_list.location_ct",
    "Delivery Note": "irfm_custom.irfm.override.delivery_note.newdeliverynote",

}



override_doctype_dashboards = {
    "Delivery Note": "irfm_custom.irfm.override.delivery_note_dashboard.get_dashboard_data",
}

