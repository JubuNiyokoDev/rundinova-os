import frappe

from ..access_control import (
    ROLES,
    get_custom_doctype_permissions,
    get_standard_doctype_permissions,
)


def ensure_rundinova_permissions():
    """Persist the documented RundiNova role policy across migrations.

    Writes DocPerm rows directly instead of saving the parent DocType,
    because Frappe protects standard-doctype metadata when developer mode
    is disabled.  Idempotent: existing rows are updated in place.
    """
    custom_policy = get_custom_doctype_permissions()
    standard_policy = get_standard_doctype_permissions()
    tables = set(
        frappe.get_all(
            "DocType", filters={"module": "RundiNova Tech", "istable": 1}, pluck="name"
        )
    )

    def upsert_permission(doctype, role, values, custom=False):
        table = "Custom DocPerm" if custom else "DocPerm"
        filters = {"parent": doctype, "role": role, "permlevel": 0}
        if not custom:
            filters["parenttype"] = "DocType"
        existing = frappe.db.get_value(table, filters, "name")
        if existing:
            frappe.db.set_value(table, existing, values)
        else:
            row = {
                "doctype": table,
                "parent": doctype,
                "role": role,
                "permlevel": 0,
                **values,
            }
            if not custom:
                row.update(parenttype="DocType", parentfield="permissions")
            frappe.get_doc(row).insert(ignore_permissions=True)

    # Replace only this app's grants; preserve other apps' custom rules.
    module_doctypes = frappe.get_all(
        "DocType", filters={"module": "RundiNova Tech"}, pluck="name"
    )
    for doctype in module_doctypes:
        frappe.db.delete(
            "Custom DocPerm", {"parent": doctype, "role": ["in", list(ROLES)]}
        )
        frappe.db.delete(
            "DocPerm",
            {"parent": doctype, "parenttype": "DocType", "role": ["in", list(ROLES)]},
        )

    for (doctype, role), values in custom_policy.items():
        if frappe.db.exists("DocType", doctype):
            upsert_permission(doctype, role, values, custom=doctype not in tables)

    # Child table rows inherit their parent's role policy.
    for child in tables:
        parents = frappe.get_all(
            "DocField",
            filters={
                "fieldtype": "Table",
                "options": child,
                "parent": ["in", list(module_doctypes)],
            },
            pluck="parent",
        )
        for parent in parents:
            for role in ROLES:
                parent_policy = custom_policy.get((parent, role))
                if parent_policy:
                    upsert_permission(child, role, parent_policy)

    # Custom DocPerm replaces the built-in matrix, so preserve explicit
    # non-RundiNova application roles while removing generic grants such as
    # Desk User/All from sensitive records.
    standard_doctypes = {doctype for doctype, _ in standard_policy}
    for doctype in standard_doctypes:
        if not frappe.db.exists("DocType", doctype):
            continue
        # Remove stale app and generic grants before installing the explicit
        # matrix; otherwise Desk User/All can bypass the intended boundary.
        frappe.db.delete(
            "Custom DocPerm",
            {
                "parent": doctype,
                "role": ["in", [*ROLES, "All", "Guest", "Desk User"]],
            },
        )
        frappe.db.delete(
            "DocPerm",
            {"parent": doctype, "parenttype": "DocType", "role": ["in", list(ROLES)]},
        )
    for (doctype, role), values in standard_policy.items():
        if frappe.db.exists("DocType", doctype):
            upsert_permission(doctype, role, values, custom=True)
    for doctype in standard_doctypes:
        if not frappe.db.exists("DocType", doctype):
            continue
        custom_roles = frappe.get_all(
            "Custom DocPerm", filters={"parent": doctype}, pluck="role"
        )
        if custom_roles:
            for role in frappe.get_all(
                "DocPerm",
                filters={
                    "parent": doctype,
                    "parenttype": "DocType",
                    "role": ["not in", custom_roles],
                },
                fields=[
                    "role",
                    "read",
                    "write",
                    "create",
                    "delete",
                    "submit",
                    "cancel",
                    "amend",
                    "report",
                    "export",
                    "share",
                    "print",
                    "email",
                    "if_owner",
                ],
            ):
                if role.role in ("All", "Guest", "Desk User") or frappe.db.exists(
                    "Custom DocPerm",
                    {"parent": doctype, "role": role.role, "permlevel": 0},
                ):
                    continue
                upsert_permission(
                    doctype,
                    role.role,
                    {
                        key: role.get(key)
                        for key in (
                            "read",
                            "write",
                            "create",
                            "delete",
                            "submit",
                            "cancel",
                            "amend",
                            "report",
                            "export",
                            "share",
                            "print",
                            "email",
                            "if_owner",
                        )
                    },
                    custom=True,
                )

    frappe.clear_cache()
    ensure_director_employee_access()
    return {"custom": custom_policy, "standard": standard_policy}


def ensure_director_employee_access():
    """Directors can read the team directory; other members keep self scope."""
    directors = frappe.get_all(
        "Has Role",
        filters={"role": "RundiNova Director"},
        pluck="parent",
    )
    if not directors:
        return
    frappe.db.delete(
        "User Permission",
        {
            "user": ["in", directors],
            "allow": "Employee",
        },
    )
    frappe.clear_cache()


def ensure_crm_app_access_roles():
    """Grant the built-in CRM entry role to the RundiNova roles using CRM.

    Frappe CRM checks for Sales User/Sales Manager before it renders its app.
    Data access remains governed by the explicit RundiNova permissions matrix.
    """
    if not frappe.db.exists("Role", "Sales User"):
        return []

    updated = []
    for user in frappe.get_all(
        "User", filters={"user_type": "System User"}, pluck="name"
    ):
        roles = set(frappe.get_roles(user))
        if not roles.intersection(
            {
                "RundiNova Director",
                "RundiNova Communications",
                "RundiNova Ecosystem Lead",
                "RundiNova Growth Lead",
            }
        ):
            continue
        if "Sales User" in roles:
            continue
        user_doc = frappe.get_doc("User", user)
        user_doc.append("roles", {"role": "Sales User"})
        user_doc.save(ignore_permissions=True)
        updated.append(user)
    return updated
