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
      description: __(
        "Préparez le catalogue utilisé par les budgets et achats.",
      ),
      items: [
        ["Item", __("Articles")],
        ["Item Group", __("Catégories d’articles")],
        ["Supplier", __("Fournisseurs")],
      ],
    },
    {
      title: __("Accès à la plateforme"),
      description: __("Consultez les comptes employés et leurs rôles RundiNova."),
      items: [],
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
    const rows = section.items
      .map(
        ([doctype, label]) => `
			<a class="list-row" href="/desk/${frappe.router.slug(doctype)}"
				style="display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-top:1px solid var(--border-color);">
				<span>${label}</span><span class="text-muted">${frappe.utils.icon("chevron-right", "sm")}</span>
			</a>
		`,
      )
      .join("");
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

  const can_manage_access = ["RundiNova Director", "System Manager"].some((role) =>
    frappe.user.has_role(role),
  );
  if (!can_manage_access) return;

  container.find("section").last().append(`
    <div style="padding:16px;border-top:1px solid var(--border-color);">
      <p class="text-muted">${__("Cette page gère uniquement les rôles RundiNova. Elle ne peut ni attribuer les droits d’administrateur système ni supprimer un compte.")}</p>
      <div class="rundinova-access-directory"><span class="text-muted">${__("Chargement des comptes…")}</span></div>
    </div>
  `);

  const directory = container.find(".rundinova-access-directory");
  const load_directory = () =>
    frappe.call({
      method: "rundinova_tech.api.get_rundinova_access_directory",
      freeze: true,
      callback(response) {
        const data = response.message || { users: [], roles: [] };
        if (!data.users.length) {
          directory.html(`<p class="text-muted">${__("Aucun compte employé associé.")}</p>`);
          return;
        }
        const options = data.roles
          .map(
            (role) =>
              `<option value="${frappe.utils.escape_html(role)}">${frappe.utils.escape_html(role)}</option>`,
          )
          .join("");
        directory.html(
          data.users
            .map(
              (account) => `
                <div class="rundinova-access-row" style="display:grid;grid-template-columns:minmax(180px,1fr) minmax(260px,2fr) auto;gap:12px;align-items:center;padding:14px 0;border-top:1px solid var(--border-color);">
                  <div><strong>${frappe.utils.escape_html(account.name)}</strong><br><small class="text-muted">${frappe.utils.escape_html(account.user)} · ${account.enabled ? __("Actif") : __("Désactivé")}</small></div>
                  <select class="form-control rundinova-role-select" multiple size="4" data-user="${frappe.utils.escape_html(account.user)}">${options}</select>
                  <button class="btn btn-primary btn-sm rundinova-role-save" data-user="${frappe.utils.escape_html(account.user)}">${__("Enregistrer")}</button>
                </div>
              `,
            )
            .join(""),
        );
        for (const account of data.users) {
          const select = directory.find(`select[data-user="${CSS.escape(account.user)}"]`);
          for (const option of select.find("option")) {
            option.selected = account.roles.includes(option.value);
          }
        }
      },
    });

  directory.on("click", ".rundinova-role-save", function () {
    const user = this.dataset.user;
    const select = directory.find(`select[data-user="${CSS.escape(user)}"]`);
    const roles = [...select[0].selectedOptions].map((option) => option.value);
    frappe.call({
      method: "rundinova_tech.api.update_rundinova_user_roles",
      args: { user, roles: JSON.stringify(roles) },
      freeze: true,
      freeze_message: __("Mise à jour des accès…"),
      callback(response) {
        if (!response.message) return;
        frappe.show_alert({
          message: __("Accès mis à jour pour {0}.", [user]),
          indicator: "green",
        });
        load_directory();
      },
    });
  });

  load_directory();
};
