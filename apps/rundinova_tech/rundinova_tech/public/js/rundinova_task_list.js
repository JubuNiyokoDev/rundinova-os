const previousTaskListSettings = frappe.listview_settings["Task"] || {};
const previousOnload = previousTaskListSettings.onload;

frappe.listview_settings["Task"] = {
  ...previousTaskListSettings,
  add_fields: [
    ...new Set([
      ...(previousTaskListSettings.add_fields || []),
      "status",
      "rundinova_test_result",
      "rundinova_last_updated_by_name",
      "rundinova_test_summary",
    ]),
  ],
  filters: [],
  get_indicator(doc) {
    const indicators = {
      Open: [__("À faire"), "gray"],
      Working: [__("En cours"), "orange"],
      "Pending Review": [__("Revue en attente"), "blue"],
      Overdue: [__("En retard"), "red"],
      Template: [__("Modèle"), "lightblue"],
      Completed: [__("Terminé"), "green"],
      Cancelled: [__("Annulé"), "darkgrey"],
    };
    const [label, color] = indicators[doc.status] || [doc.status || __("À faire"), "gray"];
    return [label, color, `status,=,${doc.status || "Open"}`];
  },
  onload(listview) {
    previousOnload?.(listview);
    const filters = listview.filter_area?.get_filters?.() || [];
    const default_open_filter =
      filters.length === 1 &&
      filters[0][1] === "status" &&
      filters[0][2] === "=" &&
      filters[0][3] === "Open";
    if (default_open_filter) {
      listview.filter_area.clear();
    }
    if (listview.page.__rundinova_all_statuses_button) return;
    listview.page.__rundinova_all_statuses_button = true;
    listview.page.add_inner_button(__("Tous les statuts"), () => {
      frappe.set_route("List", "Task");
    });
  },
};
