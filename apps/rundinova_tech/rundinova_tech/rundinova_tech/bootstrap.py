"""Idempotent bootstrap for the RundiNova Tech installation.

Repairs / completes a headless install so that:

1. the ERPNext "Transit" warehouse type exists (normally created by the
   setup wizard, which never runs in headless installs);
2. the RundiNova Tech company exists with its default warehouses, cost
   center, departments and chart of accounts;
3. the rundinova_tech seed (roles, permissions, dashboards) has run;
4. ERPNext modules that a 5-person dev hub does not use (manufacturing,
   quality, subcontracting, support, website) are hidden from the Desk
   sidebar so end users never see them.

Safe to re-run: every step checks current state first.

Run with:

    bench --site <site> execute rundinova_tech.rundinova_tech.bootstrap.run
"""

import frappe

from rundinova_tech.rundinova_tech.setup import seed

COMPANY_NAME = "RundiNova Tech"
COMPANY_ABBR = "RNT"

# Founding team of the hub.  Roles mirror the chart in
# docs/rundinova/06-roles-and-responsibilities.md.  Everyone also gets
# RundiNova Team Member because everyone develops.
TEAM_USERS = [
    {
        "email": "joffre.niyondiko@rundinova.com",
        "first_name": "Joffre",
        "last_name": "Niyondiko",
        "designation": "Co-Founder & CEO",
        "roles": ["RundiNova Director", "RundiNova Finance Manager", "RundiNova Team Member"],
    },
    {
        "email": "janvier.ndabubaha@rundinova.com",
        "first_name": "Janvier",
        "last_name": "Ndabubaha",
        "designation": "Co-Founder & COO",
        "roles": ["RundiNova Operations", "RundiNova Team Member"],
    },
    {
        "email": "franck.maniranyibutse@rundinova.com",
        "first_name": "Franck",
        "last_name": "Maniranyibutse",
        "designation": "Head of Engineering",
        "roles": ["RundiNova Project Lead", "RundiNova Team Member"],
    },
    {
        "email": "elvis.irambona@rundinova.com",
        "first_name": "Elvis",
        "last_name": "Irambona",
        "designation": "Head of Communications",
        "roles": ["RundiNova Communications", "RundiNova Team Member"],
    },
    {
        "email": "mandela.fanuel-kasumba@rundinova.com",
        "first_name": "Fanuel",
        "last_name": "Kasumba Mandela",
        "designation": "Head of People & Culture",
        "roles": ["RundiNova People & Culture", "RundiNova Team Member"],
    },
]

# ERPNext workspaces behind modules the hub does not use.  Hiding them
# removes the modules from the Desk sidebar for every user; the doctypes
# stay installed but unreachable from the UI.
UNUSED_WORKSPACES = [
    "Manufacturing",
    "Quality",
    "Subcontracting",
    "Support",
    "Website",
]


def run():
    """Bootstrap entry point; returns a small status report."""
    report = {}
    report["warehouse_type"] = ensure_transit_warehouse_type()
    report["company"] = ensure_company()
    report["seed"] = run_seed()
    report["team_users"] = ensure_team_users()
    report["hidden_workspaces"] = hide_unused_workspaces()
    frappe.db.commit()
    report["checks"] = current_state()
    return report


