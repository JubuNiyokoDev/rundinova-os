frappe.pages["rundinova-record-view"].on_page_load = function (wrapper) {
  wrapper.__rn_record_page = frappe.ui.make_app_page({ parent: wrapper, title: __("Détail"), single_column: true });
  $(wrapper.__rn_record_page.body).html('<main class="rn-record-view"></main>');
};

frappe.pages["rundinova-record-view"].on_page_show = function (wrapper) {
  const page = wrapper.__rn_record_page;
  const [route, doctype, name] = frappe.get_route();
  if (route !== "rundinova-record-view" || !doctype || !name) return;
  const escape = (value) => $("<div>").text(value == null ? "" : value).html();
  const statusTone = (status) => ({ Approved: "success", Paid: "success", Completed: "success", Closed: "success", Active: "success", Open: "warning", "In Progress": "info", Submitted: "info", Draft: "muted", Cancelled: "danger", Rejected: "danger", "À préparer": "warning", "À corriger": "danger", Planifiée: "info", Tenue: "success" }[status] || "muted");
  const format = (field, value) => {
    if (field.fieldtype === "Check") return value ? __("Oui") : __("Non");
    if (field.fieldtype === "Date") return frappe.format(value, { fieldtype: "Date" });
    if (field.fieldtype === "Datetime") return frappe.format(value, { fieldtype: "Datetime" });
    if (field.fieldtype === "Time") return String(value).slice(0, 5);
    if (["Currency", "Float", "Percent", "Int"].includes(field.fieldtype)) return frappe.format(value, { fieldtype: field.fieldtype, options: field.options });
    if (field.fieldtype === "Attach" || field.fieldtype === "Attach Image") return `<a href="${escape(value)}" target="_blank" rel="noopener">${__("Ouvrir le fichier")}</a>`;
    return escape(value).replace(/\n/g, "<br>");
  };
  const renderTable = (table) => `<section class="rn-record-section"><h3>${escape(table.label)}</h3><div class="rn-record-table-wrap"><table class="rn-record-table"><thead><tr>${table.columns.map((column) => `<th>${escape(column.label)}</th>`).join("")}</tr></thead><tbody>${table.rows.map((row) => `<tr>${table.columns.map((column) => `<td>${format(column, row[column.fieldname]) || "—"}</td>`).join("")}</tr>`).join("")}</tbody></table></div></section>`;
  const render = (data) => {
    const sections = data.sections.map((section) => `<section class="rn-record-section"><h3>${escape(section.label)}</h3><dl class="rn-record-grid">${section.fields.map((field) => `<div class="rn-record-field"><dt>${escape(field.label)}</dt><dd>${format(field, field.value)}</dd></div>`).join("")}</dl></section>`).join("");
    const badge = data.status ? `<span class="rn-record-status ${statusTone(data.status)}">${escape(data.status)}</span>` : "";
    const edit = data.can_edit ? `<button class="btn btn-primary btn-sm rn-record-edit">${__("Modifier")}</button>` : "";
    $(page.body).find(".rn-record-view").html(`<style>
      .rn-record-view{max-width:1040px;margin:0 auto;padding:4px 0 32px}.rn-record-head{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;padding:6px 0 18px;border-bottom:1px solid var(--border-color)}.rn-record-head h2{margin:0 0 6px;font-size:21px;font-weight:650;color:var(--text-color)}.rn-record-meta{font-size:12px;color:var(--text-muted)}.rn-record-actions{display:flex;gap:8px;align-items:center}.rn-record-status{border-radius:999px;padding:4px 8px;background:var(--control-bg);font-size:12px}.rn-record-status.success{color:var(--green-600,var(--text-color))}.rn-record-status.warning{color:var(--orange-600,var(--text-color))}.rn-record-status.info{color:var(--primary)}.rn-record-status.danger{color:var(--red-600,var(--text-color))}.rn-record-section{margin-top:18px;border:1px solid var(--border-color);border-radius:10px;background:var(--card-bg);overflow:hidden}.rn-record-section h3{margin:0;padding:14px 18px;border-bottom:1px solid var(--border-color);font-size:15px;font-weight:650}.rn-record-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));margin:0}.rn-record-field{padding:13px 18px;border-right:1px solid var(--border-color);border-bottom:1px solid var(--border-color)}.rn-record-field:nth-child(2n){border-right:0}.rn-record-field:nth-last-child(-n+2){border-bottom:0}.rn-record-field dt{font-size:12px;color:var(--text-muted);font-weight:400;margin-bottom:5px}.rn-record-field dd{margin:0;color:var(--text-color);font-size:14px;line-height:1.5;word-break:break-word}.rn-record-table-wrap{overflow:auto}.rn-record-table{width:100%;border-collapse:collapse;font-size:13px}.rn-record-table th,.rn-record-table td{padding:11px 14px;text-align:left;border-bottom:1px solid var(--border-color);vertical-align:top}.rn-record-table th{font-size:12px;color:var(--text-muted);font-weight:500;background:var(--subtle-fg)}.rn-record-table tr:last-child td{border-bottom:0}@media(max-width:700px){.rn-record-head{flex-direction:column}.rn-record-grid{grid-template-columns:1fr}.rn-record-field,.rn-record-field:nth-child(2n){border-right:0}.rn-record-field:nth-last-child(-n+2){border-bottom:1px solid var(--border-color)}.rn-record-field:last-child{border-bottom:0}}
    </style><header class="rn-record-head"><div><h2>${escape(data.title)}</h2><div class="rn-record-meta">${escape(data.doctype)} · ${__("Mis à jour le")} ${escape(frappe.format(data.modified, { fieldtype: "Datetime" }))}</div></div><div class="rn-record-actions">${badge}${edit}</div></header>${sections}${data.tables.map(renderTable).join("")}`);
    $(page.body).find(".rn-record-edit").on("click", () => {
      sessionStorage.setItem("rundinova-edit-route", `${data.doctype}:${data.name}`);
      frappe.set_route("Form", data.doctype, data.name);
    });
  };
  frappe.call({ method: "rundinova_tech.rundinova_tech.record_detail.get_record_detail", args: { doctype, name } }).then(({ message }) => render(message));
};
