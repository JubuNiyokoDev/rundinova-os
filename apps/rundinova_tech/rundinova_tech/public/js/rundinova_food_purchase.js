// One short purchase flow shared by budget lines, food progress, and list rows.
frappe.listview_settings = frappe.listview_settings || {};
window.rundinova_open_food_purchase = async function ({
  budget,
  item,
  progress,
  frm,
} = {}) {
  if (progress && (!budget || !item)) {
    const row = await frappe.db.get_doc("RundiNova Food Progress", progress);
    budget = budget || row.budget;
    item = item || row.item;
  }
  if (!budget && frm?.doctype === "RundiNova Food Budget")
    budget = frm.doc.name;

  let budget_doc =
    frm?.doctype === "RundiNova Food Budget" && frm.doc.name === budget
      ? frm.doc
      : budget
        ? await frappe.db.get_doc("RundiNova Food Budget", budget)
        : null;
  let budget_lines = budget_doc?.items || [];
  let allowed_items = budget_lines.map((line) => line.item).filter(Boolean);
  if (budget && !allowed_items.length) {
    frappe.msgprint(__("Ce budget ne contient aucune ligne d’article."));
    return;
  }
  if (item && allowed_items.length && !allowed_items.includes(item)) {
    frappe.msgprint(
      __("Cet article ne figure pas dans le budget sélectionné."),
    );
    return;
  }

  const privileged = [
    "RundiNova Director",
    "RundiNova Finance Manager",
    "RundiNova Operations",
  ].some((role) => frappe.user.has_role(role));
  const fields = [];
  if (!budget)
    fields.push({
      fieldtype: "Link",
      fieldname: "budget",
      label: __("Budget alimentaire"),
      options: "RundiNova Food Budget",
      reqd: 1,
      async onchange() {
        const selected = dialog.get_value("budget");
        budget_doc = selected
          ? await frappe.db.get_doc("RundiNova Food Budget", selected)
          : null;
        budget_lines = budget_doc?.items || [];
        allowed_items = budget_lines.map((line) => line.item).filter(Boolean);
        if (item) {
          if (selected && !allowed_items.includes(item)) {
            budget_doc = null;
            budget_lines = [];
            allowed_items = [];
            dialog.set_value("budget", "");
            frappe.msgprint(
              __("Cet article ne figure pas dans le budget sélectionné."),
            );
            return;
          }
          dialog.set_value(
            "unit",
            budget_lines.find((line) => line.item === item)?.unit || "",
          );
        } else {
          dialog.set_value("items", []);
          dialog.get_field("items")?.grid?.refresh();
        }
        if (!allowed_items.length && selected) {
          frappe.msgprint(__("Ce budget ne contient aucune ligne d’article."));
        }
      },
    });
  if (item) {
    fields.push(
      {
        fieldtype: "Link",
        fieldname: "item",
        label: __("Article"),
        options: "Item",
        reqd: 1,
        read_only: true,
        default: item,
      },
      {
        fieldtype: "Float",
        fieldname: "quantity",
        label: __("Quantité achetée"),
        default: 1,
        reqd: 1,
      },
      {
        fieldtype: "Data",
        fieldname: "unit",
        label: __("Unité"),
        read_only: 1,
        default: budget_lines.find((line) => line.item === item)?.unit || "",
      },
      {
        fieldtype: "Currency",
        fieldname: "amount",
        label: __("Prix unitaire (FBu)"),
        reqd: 1,
      },
    );
  } else {
    fields.push({
      fieldtype: "Table",
      fieldname: "items",
      label: __("Articles achetés"),
      options: "RundiNova Food Purchase Line",
      reqd: 1,
      in_place_edit: true,
      data: [],
      fields: [
        {
          fieldtype: "Link",
          fieldname: "item",
          label: __("Article"),
          options: "Item",
          reqd: 1,
          in_list_view: 1,
          get_query: () => ({ filters: { name: ["in", allowed_items] } }),
        },
        {
          fieldtype: "Float",
          fieldname: "quantity",
          label: __("Quantité"),
          default: 1,
          reqd: 1,
          in_list_view: 1,
        },
        {
          fieldtype: "Currency",
          fieldname: "amount",
          label: __("Prix unitaire (FBu)"),
          reqd: 1,
          in_list_view: 1,
        },
      ],
    });
  }
  fields.push(
    {
      fieldtype: "Date",
      fieldname: "expense_date",
      label: __("Date d’achat"),
      default: frappe.datetime.get_today(),
      reqd: 1,
    },
    {
      fieldtype: "Select",
      fieldname: "payment_method",
      label: __("Mode de paiement"),
      options: "Cash\nMobile Money\nBank Transfer\nCard\nOther",
      default: "Cash",
      reqd: 1,
    },
  );
  if (privileged)
    fields.push({
      fieldtype: "Link",
      fieldname: "supplier",
      label: __("Fournisseur (facultatif)"),
      options: "Supplier",
    });
  fields.push(
    {
      fieldtype: "Attach",
      fieldname: "receipt",
      label: __("Reçu (facultatif)"),
    },
    {
      fieldtype: "Small Text",
      fieldname: "notes",
      label: __("Note (facultatif)"),
    },
  );

  const dialog = new frappe.ui.Dialog({
    title: item ? __("Nouvel achat alimentaire") : __("Nouvel achat au marché"),
    fields,
    primary_action_label: item
      ? __("Enregistrer l’achat")
      : __("Enregistrer les achats"),
    primary_action: async (values) => {
      dialog.disable_primary_action();
      try {
        const args = item
          ? {
              ...values,
              budget: budget || values.budget,
              food_progress: progress || undefined,
              unit_price: values.amount,
            }
          : {
              budget: budget || values.budget,
              items: JSON.stringify(
                (values.items || []).map((row) => ({
                  ...row,
                  unit_price: row.amount,
                })),
              ),
              expense_date: values.expense_date,
              payment_method: values.payment_method,
              supplier: values.supplier,
              receipt: values.receipt,
              notes: values.notes,
            };
        const method = `rundinova_tech.rundinova_tech.doctype.rundinova_food_expense.rundinova_food_expense.${item ? "record_food_purchase" : "record_food_purchases"}`;
        const result = await frappe.call({ method, args });
        dialog.hide();
        frappe.show_alert({
          message: __("Achat enregistré. Budget et progression mis à jour."),
          indicator: "green",
        });
        if (frm && !frm.is_new()) await frm.reload_doc();
        if (window.cur_list?.refresh) window.cur_list.refresh();
        return result;
      } catch (error) {
        dialog.enable_primary_action();
        throw error;
      }
    },
  });
  dialog.show();
  if (!item) {
    dialog.set_value("items", [{ quantity: 1 }]);
    dialog.get_field("items")?.grid?.refresh();
  }
};

