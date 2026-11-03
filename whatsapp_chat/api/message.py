import ast
import json
import mimetypes

import frappe
from frappe import _

from whatsapp_chat.api.permission import validate_inbox_access
from whatsapp_chat.utils.phone import (
	find_whatsapp_contact,
	normalize_mobile_no,
	normalized_message_filter,
)


@frappe.whitelist()
def get_all(room: str, user_no: str):
	"""Get all messages for a phone number with CRM-style enrichment."""
	validate_inbox_access()
	normalized_no = normalize_mobile_no(user_no)
	if not normalized_no:
		return []

	suffix = normalized_no[-10:] if len(normalized_no) >= 10 else normalized_no
	pattern = f"%{suffix}"

	to_norm = (
		"REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(IFNULL(`to`, ''), '+', ''), "
		"' ', ''), '-', ''), '(', ''), ')', '')"
	)
	from_norm = (
		"REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(IFNULL(`from`, ''), '+', ''), "
		"' ', ''), '-', ''), '(', ''), ')', '')"
	)

	messages = frappe.db.sql(
		f"""
		SELECT
			name,
			creation,
			type,
			COALESCE(content_type, 'text') AS content_type,
			message_type,
			message,
			attach,
			template,
			use_template,
			message_id,
			is_reply,
			reply_to_message_id,
			status,
			template_parameters,
			template_header_parameters,
			buttons,
			`from`,
			`to`
		FROM `tabWhatsApp Message`
		WHERE ({to_norm} LIKE %(pattern)s OR {from_norm} LIKE %(pattern)s)
		ORDER BY creation ASC
		""",
		{"pattern": pattern},
		as_dict=True,
	)

	_enrich_template_messages(messages)
	_enrich_reactions(messages)
	_enrich_replies(messages)

	contact_name = _get_contact_display_name(room, user_no)

	result = []
	for message in messages:
		if message.content_type == "reaction":
			continue
		if not _should_include_message(message):
			continue

		message["from_name"] = (
			contact_name if message.type == "Incoming" else frappe._("You")
		)
		message["sender_user_no"] = (
			message.get("from") or "" if message.type == "Incoming" else "Administrator"
		)
		result.append(message)

	return result


def _should_include_message(message):
	if message.get("attach"):
		return True
	if message.get("message_type") == "Template":
		return True
	if message.get("content_type") in ("button", "interactive", "image", "document", "audio", "video"):
		return True
	if (message.get("message") or "").strip():
		return True
	return False


def _enrich_template_messages(messages):
	template_messages = [m for m in messages if m.message_type == "Template"]
	for template_message in template_messages:
		template_name = template_message.get("template")
		if not template_name or not frappe.db.exists("WhatsApp Templates", template_name):
			continue

		template = frappe.get_doc("WhatsApp Templates", template_name)
		template_message["template_name"] = template.template_name

		body = template.template or ""
		if template_message.get("template_parameters"):
			try:
				parameters = json.loads(template_message["template_parameters"])
				body = _parse_template_parameters(body, parameters)
			except (json.JSONDecodeError, TypeError):
				pass
		template_message["template"] = body

		header = template.header or ""
		if template_message.get("template_header_parameters"):
			try:
				header_parameters = json.loads(template_message["template_header_parameters"])
				header = _parse_template_parameters(header, header_parameters)
			except (json.JSONDecodeError, TypeError):
				pass
		template_message["header"] = header
		template_message["footer"] = template.footer or ""
		template_message["header_type"] = (template.header_type or "TEXT").upper()
		header_media, header_filename = _resolve_template_header_media(
			template_message, template
		)
		template_message["header_media"] = header_media
		template_message["header_filename"] = header_filename


def _parse_stored_template_payload(message_text):
	"""Parse template payload stored on WhatsApp Message.message."""
	if not message_text or not isinstance(message_text, str):
		return None

	text = message_text.strip()
	if not text.startswith("{"):
		return None

	for parser in (json.loads, ast.literal_eval):
		try:
			payload = parser(text)
		except (json.JSONDecodeError, SyntaxError, TypeError, ValueError):
			continue
		if isinstance(payload, dict):
			return payload.get("template", payload)

	return None


def _extract_header_media_from_payload(payload):
	"""Extract header media URL and filename from a stored template payload."""
	if not isinstance(payload, dict):
		return "", ""

	for component in payload.get("components") or []:
		if component.get("type") != "header":
			continue

		parameters = component.get("parameters") or []
		if not parameters:
			continue

		param = parameters[0] or {}
		param_type = (param.get("type") or "").lower()

		if param_type == "document":
			document = param.get("document") or {}
			return document.get("link") or "", document.get("filename") or ""

		if param_type == "image":
			return (param.get("image") or {}).get("link") or "", ""

		if param_type == "video":
			return (param.get("video") or {}).get("link") or "", ""

	return "", ""


