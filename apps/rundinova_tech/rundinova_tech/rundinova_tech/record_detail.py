"""Read-model API for the RundiNova detail-first interface."""

import frappe
from frappe import _


DETAIL_DOCTYPES = {
    "Project",
    "Task",
    "Employee",
    "RundiNova Asset",
    "RundiNova Budget Review",
    "RundiNova Cash Account",
    "RundiNova Cash Movement",
    "RundiNova Community Impact",
    "RundiNova Daily Update",
    "RundiNova Decision",
    "RundiNova Document",
    "RundiNova Document Folder",
    "RundiNova Expense",
    "RundiNova Food Budget",
    "RundiNova Food Expense",
    "RundiNova Food Progress",
    "RundiNova Goal",
    "RundiNova Governance Meeting",
    "RundiNova Growth Opportunity",
    "RundiNova KPI Definition",
    "RundiNova KPI Snapshot",
    "RundiNova Meeting Action",
    "RundiNova Office",
    "RundiNova Partnership",
    "RundiNova Repository",
    "RundiNova Risk",
    "RundiNova Weekly Management Report",
}

STRUCTURAL_FIELD_TYPES = {
    "Section Break",
    "Column Break",
    "Tab Break",
    "HTML",
    "Heading",
    "Button",
    "Fold",
}


def _visible_field(field):
    return bool(
        field.fieldname
        and not field.hidden
        and field.fieldtype not in STRUCTURAL_FIELD_TYPES
        and field.fieldname
        not in {"naming_series", "amended_from", "_user_tags", "_comments", "_assign", "_liked_by"}
    )


def _field_payload(field, value):
    return {
        "fieldname": field.fieldname,
        "label": field.label or field.fieldname.replace("_", " ").title(),
        "fieldtype": field.fieldtype,
        "options": field.options,
        "value": value,
    }


def _table_payload(doc, field):
    rows = doc.get(field.fieldname) or []
    if not rows:
        return None
    child_meta = frappe.get_meta(field.options)
    columns = [child for child in child_meta.fields if _visible_field(child)][:6]
    return {
        "label": field.label,
        "fieldname": field.fieldname,
        "columns": [
            {"fieldname": column.fieldname, "label": column.label, "fieldtype": column.fieldtype, "options": column.options}
            for column in columns
        ],
        "rows": [{column.fieldname: row.get(column.fieldname) for column in columns} for row in rows],
    }


@frappe.whitelist()
def get_record_detail(doctype, name):
    """Return a permission-checked, display-only document projection."""
    if doctype not in DETAIL_DOCTYPES:
        frappe.throw(_("This record type is not available in the RundiNova detail view."), frappe.PermissionError)
    doc = frappe.get_doc(doctype, name)
    if not frappe.has_permission(doctype, "read", doc=doc):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    meta = frappe.get_meta(doctype)
    sections = []
    current = {"label": _("Informations"), "fields": []}
    tables = []
    for field in meta.fields:
        if field.fieldtype == "Section Break":
            if current["fields"]:
                sections.append(current)
            current = {"label": field.label or _("Informations"), "fields": []}
            continue
        if field.fieldtype == "Table":
            table = _table_payload(doc, field)
            if table:
                tables.append(table)
            continue
        if not _visible_field(field):
            continue
        value = doc.get(field.fieldname)
        if value in (None, "", 0, 0.0, [], {}):
            continue
        current["fields"].append(_field_payload(field, value))
    if current["fields"]:
        sections.append(current)

    title = doc.get(meta.title_field) if meta.title_field else None
    return {
        "doctype": doctype,
        "name": name,
        "title": title or name,
        "status": doc.get("status"),
        "modified": doc.modified,
        "owner": doc.owner,
        "can_edit": frappe.has_permission(doctype, "write", doc=doc),
        "sections": sections,
        "tables": tables,
    }
