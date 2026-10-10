// Give administrators one concise place for initial company configuration.
frappe.pages["rundinova-setup"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Configuration RundiNova"),
		single_column: true,
	});

	const sections = [
		{
			title: __("Organisation"),
			description: __("Définissez l’entreprise, ses bureaux et ses équipes."),
			items: [
				["Company", __("Entreprise")],
				["Branch", __("Bureaux et agences")],
				["Department", __("Départements")],
				["Cost Center", __("Centres de coûts")],
			],
		},
		{
			title: __("Articles et fournisseurs"),
			description: __("Préparez le catalogue utilisé par les budgets et achats."),
			items: [
				["Item", __("Articles")],
				["Item Group", __("Catégories d’articles")],
				["Supplier", __("Fournisseurs")],
			],
		},
		{
			title: __("Accès à la plateforme"),
			description: __("Créez les comptes et attribuez les rôles de travail."),
			items: [["User", __("Utilisateurs")]],
		},
	];

	page.main.html(`
		<div class="rundinova-setup container" style="max-width:1040px;margin:0 auto;padding:24px 0;">
			<div style="margin-bottom:24px;">
				<p class="text-muted">${__("Administration de l’espace RundiNova Tech")}</p>
				<h2>${__("Configuration de départ")}</h2>
				<p class="text-muted">${__("Ces réglages structurent la plateforme. Les opérations quotidiennes et les tableaux de bord restent dans l’espace RundiNova Tech.")}</p>
			</div>
			<div class="rundinova-setup-sections"></div>
		</div>
	`);

	const container = page.main.find(".rundinova-setup-sections");
	for (const section of sections) {
		const rows = section.items.map(([doctype, label]) => `
			<a class="list-row" href="/desk/${frappe.router.slug(doctype)}"
				style="display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-top:1px solid var(--border-color);">
				<span>${label}</span><span class="text-muted">${frappe.utils.icon("chevron-right", "sm")}</span>
			</a>
		`).join("");
		container.append(`
			<section class="card" style="margin-bottom:16px;overflow:hidden;">
				<div style="padding:16px 16px 10px;">
					<h3 style="margin:0 0 4px;font-size:16px;">${section.title}</h3>
					<p class="text-muted" style="margin:0;">${section.description}</p>
				</div>
				${rows}
			</section>
		`);
	}
};
