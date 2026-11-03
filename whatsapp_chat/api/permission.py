import frappe
from frappe import _

# Align with CRM WhatsApp access (crm.api.whatsapp.ALLOWED_WHATSAPP_ROLES)
ALLOWED_WHATSAPP_ROLES = ["System Manager", "Sales Manager", "Sales User"]


def check_app_permission():
	"""Used by add_to_apps_screen has_permission hook."""
	return _has_inbox_access()


def validate_inbox_access():
	"""Raise if the current user may not access the WhatsApp Inbox."""
	if not _has_inbox_access():
		frappe.throw(
			_("You do not have permission to access WhatsApp Inbox"),
			frappe.PermissionError,
		)


def _has_inbox_access():
	if frappe.session.user in ("Guest", ""):
		return False

	if frappe.session.user == "Administrator":
		return True

	user_type = frappe.db.get_value("User", frappe.session.user, "user_type")
	if user_type != "System User":
		return False

	roles = frappe.get_roles()
	return any(role in ALLOWED_WHATSAPP_ROLES for role in roles)