def _resolve_template_header_media(template_message, template):
	"""Resolve image/document URL and filename for template headers."""
	header_type = (template.header_type or "").upper()

	stored_payload = _parse_stored_template_payload(template_message.get("message"))
	if stored_payload:
		media, filename = _extract_header_media_from_payload(stored_payload)
		if media:
			return media, filename

	if template_message.get("template_header_parameters"):
		try:
			header_parameters = json.loads(template_message["template_header_parameters"])
			if header_parameters:
				media = str(header_parameters[0] or "").strip()
				if media:
					return media, ""
		except (json.JSONDecodeError, TypeError):
			pass

	if template_message.get("attach"):
		attach = template_message.attach
		filename = attach.split("/")[-1] if attach else ""
		return attach, filename

	if header_type in ("IMAGE", "DOCUMENT", "VIDEO") and template.sample:
		filename = template.sample.split("/")[-1] if template.sample else ""
		return template.sample, filename

	return "", ""


def _enrich_reactions(messages):
	reaction_messages = [m for m in messages if m.content_type == "reaction"]
	for reaction_message in reversed(reaction_messages):
		reacted_message = next(
			(m for m in messages if m.get("message_id") == reaction_message.get("reply_to_message_id")),
			None,
		)
		if reacted_message:
			reacted_message["reaction"] = reaction_message.get("message")


def _enrich_replies(messages):
	reply_messages = [m for m in messages if m.get("is_reply")]
	for reply_message in reply_messages:
		replied_message = next(
			(m for m in messages if m.get("message_id") == reply_message.get("reply_to_message_id")),
			None,
		)
		if not replied_message:
			continue

		reply_text = replied_message.get("message") or ""
		if replied_message.get("message_type") == "Template":
			reply_text = replied_message.get("template") or reply_text

		from_name = (
			_get_phone_display_name(replied_message.get("from"))
			if replied_message.get("type") == "Incoming"
			else frappe._("You")
		)
		reply_message["reply_message"] = reply_text
		reply_message["header"] = replied_message.get("header") or ""
		reply_message["footer"] = replied_message.get("footer") or ""
		reply_message["header_type"] = replied_message.get("header_type") or ""
		reply_message["header_media"] = replied_message.get("header_media") or ""
		reply_message["header_filename"] = replied_message.get("header_filename") or ""
		reply_message["reply_to"] = replied_message.get("name")
		reply_message["reply_to_type"] = replied_message.get("type")
		reply_message["reply_to_from"] = from_name


def _parse_template_parameters(string, parameters):
	if not string or not parameters:
		return string or ""
	for i, parameter in enumerate(parameters, start=1):
		placeholder = "{{" + str(i) + "}}"
		string = string.replace(placeholder, str(parameter))
	return string


def _get_contact_display_name(room, user_no):
	if room and frappe.db.exists("WhatsApp Contact", room):
		contact = frappe.db.get_value(
			"WhatsApp Contact",
			room,
			["contact_name", "mobile_no"],
			as_dict=True,
		)
		if contact and contact.contact_name:
			return contact.contact_name
		if contact and contact.mobile_no:
			return contact.mobile_no

	contact_name = find_whatsapp_contact(user_no)
	if contact_name:
		name = frappe.db.get_value("WhatsApp Contact", contact_name, "contact_name")
		if name:
			return name

	return _get_phone_display_name(user_no)


def _get_phone_display_name(phone):
	return phone or frappe._("Contact")


@frappe.whitelist()
def mark_as_read(room):
	"""Mark messages as read in local DB and optionally send read receipts to WhatsApp."""
	validate_inbox_access()
	try:
		frappe.db.set_value("WhatsApp Contact", room, "is_read", 1, update_modified=False)
		frappe.db.commit()
		send_whatsapp_read_receipts(room)
	except Exception:
		pass
	return "ok"


def send_whatsapp_read_receipts(room):
	"""Send read receipts to WhatsApp for unread incoming messages."""
	try:
		contact = frappe.get_doc("WhatsApp Contact", room)
		if not contact.mobile_no:
			return

		normalized_no = normalize_mobile_no(contact.mobile_no)
		from_filter = normalized_message_filter("from")
		unread_messages = frappe.db.sql(
			f"""
			SELECT name, whatsapp_account
			FROM `tabWhatsApp Message`
			WHERE {from_filter}
			AND type = 'Incoming'
			AND COALESCE(status, '') NOT IN ('marked as read')
			ORDER BY creation DESC
			LIMIT 10
			""",
			{"normalized_no": normalized_no},
			as_dict=True,
		)

		if not unread_messages:
			return

		for msg in unread_messages:
			if not msg.whatsapp_account:
				continue

			allow_auto_read = frappe.db.get_value(
				"WhatsApp Account",
				msg.whatsapp_account,
				"allow_auto_read_receipt",
			)

			if allow_auto_read:
				try:
					msg_doc = frappe.get_doc("WhatsApp Message", msg.name)
					msg_doc.send_read_receipt()
				except Exception as e:
					frappe.log_error(
						f"Failed to send read receipt for {msg.name}: {str(e)}",
						"WhatsApp Chat Read Receipt",
					)
	except Exception as e:
		frappe.log_error(f"send_whatsapp_read_receipts error: {str(e)}", "WhatsApp Chat Read Receipt")


