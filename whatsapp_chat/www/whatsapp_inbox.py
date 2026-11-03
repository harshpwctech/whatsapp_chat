import frappe
from frappe import _
from frappe.utils import get_system_timezone

from whatsapp_chat.utils.chatbot import is_chatbot_installed


no_cache = 1


def get_context():
	from whatsapp_chat.api.permission import validate_inbox_access

	validate_inbox_access()

	frappe.db.commit()
	return frappe._dict(boot=get_boot())


@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_context_for_dev():
	if not frappe.conf.developer_mode:
		frappe.throw(_("This method is only meant for developer mode"))
	return get_boot()


def get_website_favicon():
	favicon = frappe.db.get_single_value("Website Settings", "favicon")
	if favicon and favicon != "attach_files:":
		return favicon
	return "/assets/frappe/images/frappe-favicon.svg"


def get_boot():
	return frappe._dict(
		{
			"frappe_version": frappe.__version__,
			"site_name": frappe.local.site,
			"csrf_token": frappe.sessions.get_csrf_token(),
			"user": frappe.session.user,
			"user_full_name": frappe.utils.get_fullname(frappe.session.user),
			"socketio_port": frappe.conf.get("socketio_port"),
			"favicon": get_website_favicon(),
			"chatbot_installed": is_chatbot_installed(),
			"timezone": {
				"system": get_system_timezone(),
				"user": frappe.db.get_value("User", frappe.session.user, "time_zone")
				or get_system_timezone(),
			},
		}
	)
