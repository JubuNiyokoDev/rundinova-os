import frappe


def ensure_rundinova_roles():
    """Create only named roles; users and permissions remain administrator-controlled."""
    role_names = [
        "RundiNova Director",
        "RundiNova Finance Manager",
        "RundiNova Operations",
        "RundiNova Project Lead",
        "RundiNova Ecosystem Lead",
        "RundiNova Growth Lead",
        "RundiNova Community Relations",
        "RundiNova Team Member",
        "RundiNova Communications",
        "RundiNova People & Culture",
    ]
    created = []
    for role_name in role_names:
        if frappe.db.exists("Role", role_name):
            continue
        frappe.get_doc(
            {
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1,
                "is_custom": 1,
            }
        ).insert(ignore_permissions=True)
        created.append(role_name)
    frappe.db.commit()
    return created
