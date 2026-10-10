// Frappe's friendly /desk/<workspace-slug> route needs the matching
// Workspace Sidebar title restored after route changes.
function use_workspace_sidebar_for_workspace_route() {
  if (!frappe.app?.sidebar) return;

  const route = frappe.get_route();
  const workspace = frappe.workspaces?.[route[0]];
  const assigned = frappe.boot?.user?.default_workspace;
  const assigned_name =
    typeof assigned === "string" ? assigned : assigned?.name;
  if (!route.length) {
    frappe.set_route(`workspace/${assigned_name || "RundiNova Tech"}`);
    return;
  }
  const workspace_route = route.length === 1 && workspace;
  const dashboard_route =
    route[0] === "dashboard-view" ||
    route[0] === "dashboard" ||
    route[0] === "rundinova-setup";
  if (!workspace_route && !dashboard_route) return;

  const sidebar_workspace = workspace_route
    ? workspace?.title || workspace?.name
    : assigned_name;
  const title = sidebar_workspace || "RundiNova Tech";
  if (!title || !frappe.boot.workspace_sidebar_item?.[title.toLowerCase()])
    return;

  if (frappe.app.sidebar.sidebar_title !== title) {
    frappe.app.sidebar.setup(title);
  }
}

if (frappe.router) {
  frappe.router.on("change", use_workspace_sidebar_for_workspace_route);
}
$(document).on("page-change", use_workspace_sidebar_for_workspace_route);
