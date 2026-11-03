import frappe
from frappe import _

from whatsapp_chat.api.permission import ALLOWED_WHATSAPP_ROLES, validate_inbox_access
from whatsapp_chat.utils.chatbot import is_chatbot_installed, require_chatbot
from whatsapp_chat.utils.phone import (
	find_whatsapp_contact,
	normalize_mobile_no,
	phone_match_key,
)

INBOX_PAGE_SIZE = 50
SEARCH_PAGE_SIZE = 50

CONTACT_FIELDS = [
	"name",
	"contact_name",
	"mobile_no",
	"is_read",
	"last_message",
	"email",
	"modified",
	"creation",
]


def _get_transfer_map():
	"""Return {phone_match_key: transfer_dict} for active transfers."""
	transfers = frappe.get_all(
		"WhatsApp Agent Transfer",
		filters={"status": "Active"},
		fields=[
			"name",
			"phone_number",
			"whatsapp_account",
			"agent",
			"agent_name",
			"transferred_at",
			"notes",
		],
	)
	result = {}
	for transfer in transfers:
		key = phone_match_key(transfer.phone_number)
		if key and key not in result:
			result[key] = transfer
	return result


def _get_session_map():
	"""Return {phone_match_key: session_dict} for active chatbot sessions."""
	sessions = frappe.get_all(
		"WhatsApp Chatbot Session",
		filters={"status": "Active"},
		fields=[
			"name",
			"phone_number",
			"whatsapp_account",
			"current_flow",
			"current_step",
			"started_at",
			"last_activity",
			"session_data",
		],
		order_by="last_activity desc",
	)
	result = {}
	for session in sessions:
		key = phone_match_key(session.phone_number)
		if key and key not in result:
			result[key] = session
	return result


def _flow_title(flow_name):
	if not flow_name:
		return None
	return frappe.db.get_value("WhatsApp Chatbot Flow", flow_name, "flow_name") or flow_name


def _get_maps():
	if not is_chatbot_installed():
		return {}, {}
	return _get_transfer_map(), _get_session_map()


def _enrich_contact(contact, transfer_map, session_map):
	phone_key = phone_match_key(contact.get("mobile_no"))
	contact["phone_normalized"] = normalize_mobile_no(contact.get("mobile_no"))

	if not is_chatbot_installed():
		return contact

	transfer = transfer_map.get(phone_key)
	session = session_map.get(phone_key)
	contact["is_transferred"] = bool(transfer)
	contact["transfer"] = transfer
	contact["has_bot_session"] = bool(session)
	contact["bot_session"] = session
	contact["current_flow_title"] = _flow_title(session.current_flow) if session else None
	return contact


def _session_to_inbox_item(session, transfer_map):
	phone_key = phone_match_key(session.phone_number)
	transfer = transfer_map.get(phone_key)
	return {
		"name": None,
		"contact_name": session.phone_number,
		"mobile_no": normalize_mobile_no(session.phone_number) or session.phone_number,
		"is_read": 1,
		"last_message": "",
		"email": None,
		"modified": session.last_activity or session.started_at,
		"creation": session.started_at,
		"phone_normalized": normalize_mobile_no(session.phone_number),
		"is_transferred": bool(transfer),
		"transfer": transfer,
		"has_bot_session": True,
		"bot_session": session,
		"current_flow_title": _flow_title(session.current_flow),
	}


def _contact_from_session(session, transfer_map, session_map):
	contact_name = find_whatsapp_contact(session.phone_number)
	if contact_name:
		contact = frappe.get_doc("WhatsApp Contact", contact_name)
		return _enrich_contact(contact.as_dict(), transfer_map, session_map)
	return _session_to_inbox_item(session, transfer_map)


def _get_bot_inbox(session_map, transfer_map):
	items = []
	for session in session_map.values():
		items.append(_contact_from_session(session, transfer_map, session_map))
	items.sort(key=lambda x: x.get("modified") or "", reverse=True)
	return items