def ensure_team_users(temporary_password=None):
    """Create the five founding-team accounts once, with their roles.

    Idempotent: existing users are left untouched except for missing
    RundiNova roles, which are added.  A shared temporary password is set
    only at creation; every member changes it on first use.

    ``designation`` in TEAM_USERS is informational only: the Frappe v16
    User doctype has no designation field (titles live on the HRMS
    Employee record); official titles are documented in
    docs/rundinova/06-roles-and-responsibilities.md.
    """
    results = {}
    password = temporary_password or "RundiNova@2026"
    for spec in TEAM_USERS:
        email = spec["email"]
        if frappe.db.exists("User", email):
            user = frappe.get_doc("User", email)
        else:
            user = frappe.new_doc("User")
            user.update({
                "email": email,
                "first_name": spec["first_name"],
                "last_name": spec["last_name"],
                "enabled": 1,
                "user_type": "System User",
                "send_welcome_email": 0,
                "new_password": password,
            })
            user.insert(ignore_permissions=True)
            results[email] = "created"
        existing_roles = {row.role for row in user.roles}
        added = False
        for role in spec["roles"]:
            if role in existing_roles:
                continue
            user.append("roles", {"role": role})
            added = True
        if added:
            user.save(ignore_permissions=True)
            results.setdefault(email, "updated")
        else:
            results.setdefault(email, "already-exists")
        frappe.db.commit()
    return results


def hide_unused_workspaces():
    """Hide the workspaces of modules the hub does not use.

    Idempotent: workspaces already hidden are left untouched.  Returns the
    list of newly hidden workspaces, or "already-hidden" when nothing changed.
    """
    newly_hidden = []
    for name in UNUSED_WORKSPACES:
        if not frappe.db.exists("Workspace", name):
            continue
        if not frappe.db.get_value("Workspace", name, "is_hidden"):
            frappe.db.set_value("Workspace", name, "is_hidden", 1)
            newly_hidden.append(name)
    frappe.db.commit()
    return newly_hidden or "already-hidden"


def ensure_transit_warehouse_type():
    if frappe.db.exists("Warehouse Type", "Transit"):
        return "already-exists"
    doc = frappe.get_doc(
        {"doctype": "Warehouse Type", "name": "Transit", "description": "Goods in transit"}
    )
    doc.flags.name_set = True
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return "created"


def ensure_company():
    if frappe.db.exists("Company", COMPANY_NAME):
        # Re-save so ERPNext completes any missing defaults
        # (warehouses, cost center, default accounts, ...).
        company = frappe.get_doc("Company", COMPANY_NAME)
        company.flags.ignore_mandatory = True
        company.save(ignore_permissions=True)
        frappe.db.commit()
        return "already-exists"

    company = frappe.new_doc("Company")
    company.company_name = COMPANY_NAME
    company.abbr = COMPANY_ABBR
    company.country = "Burundi"
    company.default_currency = "BIF"
    company.enable_perpetual_inventory = 1
    company.flags.ignore_mandatory = True
    company.insert(ignore_permissions=True)
    frappe.db.commit()
    return "created"


def run_seed():
    result = seed()
    frappe.db.commit()
    return result


def current_state():
    return {
        "companies": frappe.db.count("Company"),
        "warehouses": frappe.db.count("Warehouse", {"company": COMPANY_NAME}),
        "cost_centers": frappe.db.count("Cost Center", {"company": COMPANY_NAME}),
        "accounts": frappe.db.count("Account", {"company": COMPANY_NAME}),
        "departments": frappe.db.count("Department", {"company": COMPANY_NAME}),
        "rundinova_roles": frappe.db.count("Role", {"role_name": ["like", "RundiNova %"]}),
    }


def permission_report():
    """Summarise the effective DocPerm matrix of RundiNova doctypes per role.

    Read-only verification helper:

        bench --site <site> execute rundinova_tech.rundinova_tech.bootstrap.permission_report
    """
    doctypes = [
        d.name
        for d in frappe.get_all(
            "DocType", filters={"module": "RundiNova Tech", "istable": 0}, fields=["name"]
        )
    ]
    by_role = {}
    for dt in doctypes:
        perms = frappe.get_all(
            "DocPerm", filters={"parent": dt}, fields=["role", "read", "write"]
        )
        for p in perms:
            entry = by_role.setdefault(p.role, {"write": [], "read_only": []})
            if p.write:
                entry["write"].append(dt)
            elif p.read:
                entry["read_only"].append(dt)
    return by_role
