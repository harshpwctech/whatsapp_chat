import frappe


def execute():
	if frappe.db.exists("Page", "whatsapp-inbox"):
		frappe.delete_doc("Page", "whatsapp-inbox", force=True, ignore_permissions=True)
