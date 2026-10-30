"""Professional document library configuration and starter folders."""

import frappe


ROOT_FOLDERS = (
    ("À classer", None, None, "Internal", "Documents reçus en attente de classement."),
    ("Gouvernance", None, None, "Internal", "Décisions, procès-verbaux et documents institutionnels."),
    ("Finance & budgets", None, None, "Confidential", "Budgets, factures, reçus, mouvements et rapports financiers."),
    ("Équipe & RH", None, None, "Confidential", "Documents d'équipe, contrats et procédures internes."),
    ("Commercial & partenariats", None, None, "Internal", "Offres, conventions, partenariats et communication."),
    ("Juridique & conformité", None, None, "Restricted", "Contrats, conformité et documents juridiques sensibles."),
    ("Projets & livraison", None, None, "Internal", "Dossiers de travail et livrables liés aux projets."),
)

PROJECT_FOLDERS = ("Medicare", "ComLab", "Imbonakazoza", "NOVARIS")


def _ensure_folder(name, parent=None, project=None, confidentiality="Internal", description=""):
    existing = frappe.db.exists("RundiNova Document Folder", {"folder_name": name, "parent_folder": parent})
    values = {
        "folder_name": name,
        "parent_folder": parent,
        "project": project,
        "folder_owner": "Administrator",
        "default_confidentiality": confidentiality,
        "status": "Active",
        "description": description,
    }
    if existing:
        document = frappe.get_doc("RundiNova Document Folder", existing)
        document.update(values)
        document.save(ignore_permissions=True)
        return document.name
    return frappe.get_doc({"doctype": "RundiNova Document Folder", **values}).insert(
        ignore_permissions=True
    ).name


def sync_document_library():
    """Provision a usable document structure without creating business files."""
    for name, parent, project, confidentiality, description in ROOT_FOLDERS:
        _ensure_folder(name, parent, project, confidentiality, description)

    projects_root = frappe.db.get_value(
        "RundiNova Document Folder", {"folder_name": "Projets & livraison", "parent_folder": ["is", "not set"]}
    )
    for project_name in PROJECT_FOLDERS:
        project = frappe.db.get_value("Project", {"project_name": project_name}, "name")
        if project:
            _ensure_folder(
                project_name,
                projects_root,
                project,
                "Internal",
                f"Documents et livrables du projet {project_name}.",
            )
    frappe.clear_cache(doctype="RundiNova Document Folder")
