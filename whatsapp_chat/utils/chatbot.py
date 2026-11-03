import frappe


def is_chatbot_installed():
	return "frappe_whatsapp_chatbot" in frappe.get_installed_apps()


def require_chatbot():
	if not is_chatbot_installed():
		frappe.throw(
			_("WhatsApp Chatbot app is required for this feature"),
			frappe.ValidationError,
		)