def _get_transferred_inbox(transfer_map, session_map):
	items = []
	seen_keys = set()

	for transfer in transfer_map.values():
		key = phone_match_key(transfer.phone_number)
		if not key or key in seen_keys:
			continue
		seen_keys.add(key)

		contact_name = find_whatsapp_contact(transfer.phone_number)
		if contact_name:
			contact = frappe.get_doc("WhatsApp Contact", contact_name)
			items.append(_enrich_contact(contact.as_dict(), transfer_map, session_map))
		else:
			items.append({
				"name": None,
				"contact_name": transfer.phone_number,
				"mobile_no": normalize_mobile_no(transfer.phone_number) or transfer.phone_number,
				"is_read": 1,
				"last_message": transfer.notes or "",
				"email": transfer.agent,
				"modified": transfer.transferred_at,
				"creation": transfer.transferred_at,
				"phone_normalized": normalize_mobile_no(transfer.phone_number),
				"is_transferred": True,
				"transfer": transfer,
				"has_bot_session": key in session_map,
				"bot_session": session_map.get(key),
				"current_flow_title": _flow_title(
					session_map[key].current_flow if key in session_map else None
				),
			})

	items.sort(key=lambda x: x.get("modified") or "", reverse=True)
	return items


def _paginate_list(items, page, page_size):
	page = max(int(page or 1), 1)
	page_size = max(int(page_size or INBOX_PAGE_SIZE), 1)
	start = (page - 1) * page_size
	chunk = items[start : start + page_size + 1]
	has_more = len(chunk) > page_size
	return chunk[:page_size], has_more


def _inbox_page(page, page_size):
	page = max(int(page or 1), 1)
	page_size = max(int(page_size or INBOX_PAGE_SIZE), 1)
	return page, page_size, (page - 1) * page_size


def _inbox_response(items, has_more, page, page_size):
	return {
		"items": items,
		"has_more": has_more,
		"page": page,
		"page_size": page_size,
	}


def _search_contacts(search, page=1, page_size=SEARCH_PAGE_SIZE):
	search = (search or "").strip()
	if not search:
		return [], False

	page, page_size, limit_start = _inbox_page(page, page_size)
	like = f"%{search}%"
	contacts = frappe.get_all(
		"WhatsApp Contact",
		or_filters=[
			["contact_name", "like", like],
			["mobile_no", "like", like],
			["last_message", "like", like],
			["email", "like", like],
		],
		fields=CONTACT_FIELDS,
		order_by="modified desc",
		limit_start=limit_start,
		limit_page_length=page_size + 1,
	)
	has_more = len(contacts) > page_size
	return contacts[:page_size], has_more


def _search_inbox(search, tab, transfer_map, session_map, page=1, page_size=INBOX_PAGE_SIZE):
	search = (search or "").strip().lower()
	if not search:
		return [], False

	if tab == "bot":
		items = _get_bot_inbox(session_map, transfer_map)
	elif tab == "transferred":
		items = _get_transferred_inbox(transfer_map, session_map)
	else:
		contacts, has_more = _search_contacts(search, page, page_size)
		items = [_enrich_contact(contact, transfer_map, session_map) for contact in contacts]

		seen_keys = {phone_match_key(item.get("mobile_no")) for item in items}
		if is_chatbot_installed() and page == 1:
			for session in session_map.values():
				phone = session.phone_number or ""
				if search in phone.lower() or search in normalize_mobile_no(phone):
					key = phone_match_key(phone)
					if key and key not in seen_keys:
						seen_keys.add(key)
						items.append(_session_to_inbox_item(session, transfer_map))

		items.sort(key=lambda x: x.get("modified") or "", reverse=True)
		return items, has_more

	filtered = [
		item
		for item in items
		if search in (item.get("contact_name") or "").lower()
		or search in (item.get("mobile_no") or "").lower()
		or search in (item.get("last_message") or "").lower()
		or search in (item.get("current_flow_title") or "").lower()
		or search in (item.get("email") or "").lower()
	]
	return _paginate_list(filtered, page, page_size)


