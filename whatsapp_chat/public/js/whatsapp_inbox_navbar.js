(function () {
	if (typeof frappe === 'undefined') {
		return;
	}

	frappe.provide('whatsapp_chat');

	// Keep in sync with whatsapp_chat.api.permission.ALLOWED_WHATSAPP_ROLES
	whatsapp_chat.ALLOWED_ROLES = ['System Manager', 'Sales Manager', 'Sales User'];

	whatsapp_chat.WHATSAPP_ICON = `
<svg class="whatsapp-inbox-nav-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.435 9.884-9.883 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
</svg>`;

	whatsapp_chat.has_inbox_permission = function () {
		if (!frappe.session || !frappe.session.user || frappe.session.user === 'Guest') {
			return false;
		}
		if (frappe.session.user === 'Administrator') {
			return true;
		}
		const roles = (frappe.boot && frappe.boot.user && frappe.boot.user.roles) || [];
		return whatsapp_chat.ALLOWED_ROLES.some((role) => roles.includes(role));
	};

	whatsapp_chat.render_inbox_navbar = function () {
		if (!('desk' in frappe) || !whatsapp_chat.has_inbox_permission()) {
			return;
		}

		if (document.querySelector('.whatsapp-inbox-navbar-icon')) {
			return;
		}

		const label = (typeof __ === 'function' && __('WhatsApp Inbox')) || 'WhatsApp Inbox';
		const html = `
			<li class="nav-item dropdown-mobile whatsapp-inbox-navbar-icon" title="${label}">
				<a class="btn-reset nav-link text-muted" href="/whatsapp-inbox" target="_blank" rel="noopener noreferrer" aria-label="${label}">
					${whatsapp_chat.WHATSAPP_ICON}
				</a>
			</li>
		`;

		const selectors = [
			'header.navbar .navbar-collapse > ul.navbar-nav',
			'header.navbar > .container > .navbar-collapse > ul',
		];

		for (const selector of selectors) {
			const $nav = $(selector);
			if ($nav.length) {
				$nav.prepend(html);
				return;
			}
		}
	};

	whatsapp_chat.setup_inbox_navbar = function () {
		if (!frappe.boot || !frappe.session) {
			return;
		}
		whatsapp_chat.render_inbox_navbar();
	};

	function schedule_setup() {
		whatsapp_chat.setup_inbox_navbar();
		[300, 1000, 2500].forEach((delay) => {
			setTimeout(whatsapp_chat.setup_inbox_navbar, delay);
		});
	}

	$(schedule_setup);
})();
