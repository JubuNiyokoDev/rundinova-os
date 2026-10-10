// Open each team member's assigned RundiNova workspace at Desk startup.
frappe.pages['rundinova-home'].on_page_load = function () {
	const configured = frappe.boot?.user?.default_workspace;
	const workspace = typeof configured === 'string' ? configured : configured?.name;
	frappe.set_route(`workspace/${workspace || 'RundiNova Tech'}`);
};
