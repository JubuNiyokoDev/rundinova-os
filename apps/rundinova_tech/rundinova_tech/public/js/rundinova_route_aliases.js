// Preserve old and translated entry points while keeping one canonical route.
const rundinova_route_aliases = {
  "configuration-rundinova": "/desk/rundinova-setup",
  "rundinova-équipe": "/desk/rundinova-tech",
  "rundinova-equipe": "/desk/rundinova-tech",
  "rundinova-team": "/desk/rundinova-tech",
  "developpement-&-livraison": "/desk/workspace/RundiNova%20Developer",
  "developpement-livraison": "/desk/workspace/RundiNova%20Developer",
  "communication-&-crm": "/desk/workspace/RundiNova%20Communications",
  "communication-crm": "/desk/workspace/RundiNova%20Communications",
  "communaute-&-impact": "/desk/workspace/RundiNova%20Community",
  "communaute-impact": "/desk/workspace/RundiNova%20Community",
  "projets-&-livraison": "/desk/workspace/RundiNova%20Delivery",
  "projets-livraison": "/desk/workspace/RundiNova%20Delivery",
  "ecosysteme-&-partenariats": "/desk/workspace/RundiNova%20Ecosystem",
  "ecosysteme-partenariats": "/desk/workspace/RundiNova%20Ecosystem",
};

function rundinova_normalize_alias(value) {
  return decodeURIComponent(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

const rundinova_current_route = rundinova_normalize_alias(
  window.location.pathname.split("/").filter(Boolean).pop() || "",
);
const rundinova_current_destination =
  rundinova_route_aliases[rundinova_current_route];
if (rundinova_current_destination) {
  window.location.replace(rundinova_current_destination);
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
    const alias = route.length === 1 ? rundinova_normalize_alias(route[0]) : "";
    if (alias && rundinova_route_aliases[alias]) {
      window.location.replace(rundinova_route_aliases[alias]);
    }
  });
}
