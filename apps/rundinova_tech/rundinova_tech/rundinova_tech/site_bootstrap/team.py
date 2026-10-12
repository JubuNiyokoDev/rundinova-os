"""Founding team account provisioning."""

import frappe

LEGACY_TEAM_LOGIN_REPLACEMENTS = {
    "1.ndabubahajanvier@gmail.com": "ndabubahajanvier@gmail.com",
}

TEAM_USERS = [
    {
        "email": "joffre.niyondiko@kit-hub.com",
        "first_name": "Joffre",
        "last_name": "Niyondiko",
        "employee_name": "NIYONDIKO Joffre",
        "roles": [
            "RundiNova Director",
            "RundiNova Finance Manager",
            "RundiNova Project Lead",
            "RundiNova Team Member",
        ],
    },
    {
        "email": "ndabubahajanvier@gmail.com",
        "first_name": "Janvier",
        "last_name": "Ndabubaha",
        "employee_name": "NDABUBAHA Janvier",
        "roles": ["Employee", "RundiNova Ecosystem Lead", "RundiNova Team Member"],
    },
    {
        "email": "maniranyibutsef@gmail.com",
        "first_name": "Franck",
        "last_name": "Maniranyibutse",
        "employee_name": "MANIRANYIBUTSE Franck",
        "roles": ["RundiNova Growth Lead", "RundiNova Team Member"],
    },
    {
        "email": "presira857@gmail.com",
        "first_name": "Elvis",
        "last_name": "Irambona",
        "employee_name": "IRAMBONA Elvis",
        "roles": ["RundiNova Communications", "RundiNova Team Member"],
    },
    {
        "email": "mandela.fanuel.1@gmail.com",
        "first_name": "Fanuel",
        "last_name": "Kasumba Mandela",
        "employee_name": "KASUMBA Fanuel",
        "roles": ["RundiNova Community Relations", "RundiNova Team Member"],
    },
    {
        "email": "housekeeping@rundinova.com",
        "first_name": "Housekeeping",
        "last_name": "",
        "employee_name": "Housekeeping",
        "roles": ["Employee", "RundiNova Team Member"],
    },
]


def ensure_team_users(temporary_password=None):
    """Provision the real team identities and keep their role assignments exact."""
    results = {}
    for spec in TEAM_USERS:
        email = spec["email"]
        user_changed = False
        if frappe.db.exists("User", email):
            user = frappe.get_doc("User", email)
            if user.user_type != "System User":
                user.user_type = "System User"
                user_changed = True
            if not user.default_workspace:
                user.default_workspace = "RundiNova Tech"
                user_changed = True
        else:
            user = frappe.new_doc("User")
            user_data = {
                "email": email,
                "first_name": spec["first_name"],
                "last_name": spec["last_name"],
                "enabled": 1,
                "user_type": "System User",
                "default_workspace": "RundiNova Tech",
                "send_welcome_email": 0,
            }
            if temporary_password:
                user_data["new_password"] = temporary_password
            user.update(user_data)
            user.insert(ignore_permissions=True)
            results[email] = "created"
        existing_roles = {row.role for row in user.roles}
        desired_roles = set(spec["roles"])
        stale_roles = {
            row.role
            for row in user.roles
            if row.role.startswith("RundiNova ") and row.role not in desired_roles
        }
        if stale_roles:
            user.set(
                "roles",
                [row for row in user.roles if row.role not in stale_roles],
            )
        added = bool(stale_roles) or user_changed
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
        employee_name = spec.get("employee_name")
        if employee_name:
            matches = frappe.get_all(
                "Employee",
                filters={"employee_name": employee_name},
                fields=["name", "user_id"],
                limit_page_length=2,
            )
            if len(matches) == 1:
                employee = matches[0]
                previous_email = employee.user_id
                if (
                    previous_email in LEGACY_TEAM_LOGIN_REPLACEMENTS
                    and LEGACY_TEAM_LOGIN_REPLACEMENTS[previous_email] == email
                ):
                    if frappe.db.exists("User", previous_email):
                        old_user = frappe.get_doc("User", previous_email)
                        if old_user.enabled:
                            old_user.enabled = 0
                            old_user.save(ignore_permissions=True)
                    frappe.db.set_value("Employee", employee.name, "user_id", email)
                elif not previous_email:
                    frappe.db.set_value("Employee", employee.name, "user_id", email)
                if "RundiNova Director" not in desired_roles and not frappe.db.exists(
                    "User Permission",
                    {"user": email, "allow": "Employee", "for_value": employee.name},
                ):
                    frappe.get_doc(
                        {
                            "doctype": "User Permission",
                            "user": email,
                            "allow": "Employee",
                            "for_value": employee.name,
                            "apply_to_all_doctypes": 1,
                        }
                    ).insert(ignore_permissions=True)
        frappe.db.commit()
    from ..provisioning.permissions import ensure_crm_app_access_roles

    ensure_crm_app_access_roles()
    frappe.db.commit()
    return results
