frappe.listview_settings = frappe.listview_settings || {};
const previousEmployeeListSettings = frappe.listview_settings.Employee || {};
const previousEmployeeOnload = previousEmployeeListSettings.onload;

frappe.listview_settings.Employee = {
  ...previousEmployeeListSettings,
  hide_name_column: true,
  add_fields: [
    ...new Set([
      ...(previousEmployeeListSettings.add_fields || []),
      "employee_name",
      "designation",
      "department",
      "branch",
      "status",
      "user_id",
      "image",
    ]),
  ],
  get_indicator(doc) {
    const indicators = {
      Active: [__("Actif(ve)"), "green"],
      Inactive: [__("Inactif(ve)"), "darkgrey"],
      Left: [__("Sorti(e)"), "red"],
      Suspended: [__("Suspendu(e)"), "orange"],
    };
    return indicators[doc.status] || [doc.status || __("—"), "gray"];
  },
  onload(listview) {
    previousEmployeeOnload?.(listview);
    if (listview.page.__rn_employee_filters) return;
    listview.page.__rn_employee_filters = true;
    listview.page.add_inner_button(__("Équipe active"), () => {
      frappe.route_options = { status: "Active" };
      frappe.set_route("List", "Employee");
    });
  },
};
