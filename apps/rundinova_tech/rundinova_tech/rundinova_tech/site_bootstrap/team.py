"""Founding team account provisioning."""

import frappe

TEAM_USERS = [
    {"email": "joffre.niyondiko@rundinova.com", "first_name": "Joffre", "last_name": "Niyondiko", "designation": "Co-Founder & CEO", "roles": ["RundiNova Director", "RundiNova Finance Manager", "RundiNova Team Member"]},
    {"email": "janvier.ndabubaha@rundinova.com", "first_name": "Janvier", "last_name": "Ndabubaha", "designation": "COO", "roles": ["RundiNova Operations", "RundiNova Team Member"]},
    {"email": "franck.maniranyibutse@rundinova.com", "first_name": "Franck", "last_name": "Maniranyibutse", "designation": "Head of Engineering", "roles": ["RundiNova Project Lead", "RundiNova Team Member"]},
    {"email": "elvis.irambona@rundinova.com", "first_name": "Elvis", "last_name": "Irambona", "designation": "Head of Communications", "roles": ["RundiNova Communications", "RundiNova Team Member"]},
    {"email": "fanuel.kasumba@rundinova.com", "first_name": "Fanuel", "last_name": "Kasumba Mandela", "designation": "Head of People & Culture", "roles": ["RundiNova People & Culture", "RundiNova Team Member"]},
]


def ensure_team_users(temporary_password=None):
    """Create founding accounts and add roles without a shared default password."""
    results = {}
    for spec in TEAM_USERS:
        email = spec["email"]
        if frappe.db.exists("User", email):
            user = frappe.get_doc("User", email)
        else:
            user = frappe.new_doc("User")
            user_data = {
                "email": email,
                "first_name": spec["first_name"],
                "last_name": spec["last_name"],
                "enabled": 1,
                "user_type": "System User",
                "send_welcome_email": 0,
            }
            if temporary_password:
                user_data["new_password"] = temporary_password
            user.update(user_data)
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
