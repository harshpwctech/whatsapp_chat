# Copyright (c) 2024, shridhar patil and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from whatsapp_chat.utils.phone import normalize_mobile_no


class WhatsAppContact(Document):

	def before_validate(self):
		if self.mobile_no:
			self.mobile_no = normalize_mobile_no(self.mobile_no)