def _get_all_inbox(transfer_map, session_map, page=1, page_size=INBOX_PAGE_SIZE):
	page, page_size, limit_start = _inbox_page(page, page_size)
	contacts = frappe.get_all(
		"WhatsApp Contact",
		fields=CONTACT_FIELDS,
		order_by="modified desc",
		limit_start=limit_start,
		limit_page_length=page_size + 1,
	)
	has_more = len(contacts) > page_size
	contacts = contacts[:page_size]

	items = []
	seen_keys = set()

	for contact in contacts:
		key = phone_match_key(contact.get("mobile_no"))
		if key:
			seen_keys.add(key)
		items.append(_enrich_contact(contact, transfer_map, session_map))

	# Include active bot sessions that have no WhatsApp Contact yet (first page only)
	if page == 1 and is_chatbot_installed():
		for session in session_map.values():
			key = phone_match_key(session.phone_number)
			if not key or key in seen_keys:
				continue
			seen_keys.add(key)
			items.append(_session_to_inbox_item(session, transfer_map))

	items.sort(key=lambda x: x.get("modified") or "", reverse=True)
	return items, has_more


@frappe.whitelist()
def get_inbox(tab="all", search=None, page=1, page_size=INBOX_PAGE_SIZE):
	"""Get inbox conversations with chatbot session and transfer metadata."""
	validate_inbox_access()

	tab = (tab or "all").lower()
	page, page_size, _ = _inbox_page(page, page_size)

	if tab in ("bot", "transferred") and not is_chatbot_installed():
		return _inbox_response([], False, page, page_size)

	transfer_map, session_map = _get_maps()

	search = (search or "").strip()
	if search:
		items, has_more = _search_inbox(search, tab, transfer_map, session_map, page, page_size)
		return _inbox_response(items, has_more, page, page_size)

	if tab == "bot":
		items, has_more = _paginate_list(_get_bot_inbox(session_map, transfer_map), page, page_size)
	elif tab == "transferred":
		items, has_more = _paginate_list(
			_get_transferred_inbox(transfer_map, session_map), page, page_size
		)
	else:
		items, has_more = _get_all_inbox(transfer_map, session_map, page, page_size)

	return _inbox_response(items, has_more, page, page_size)


@frappe.whitelist()
def get_conversation_detail(phone_number):
	"""Get session, transfer, and contact info for a phone number."""
	validate_inbox_access()
	phone_key = phone_match_key(phone_number)
	transfer_map, session_map = _get_maps()

	contact_name = find_whatsapp_contact(phone_number)
	contact = None
	if contact_name:
		contact = frappe.get_doc("WhatsApp Contact", contact_name).as_dict()

	result = {
		"phone_number": normalize_mobile_no(phone_number),
		"contact": contact,
	}

	if is_chatbot_installed():
		result.update(
			{
				"bot_session": session_map.get(phone_key),
				"transfer": transfer_map.get(phone_key),
				"is_transferred": phone_key in transfer_map,
				"has_bot_session": phone_key in session_map,
			}
		)

	return result


def _whatsapp_account_for_phone(phone_number):
	"""Resolve WhatsApp account from an active bot session when available."""
	if not is_chatbot_installed():
		return None

	_, session_map = _get_maps()
	session = session_map.get(phone_match_key(phone_number))
	if session:
		return session.get("whatsapp_account")
	return None


def _ensure_agent_transfer(phone_number, agent, whatsapp_account=None, notes=None):
	from frappe_whatsapp_chatbot.frappe_whatsapp_chatbot.doctype.whatsapp_agent_transfer.whatsapp_agent_transfer import (
		WhatsAppAgentTransfer,
	)

	doc = WhatsAppAgentTransfer.transfer_to_agent(
		phone_number=phone_number,
		whatsapp_account=whatsapp_account,
		agent=agent,
		notes=notes,
	)
	if agent and doc.agent != agent:
		doc.agent = agent
		doc.save(ignore_permissions=True)
	return doc


