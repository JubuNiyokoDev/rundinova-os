// Preserve old and translated entry points while keeping one canonical route.
const rundinova_route_aliases = {
  "configuration-rundinova": "/desk/rundinova-setup",
  "rundinova-équipe": "/desk/rundinova-tech",
  "rundinova-equipe": "/desk/rundinova-tech",
  "rundinova-team": "/desk/rundinova-tech",
};

const rundinova_current_route = decodeURIComponent(
  window.location.pathname.split("/").filter(Boolean).pop() || "",
);
if (rundinova_route_aliases[rundinova_current_route]) {
  window.location.replace(rundinova_route_aliases[rundinova_current_route]);
}

for (const [alias, destination] of Object.entries(rundinova_route_aliases)) {
  frappe.pages[alias] = frappe.pages[alias] || {};
  frappe.pages[alias].on_page_load = function () {
    window.location.replace(destination);
  };
}

// Catch legacy routes before Desk renders a missing Page.
if (frappe.router && !window.rundinova_route_alias_listener) {
  window.rundinova_route_alias_listener = true;
  frappe.router.on("change", () => {
    const route = frappe.get_route?.() || [];
    if (route.length === 1 && rundinova_route_aliases[route[0]]) {
      window.location.replace(rundinova_route_aliases[route[0]]);
    }
  });
}