frappe.ui.form.on("RundiNova Food Budget", {
  refresh(frm) {
    if (!frm.is_new()) {
      frm.add_custom_button(
        __("Enregistrer un achat"),
        () => {
          window.rundinova_open_food_purchase({ budget: frm.doc.name, frm });
        },
        __("Achats"),
      );
    }
  },
});

frappe.ui.form.on("RundiNova Food Progress", {
  refresh(frm) {
    if (!frm.is_new() && frm.doc.budget && frm.doc.item) {
      frm.add_custom_button(
        __("Enregistrer un achat"),
        () => {
          window.rundinova_open_food_purchase({
            budget: frm.doc.budget,
            item: frm.doc.item,
            progress: frm.doc.name,
            frm,
          });
        },
        __("Achats"),
      );
    }
  },
});

frappe.ui.form.on("RundiNova Food Expense", {
  refresh(frm) {
    frm.set_df_property("status", "read_only", 1);
    frm.set_df_property("category", "read_only", 1);
    frm.set_df_property("amount", "read_only", 1);
    updateFoodExpenseTotal(frm);
    if (!frm.is_new()) {
      frm.add_custom_button(
        __("Enregistrer un autre achat"),
        () => {
          window.rundinova_open_food_purchase({
            budget: frm.doc.budget,
            item: frm.doc.item,
          });
        },
        __("Achats"),
      );
    }
  },
  quantity(frm) {
    updateFoodExpenseTotal(frm);
  },
  unit_price(frm) {
    updateFoodExpenseTotal(frm);
  },
});

function updateFoodExpenseTotal(frm) {
  const quantity = Number(frm.doc.quantity || 0);
  const unitPrice = Number(frm.doc.unit_price || 0);
  if (quantity > 0 && unitPrice > 0) {
    frm.set_value("amount", quantity * unitPrice);
  }
}

