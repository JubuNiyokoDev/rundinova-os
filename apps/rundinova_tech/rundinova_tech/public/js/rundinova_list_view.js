// Human-friendly list views: document keys stay internal and links use titles.
frappe.listview_settings = frappe.listview_settings || {};
[
  "RundiNova Decision",
  "RundiNova Repository",
  "RundiNova Growth Opportunity",
  "RundiNova KPI Definition",
  "RundiNova Goal",
  "RundiNova KPI Snapshot",
  "RundiNova Partnership",
  "RundiNova Food Progress",
  "RundiNova Food Budget",
  "RundiNova Risk",
  "RundiNova Office",
  "RundiNova Asset",
  "RundiNova Community Impact",
  "RundiNova Cash Movement",
  "RundiNova Food Expense",
  "RundiNova Budget Review",
  "RundiNova Expense",
  "RundiNova Cash Account",
  "RundiNova Document",
].forEach((doctype) => {
  frappe.listview_settings[doctype] = {
    ...(frappe.listview_settings[doctype] || {}),
    hide_name_column: true,
  };
});
