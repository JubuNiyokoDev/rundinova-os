// RundiNova Onboarding — checklist de démarrage pour l'équipe fondatrice.
frappe.pages['rundinova-onboarding'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'RundiNova Onboarding',
		single_column: true,
	});

	page.main.html(`
	<div class="rundinova-onboarding container" style="max-width:860px;margin:0 auto;padding:24px 0;">
		<div style="text-align:center;margin-bottom:32px;">
			<img src="/assets/rundinova_tech/images/rundinova-logo.png"
				alt="RundiNova" style="height:64px;margin-bottom:16px;">
			<h2 style="margin:0;">Bienvenue chez RundiNova Tech</h2>
			<p class="text-muted">Suivez ces étapes pour configurer votre espace de travail.</p>
		</div>
		<div id="rundinova-onboarding-steps"></div>
	</div>`);

	const steps = [
		{
			section: 'Équipe & organisation',
			items: [
				{ label: 'Créer le bureau / hub principal', doctype: 'RundiNova Office' },
				{ label: 'Créer les membres de l\'équipe (Users + rôles)', url: '/app/user' },
			],
		},
		{
			section: 'Finance & budget',
			items: [
				{ label: 'Créer le budget alimentaire mensuel', doctype: 'RundiNova Food Budget' },
				{ label: 'Enregistrer les achats alimentaires', doctype: 'RundiNova Food Expense' },
				{ label: 'Ouvrir un compte de caisse', doctype: 'RundiNova Cash Account' },
				{ label: 'Enregistrer les mouvements de trésorerie', doctype: 'RundiNova Cash Movement' },
				{ label: 'Enregistrer les dépenses générales', doctype: 'RundiNova Expense' },
			],
		},
		{
			section: 'Biens & projets',
			items: [
				{ label: 'Enregistrer les équipements', doctype: 'RundiNova Asset' },
				{ label: 'Connecter un dépôt GitHub', doctype: 'RundiNova Repository' },
				{ label: 'Définir les objectifs', doctype: 'RundiNova Goal' },
			],
		},
		{
			section: 'Pilotage & gouvernance',
			items: [
				{ label: 'Définir les KPI', doctype: 'RundiNova KPI Definition' },
				{ label: 'Enregistrer les décisions', doctype: 'RundiNova Decision' },
				{ label: 'Ouvrir le tableau de bord exécutif', url: '/app/dashboard/RundiNova%20Executive%20Dashboard' },
			],
		},
	];

	const container = page.main.find('#rundinova-onboarding-steps');

	steps.forEach((step) => {
		const items_html = step.items.map((item) => {
			const href = item.doctype
				? `/app/${frappe.router.slug(item.doctype)}/new`
				: item.url;
			return `
			<div class="list-row" style="display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid var(--border-color);">
				${frappe.utils.icon('circle', 'sm', 'text-muted')}
				<a href="${href}" style="flex:1;">${item.label}</a>
			</div>`;
		}).join('');

		container.append(`
		<div class="card" style="margin-bottom:16px;">
			<div class="card-header font-weight-bold" style="padding:12px 16px;border-bottom:1px solid var(--border-color);">
				${step.section}
			</div>
			<div class="card-body" style="padding:4px 0;">${items_html}</div>
		</div>`);
	});
};