for (const doctype of ["RundiNova Food Budget", "RundiNova Food Progress"]) {
  frappe.listview_settings[doctype] = {
    ...(frappe.listview_settings[doctype] || {}),
    add_fields:
      doctype === "RundiNova Food Progress"
        ? [
            ...new Set([
              ...(frappe.listview_settings[doctype]?.add_fields || []),
              "budget",
              "item",
            ]),
          ]
        : frappe.listview_settings[doctype]?.add_fields || [],
    button: {
      show(doc) {
        return doctype === "RundiNova Food Budget"
          ? Boolean(doc.name)
          : Boolean(doc.budget && doc.item);
      },
      get_label() {
        return __("Acheter");
      },
      get_description(doc) {
        return __("Enregistrer un achat pour {0}", [doc.title || doc.name]);
      },
      action(doc) {
        window.rundinova_open_food_purchase(
          doctype === "RundiNova Food Budget"
            ? { budget: doc.name }
            : { budget: doc.budget, item: doc.item, progress: doc.name },
        );
      },
    },
  };
}

// Replace the generic New form with the short purchase flow. Users can start
// here or buy directly from the budget/progress list without editing details.
frappe.listview_settings["RundiNova Food Expense"] = {
  ...(frappe.listview_settings["RundiNova Food Expense"] || {}),
  hide_name_column: true,
  onload(listview) {
    listview.page.set_primary_action(__("Enregistrer un achat"), () => {
      window.rundinova_open_food_purchase({});
    });
  },
};

// Start a purchase from the item the user selected; the dialog asks for the
// food budget and keeps this item fixed while validating the budget line.
frappe.listview_settings["Item"] = {
  ...(frappe.listview_settings["Item"] || {}),
  button: {
    ...(frappe.listview_settings["Item"]?.button || {}),
    show(doc) {
      return !doc.disabled;
    },
    get_label() {
      return __("Acheter");
    },
    get_description(doc) {
      return __("Enregistrer un achat de {0}", [doc.item_name || doc.name]);
    },
    action(doc) {
      window.rundinova_open_food_purchase({ item: doc.name });
    },
  },
};

// A budget is a planning and control register, not a generic document list.
// Keep the purchase shortcut above, then foreground its period, ceiling and
// consumption level for finance and operations users.
const previousFoodBudgetListSettings = frappe.listview_settings["RundiNova Food Budget"] || {};
const previousFoodBudgetOnload = previousFoodBudgetListSettings.onload;
frappe.listview_settings["RundiNova Food Budget"] = {
  ...previousFoodBudgetListSettings,
  hide_name_column: true,
  add_fields: [
    ...new Set([
      ...(previousFoodBudgetListSettings.add_fields || []),
      "period_start",
      "period_end",
      "branch",
      "covered_people",
      "approved_ceiling",
      "total_planned_amount",
      "committed_amount",
      "actual_amount",
      "balance_amount",
      "consumed_percent",
    ]),
  ],
  formatters: {
    ...(previousFoodBudgetListSettings.formatters || {}),
    consumed_percent(value) {
      const percent = Math.max(0, Math.min(100, Number(value || 0)));
      const color = percent >= 100 ? "#dc2626" : percent >= 80 ? "#d97706" : "#059669";
      return `<div style="min-width:110px"><div class="text-muted" style="font-size:11px">${percent.toFixed(0)}% consommé</div><div style="height:6px;background:#e5e7eb;border-radius:99px;overflow:hidden"><div style="height:100%;width:${percent}%;background:${color}"></div></div></div>`;
    },
    balance_amount(value) {
      const amount = Number(value || 0);
      return `<strong class="${amount < 0 ? "text-danger" : "text-success"}">${frappe.format(amount, { fieldtype: "Currency", options: "currency" })}</strong>`;
    },
  },
  onload(listview) {
    previousFoodBudgetOnload?.(listview);
    if (listview.page.__rn_food_budget_filters) return;
    listview.page.__rn_food_budget_filters = true;
    listview.page.add_inner_button(__("Budgets dépassés"), () => {
      frappe.route_options = { consumed_percent: [">", 100] };
      frappe.set_route("List", "RundiNova Food Budget");
    });
  },
};
