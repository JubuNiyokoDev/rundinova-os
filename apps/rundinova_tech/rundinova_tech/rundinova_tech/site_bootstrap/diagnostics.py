"""Read-only reports for bootstrap and access troubleshooting."""

import frappe

from .company import COMPANY_NAME
from .team import TEAM_USERS
def current_state():
    return {
        "companies": frappe.db.count("Company"),
        "warehouses": frappe.db.count("Warehouse", {"company": COMPANY_NAME}),
        "cost_centers": frappe.db.count("Cost Center", {"company": COMPANY_NAME}),
        "accounts": frappe.db.count("Account", {"company": COMPANY_NAME}),
        "departments": frappe.db.count("Department", {"company": COMPANY_NAME}),
        "rundinova_roles": frappe.db.count("Role", {"role_name": ["like", "RundiNova %"]}),
    }


def check_sidebar():
    """Report the Desk sidebar visible to each founding member."""
    from frappe.desk.desktop import get_workspaces

    results = {}
    for spec in TEAM_USERS + [{"email": "Administrator"}]:
        email = spec["email"]
        try:
            frappe.set_user(email)
            data = get_workspaces()
            titles = [page.title for page in data.get("pages") or []]
            results[email] = {
                "titles": titles,
                "count": len(titles),
                "has_workspace_manager": "Workspace Manager" in (frappe.get_roles() or []),
            }
        except Exception as exc:
            results[email] = "ERROR: %s" % repr(exc)[:80]
    frappe.set_user("Administrator")
    return results


def check_page_access(page_name="rundinova-onboarding"):
    """Check if each founding member can load a Desk page."""
    from frappe.desk.desk_page import get

    results = {}
    for spec in TEAM_USERS + [{"email": "Administrator"}]:
        email = spec["email"]
        try:
            frappe.set_user(email)
            docs = get(page_name)
            results[email] = "OK (script=%d)" % len(docs.get("script") or "")
        except frappe.PermissionError:
            results[email] = "DENIED"
        except Exception as exc:
            results[email] = "ERROR: %s" % repr(exc)[:80]
    frappe.set_user("Administrator")
    return results


def permission_report():
    """Summarize the effective DocPerm matrix for RundiNova doctypes."""
    doctypes = [
        doc.name
        for doc in frappe.get_all(
            "DocType", filters={"module": "RundiNova Tech", "istable": 0}, fields=["name"]
        )
    ]
    by_role = {}
    for doctype in doctypes:
        permissions = frappe.get_all(
            "DocPerm", filters={"parent": doctype}, fields=["role", "read", "write"]
        )
        for permission in permissions:
            entry = by_role.setdefault(permission.role, {"write": [], "read_only": []})
            if permission.write:
                entry["write"].append(doctype)
            elif permission.read:
                entry["read_only"].append(doctype)
    return by_role
