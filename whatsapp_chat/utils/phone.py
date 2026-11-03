import frappe


def normalize_mobile_no(number):
	"""Normalize WhatsApp numbers to a single comparable format (digits only, no +)."""
	if not number:
		return ""

	normalized = str(number).strip()
	if normalized.startswith("+"):
		normalized = normalized[1:]

	for ch in (" ", "-", "(", ")"):
		normalized = normalized.replace(ch, "")

	return normalized


def phone_match_key(number):
	"""Last 10 digits for reliable cross-field phone matching."""
	normalized = normalize_mobile_no(number)
	if len(normalized) >= 10:
		return normalized[-10:]
	return normalized


def find_whatsapp_contact(mobile_no):
	"""Find WhatsApp Contact by number, ignoring +91 vs 91 formatting differences."""
	normalized = normalize_mobile_no(mobile_no)
	if not normalized:
		return None

	for candidate in (normalized, f"+{normalized}"):
		name = frappe.db.get_value("WhatsApp Contact", {"mobile_no": candidate})
		if name:
			return name

	suffix = normalized[-10:] if len(normalized) >= 10 else normalized
	rows = frappe.db.sql(
		"""
		SELECT name
		FROM `tabWhatsApp Contact`
		WHERE REPLACE(REPLACE(IFNULL(mobile_no, ''), '+', ''), ' ', '') LIKE %(pattern)s
		ORDER BY modified DESC
		LIMIT 1
		""",
		{"pattern": f"%{suffix}"},
	)
	return rows[0][0] if rows else None


def normalized_message_filter(field_name, param_name="normalized_no"):
	"""SQL expression to compare a message from/to field against a normalized number."""
	return (
		f"REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(IFNULL(`{field_name}`, ''), '+', ''), "
		f"' ', ''), '-', ''), '(', ''), ')', '') = %({param_name})s"
	)
