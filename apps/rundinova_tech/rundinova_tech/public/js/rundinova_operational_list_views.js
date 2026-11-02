// Purpose-built list views: each operational register foregrounds the data
// people use to make a decision, while retaining Frappe's native filters,
// export, permissions and document actions.
frappe.listview_settings = frappe.listview_settings || {};

const rnMoney = (value) =>
  frappe.format(value || 0, { fieldtype: "Currency", options: "currency" });

const rnStatus = (labels) => (doc) => {
  const [label, color] = labels[doc.status] || [doc.status || "—", "gray"];
  return [__(label), color, `status,=,${doc.status}`];
};

const rnQuickFilter = (doctype, field, value) => {
  frappe.route_options = { [field]: value };
  frappe.set_route("List", doctype);
};

const rnAddButtons = (listview, key, buttons) => {
  if (listview.page[key]) return;
  listview.page[key] = true;
  buttons.forEach(([label, field, value]) => {
    listview.page.add_inner_button(__(label), () =>
      rnQuickFilter(listview.doctype, field, value),
    );
  });
};

const operationalViews = {
  "RundiNova Decision": {
    add_fields: ["decision_date", "decision_type", "project", "decision_owner", "follow_up_date", "status", "action_task"],
    get_indicator: rnStatus({
      Open: ["À décider", "red"],
      "In Progress": ["En suivi", "orange"],
      Completed: ["Clôturée", "green"],
      Cancelled: ["Annulée", "darkgrey"],
    }),
    formatters: {
      follow_up_date(value) {
        return value ? `<span class="text-muted"><i class="fa fa-calendar"></i> ${frappe.format(value, { fieldtype: "Date" })}</span>` : '<span class="text-muted">Sans échéance</span>';
      },
    },
    onload(listview) {
      rnAddButtons(listview, "__rn_decision_filters", [
        ["Décisions ouvertes", "status", "Open"],
        ["En suivi", "status", "In Progress"],
      ]);
    },
  },
  "RundiNova Expense": {
    add_fields: ["expense_date", "category", "amount", "project", "paid_by", "payment_method", "status", "approved_by"],
    get_indicator: rnStatus({
      Draft: ["Brouillon", "gray"],
      Submitted: ["À approuver", "orange"],
      Approved: ["Approuvée", "blue"],
      Paid: ["Payée", "green"],
      Rejected: ["Refusée", "red"],
      Cancelled: ["Annulée", "darkgrey"],
    }),
    formatters: {
      amount(value) {
        return `<strong class="text-primary">${rnMoney(value)}</strong>`;
      },
    },
    onload(listview) {
      rnAddButtons(listview, "__rn_expense_filters", [
        ["À approuver", "status", "Submitted"],
        ["Approuvées", "status", "Approved"],
        ["Payées", "status", "Paid"],
      ]);
    },
  },
  "RundiNova Budget Review": {
    add_fields: ["review_period", "branch", "budget", "planned_amount", "committed_amount", "actual_amount", "variance_amount"],
    formatters: {
      planned_amount(value) {
        return `<span class="text-muted">Prévu ${rnMoney(value)}</span>`;
      },
      actual_amount(value) {
        return `<strong>${rnMoney(value)}</strong>`;
      },
      variance_amount(value) {
        const numeric = Number(value || 0);
        const color = numeric > 0 ? "text-danger" : numeric < 0 ? "text-success" : "text-muted";
        return `<span class="${color}">${numeric > 0 ? "+" : ""}${rnMoney(numeric)}</span>`;
      },
    },
  },
  "RundiNova Cash Account": {
    add_fields: ["account_type", "currency", "account_holder", "current_balance", "opening_date", "status"],
    get_indicator: rnStatus({
      Active: ["Actif", "green"],
      Closed: ["Clôturé", "darkgrey"],
    }),
    formatters: {
      current_balance(value) {
        const amount = Number(value || 0);
        return `<strong class="${amount < 0 ? "text-danger" : "text-success"}">${rnMoney(amount)}</strong>`;
      },
    },
    onload(listview) {
      rnAddButtons(listview, "__rn_account_filters", [["Comptes actifs", "status", "Active"]]);
    },
  },
  "RundiNova Cash Movement": {
    add_fields: ["movement_date", "movement_type", "account", "destination_account", "amount", "category", "project", "status"],
    get_indicator(doc) {
      const statuses = {
        Draft: ["Brouillon", "gray"],
        Submitted: ["Soumis", "orange"],
        Approved: ["Approuvé", "green"],
        Reconciled: ["Rapproché", "blue"],
        Cancelled: ["Annulé", "darkgrey"],
      };
      const [label, color] = statuses[doc.status] || [doc.status || "Brouillon", "gray"];
      return [__(label), color, `status,=,${doc.status || "Draft"}`];
    },
    formatters: {
      status(value) {
        return ({ Draft: __("Brouillon"), Submitted: __("Soumis"), Approved: __("Approuvé"), Reconciled: __("Rapproché"), Cancelled: __("Annulé") }[value] || value || "—");
      },
      amount(value, df, doc) {
        const color = doc.movement_type === "Income" ? "text-success" : doc.movement_type === "Expense" ? "text-danger" : "text-primary";
        const sign = doc.movement_type === "Income" ? "+" : doc.movement_type === "Expense" ? "−" : "↔ ";
        return `<strong class="${color}">${sign}${rnMoney(value)}</strong>`;
      },
    },
    onload(listview) {
      rnAddButtons(listview, "__rn_movement_filters", [
        ["Entrées", "movement_type", "Income"],
        ["Sorties", "movement_type", "Expense"],
        ["Transferts", "movement_type", "Transfer"],
      ]);
    },
  },
};

Object.entries(operationalViews).forEach(([doctype, settings]) => {
  const previous = frappe.listview_settings[doctype] || {};
  const previousOnload = previous.onload;
  frappe.listview_settings[doctype] = {
    ...previous,
    ...settings,
    hide_name_column: true,
    add_fields: [...new Set([...(previous.add_fields || []), ...(settings.add_fields || [])])],
    formatters: { ...(previous.formatters || {}), ...(settings.formatters || {}) },
    onload(listview) {
      previousOnload?.(listview);
      settings.onload?.(listview);
    },
  };
});
