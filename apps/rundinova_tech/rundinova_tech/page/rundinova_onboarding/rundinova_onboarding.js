frappe.pages["rundinova-onboarding"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("RundiNova · Préparation au démarrage"),
    single_column: true,
  });

  const body = $("<div class='rundinova-onboarding p-4'></div>").appendTo(page.body);
  body.html(`
    <div class="mb-4">
      <h3>${__("Préparation au démarrage")}</h3>
      <p class="text-muted">${__("Cette page est en lecture seule. Elle indique ce qui doit être préparé avant l’utilisation réelle de RundiNova OS.")}</p>
    </div>
    <div class="rundinova-onboarding-summary mb-3"></div>
    <div class="rundinova-onboarding-checks"></div>
  `);

  frappe.call({
    method: "rundinova_tech.api.get_onboarding_status",
    callback: (response) => {
      const result = response.message || { ready: false, checks: [] };
      const summary = result.ready
        ? `<div class="alert alert-success">${__("La préparation minimale est complète.")}</div>`
        : `<div class="alert alert-warning">${__("La production n’est pas encore prête. Complète les éléments ci-dessous.")}</div>`;
      body.find(".rundinova-onboarding-summary").html(summary);

      const rows = (result.checks || []).map((item) => {
        const icon = item.ready ? "✓" : "!";
        const color = item.ready ? "text-success" : "text-warning";
        return `<div class="list-group-item d-flex align-items-start">
          <span class="${color} font-weight-bold mr-3">${icon}</span>
          <div><strong>${frappe.utils.escape_html(item.label)}</strong>
          <div class="text-muted small">${frappe.utils.escape_html(item.detail)}</div></div>
        </div>`;
      }).join("");
      body.find(".rundinova-onboarding-checks").html(`<div class="list-group">${rows}</div>`);
    },
  });
};