@frappe.whitelist()
def send(content, user, room, user_no, attachment=None, reply_to=None):
	validate_inbox_access()
	content_type = "text"
	doc_data = {
		"doctype": "WhatsApp Message",
		"to": user_no,
		"type": "Outgoing",
		"content_type": content_type,
		"message_type": "Manual",
	}

	if reply_to and frappe.db.exists("WhatsApp Message", reply_to):
		reply_doc = frappe.get_doc("WhatsApp Message", reply_to)
		doc_data["is_reply"] = True
		doc_data["reply_to_message_id"] = reply_doc.message_id

	if attachment:
		file_type = mimetypes.guess_type(content)[0]
		if file_type in [
			"image/apng",
			"image/avif",
			"image/gif",
			"image/jpeg",
			"image/png",
			"image/svg",
			"image/webp",
		]:
			content_type = "image"
		elif file_type in [
			"application/pdf",
			"application/vnd.ms-powerpoint",
			"application/msword",
			"application/vnd.ms-excel",
			"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
			"application/vnd.openxmlformats-officedocument.presentationml.presentation",
			"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
		]:
			content_type = "document"
		elif file_type in ["audio/aac", "audio/mp4", "audio/mpeg", "audio/amr", "audio/ogg"]:
			content_type = "audio"
		elif file_type in ["video/mp4", "video/3gp"]:
			content_type = "video"

		doc_data.update({
			"attach": content,
			"content_type": content_type,
		})
		frappe.get_doc(doc_data).save()
	else:
		doc_data.update({
			"message": content,
			"content_type": content_type,
		})
		frappe.get_doc(doc_data).save()

	return "ok"


@frappe.whitelist()
def react_on_message(emoji, reply_to_name):
	validate_inbox_access()
	if not frappe.db.exists("WhatsApp Message", reply_to_name):
		frappe.throw(_("Referenced WhatsApp message does not exist."), frappe.DoesNotExistError)

	reply_to_doc = frappe.get_doc("WhatsApp Message", reply_to_name)
	to = (reply_to_doc.type == "Incoming" and reply_to_doc.get("from")) or reply_to_doc.to

	doc = frappe.new_doc("WhatsApp Message")
	doc.update(
		{
			"message": emoji,
			"to": to,
			"reply_to_message_id": reply_to_doc.message_id,
			"content_type": "reaction",
			"type": "Outgoing",
			"message_type": "Manual",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def last_message(doc, method):
	if doc.type == "Outgoing":
		mobile_no = doc.to
	else:
		mobile_no = doc.get("from")

	normalized_no = normalize_mobile_no(mobile_no)
	contact_name = find_whatsapp_contact(mobile_no)
	if contact_name:
		chat_doc = frappe.get_doc("WhatsApp Contact", contact_name)
		if normalize_mobile_no(chat_doc.mobile_no) != chat_doc.mobile_no:
			chat_doc.mobile_no = normalized_no
		chat_doc.last_message = doc.message
		chat_doc.is_read = 0
		chat_doc.save(ignore_permissions=True)
	else:
		chat_doc = frappe.get_doc(
			{
				"doctype": "WhatsApp Contact",
				"mobile_no": normalized_no,
				"last_message": doc.message,
				"contact_name": normalized_no,
				"is_read": 0,
			}
		)
		chat_doc.save(ignore_permissions=True)

	if doc.type != "Outgoing":
		message_data = {
			"content": doc.message or doc.attach or "",
			"creation": frappe.utils.now(),
			"room": chat_doc.name,
			"contact_name": chat_doc.contact_name,
			"sender_user_no": mobile_no,
			"user": "Guest",
			"mobile_no": normalized_no,
			"type": "Incoming",
		}
	else:
		message_data = {
			"content": doc.message or doc.attach or "",
			"creation": frappe.utils.now(),
			"room": chat_doc.name,
			"contact_name": chat_doc.contact_name,
			"sender_user_no": "Administrator",
			"user": frappe.session.user,
			"mobile_no": normalized_no,
			"type": "Outgoing",
		}

	frappe.publish_realtime("whatsapp_inbox_update", message_data)

	return "ok"