@frappe.whitelist()
def transfer_to_agent(phone_number, whatsapp_account=None, agent=None, notes=None):
	"""Transfer a chatbot session to a human agent."""
	validate_inbox_access()
	require_chatbot()
	if not phone_number:
		frappe.throw(_("Phone number is required"))

	agent = agent or frappe.session.user

	doc = _ensure_agent_transfer(
		phone_number=phone_number,
		whatsapp_account=whatsapp_account,
		agent=agent,
		notes=notes,
	)

	contact_name = find_whatsapp_contact(phone_number)
	if contact_name:
		frappe.db.set_value("WhatsApp Contact", contact_name, "email", agent, update_modified=False)
	elif phone_number:
		normalized = normalize_mobile_no(phone_number)
		frappe.get_doc(
			{
				"doctype": "WhatsApp Contact",
				"contact_name": phone_number,
				"mobile_no": normalized,
				"email": agent,
			}
		).insert(ignore_permissions=True)

	frappe.db.commit()

	frappe.publish_realtime(
		"whatsapp_inbox_update",
		{
			"type": "transfer",
			"phone_number": normalize_mobile_no(phone_number),
			"agent": agent,
		},
	)

	return {
		"status": "transferred",
		"name": doc.name,
		"phone_number": phone_number,
		"agent": agent,
	}


@frappe.whitelist()
def resume_chatbot(phone_number, whatsapp_account=None):
	"""Resume chatbot for a phone number after agent handoff."""
	validate_inbox_access()
	require_chatbot()
	if not phone_number:
		frappe.throw(_("Phone number is required"))

	from frappe_whatsapp_chatbot.frappe_whatsapp_chatbot.doctype.whatsapp_agent_transfer.whatsapp_agent_transfer import (
		WhatsAppAgentTransfer,
	)

	resumed = WhatsAppAgentTransfer.resume_chatbot(
		phone_number=phone_number,
		whatsapp_account=whatsapp_account,
	)

	frappe.publish_realtime(
		"whatsapp_inbox_update",
		{
			"type": "resume",
			"phone_number": normalize_mobile_no(phone_number),
		},
	)

	if resumed:
		return {
			"status": "resumed",
			"phone_number": phone_number,
			"message": _("Chatbot has been resumed for this number"),
		}

	return {
		"status": "not_found",
		"phone_number": phone_number,
		"message": _("No active transfer found for this number"),
	}


@frappe.whitelist()
def get_assignable_agents():
	"""Users who may be assigned as WhatsApp inbox agents."""
	validate_inbox_access()

	allowed_users = {"Administrator"}
	for role in ALLOWED_WHATSAPP_ROLES:
		for user in frappe.get_all(
			"Has Role",
			filters={"role": role, "parenttype": "User"},
			pluck="parent",
		):
			allowed_users.add(user)

	users = frappe.get_all(
		"User",
		filters={"enabled": 1, "name": ["in", list(allowed_users)]},
		fields=["name", "full_name"],
		order_by="full_name asc",
	)
	return [{"value": user.name, "label": user.full_name or user.name} for user in users]


@frappe.whitelist()
def assign_contact(contact_name, agent):
	"""Assign a WhatsApp Contact to an agent and create an active agent transfer."""
	validate_inbox_access()
	if not contact_name:
		frappe.throw(_("Contact is required"))

	contact = frappe.get_doc("WhatsApp Contact", contact_name)
	agent = (agent or "").strip()

	frappe.db.set_value("WhatsApp Contact", contact_name, "email", agent, update_modified=False)

	transfer_name = None
	if is_chatbot_installed():
		from frappe_whatsapp_chatbot.frappe_whatsapp_chatbot.doctype.whatsapp_agent_transfer.whatsapp_agent_transfer import (
			WhatsAppAgentTransfer,
		)

		if agent:
			whatsapp_account = _whatsapp_account_for_phone(contact.mobile_no)
			transfer = _ensure_agent_transfer(
				phone_number=contact.mobile_no,
				whatsapp_account=whatsapp_account,
				agent=agent,
				notes=_("Assigned from WhatsApp Inbox"),
			)
			transfer_name = transfer.name
			frappe.publish_realtime(
				"whatsapp_inbox_update",
				{
					"type": "transfer",
					"phone_number": normalize_mobile_no(contact.mobile_no),
					"agent": agent,
				},
			)
		else:
			WhatsAppAgentTransfer.resume_chatbot(phone_number=contact.mobile_no)
			frappe.publish_realtime(
				"whatsapp_inbox_update",
				{
					"type": "resume",
					"phone_number": normalize_mobile_no(contact.mobile_no),
				},
			)

	frappe.db.commit()
	return {
		"status": "ok",
		"contact": contact_name,
		"agent": agent,
		"transfer": transfer_name,
	}
