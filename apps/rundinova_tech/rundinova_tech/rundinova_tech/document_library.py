"""Small, permission-aware API for the RundiNova document library."""

import frappe
from frappe import _


def _check_read(doctype):
    frappe.has_permission(doctype, "read", throw=True)


def _folder_breadcrumbs(folder_name):
    crumbs = []
    seen = set()
    while folder_name and folder_name not in seen:
        seen.add(folder_name)
        folder = frappe.get_doc("RundiNova Document Folder", folder_name)
        folder.check_permission("read")
        crumbs.append({"name": folder.name, "label": folder.folder_name})
        folder_name = folder.parent_folder
    return list(reversed(crumbs))


@frappe.whitelist()
def get_library(folder=None, search=None, document_type=None, project=None):
    """Return only folders and files visible to the current user."""
    _check_read("RundiNova Document Folder")
    _check_read("RundiNova Document")

    folder = folder or None
    if folder:
        _folder_breadcrumbs(folder)

    folder_filters = {"parent_folder": folder, "status": "Active"}
    document_filters = {"document_folder": folder, "status": "Active"}
    if project:
        document_filters["project"] = project
        folder_filters["project"] = project
    if document_type:
        document_filters["document_type"] = document_type
    if search:
        like = f"%{search.strip()}%"
        documents = frappe.get_list(
            "RundiNova Document",
            filters=document_filters,
            or_filters={"document_title": ["like", like]},
            fields=[
                "name",
                "document_title",
                "document_type",
                "file",
                "project",
                "confidentiality",
                "document_date",
                "modified",
            ],
            order_by="modified desc",
            limit_page_length=100,
        )
        folders = frappe.get_list(
            "RundiNova Document Folder",
            filters=folder_filters,
            or_filters={"folder_name": ["like", like]},
            fields=["name", "folder_name", "project", "default_confidentiality", "modified"],
            order_by="folder_name asc",
            limit_page_length=100,
        )
    else:
        folders = frappe.get_list(
            "RundiNova Document Folder",
            filters=folder_filters,
            fields=["name", "folder_name", "project", "default_confidentiality", "modified"],
            order_by="folder_name asc",
            limit_page_length=100,
        )
        documents = frappe.get_list(
            "RundiNova Document",
            filters=document_filters,
            fields=[
                "name",
                "document_title",
                "document_type",
                "file",
                "project",
                "confidentiality",
                "document_date",
                "modified",
            ],
            order_by="modified desc",
            limit_page_length=100,
        )

    projects = frappe.get_list(
        "Project", fields=["name", "project_name"], order_by="project_name asc", limit_page_length=200
    )
    return {
        "breadcrumbs": _folder_breadcrumbs(folder) if folder else [],
        "folders": folders,
        "documents": documents,
        "projects": projects,
    }


@frappe.whitelist()
def create_folder(folder_name, parent_folder=None, project=None):
    """Create a folder beneath the current folder, inheriting its project policy."""
    frappe.has_permission("RundiNova Document Folder", "create", throw=True)
    folder_name = (folder_name or "").strip()
    if not folder_name:
        frappe.throw(_("Le nom du dossier est obligatoire."))

    existing = frappe.db.exists(
        "RundiNova Document Folder",
        {"folder_name": folder_name, "parent_folder": parent_folder},
    )
    if existing:
        return {
            "name": existing,
            "label": folder_name,
            "created": False,
            "message": _("Ce dossier existe déjà dans cet emplacement."),
        }

    confidentiality = "Internal"
    if parent_folder:
        parent = frappe.get_doc("RundiNova Document Folder", parent_folder)
        parent.check_permission("read")
        project = project or parent.project
        confidentiality = parent.default_confidentiality

    document = frappe.get_doc(
        {
            "doctype": "RundiNova Document Folder",
            "folder_name": folder_name,
            "parent_folder": parent_folder,
            "project": project,
            "folder_owner": frappe.session.user,
            "default_confidentiality": confidentiality,
            "status": "Active",
        }
    )
    document.insert()
    # This endpoint is also invoked from the Desk modal. Commit explicitly so
    # the folder is immediately visible to the following library reload.
    frappe.db.commit()
    return {"name": document.name, "label": document.folder_name, "created": True}


@frappe.whitelist()
def create_document(document_title, document_type, file_url, folder=None, project=None, notes=None):
    """Register an uploaded file as a classified RundiNova document."""
    frappe.has_permission("RundiNova Document", "create", throw=True)
    if folder:
        library_folder = frappe.get_doc("RundiNova Document Folder", folder)
        library_folder.check_permission("read")
        project = project or library_folder.project

    file_doc = frappe.get_doc("File", {"file_url": file_url})
    file_doc.check_permission("read")
    document = frappe.get_doc(
        {
            "doctype": "RundiNova Document",
            "document_title": (document_title or "").strip(),
            "document_type": document_type,
            "file": file_url,
            "document_folder": folder,
            "project": project,
            "document_owner": frappe.session.user,
            "document_date": frappe.utils.today(),
            "status": "Active",
            "notes": notes,
        }
    )
    document.insert()
    file_doc.attached_to_doctype = "RundiNova Document"
    file_doc.attached_to_name = document.name
    file_doc.save(ignore_permissions=True)
    frappe.db.commit()
    return document.as_dict()
