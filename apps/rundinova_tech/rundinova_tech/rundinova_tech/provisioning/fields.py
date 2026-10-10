import frappe


def backfill_budget_titles():
    """Populate human-readable titles and consumption totals on legacy budgets."""
    from rundinova_tech.rundinova_tech.doctype.rundinova_food_budget.rundinova_food_budget import (
        set_budget_title,
        update_budget_totals,
    )

    for name in frappe.get_all("RundiNova Food Budget", pluck="name"):
        budget = frappe.get_doc("RundiNova Food Budget", name)
        set_budget_title(budget)
        update_budget_totals(budget)
        budget.db_update()


def fix_company_currency():
    """Set company currency to BIF with the product's FBU display symbol."""
    if frappe.db.exists("Currency", "BIF"):
        frappe.db.set_value("Currency", "BIF", "symbol", "FBU", update_modified=False)
    if frappe.db.exists("Company", "RundiNova Tech"):
        company = frappe.get_doc("Company", "RundiNova Tech")
        if company.default_currency != "BIF":
            company.default_currency = "BIF"
            company.save()
    frappe.clear_cache()


def ensure_purchase_invoice_budget_field():
    """Add the optional budget selector to ERPNext Purchase Invoice once."""
    fieldname = "rundinova_food_budget"
    if frappe.db.exists("Custom Field", {"dt": "Purchase Invoice", "fieldname": fieldname}):
        return
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Purchase Invoice",
        "fieldname": fieldname,
        "label": "RundiNova Food Budget",
        "fieldtype": "Link",
        "options": "RundiNova Food Budget",
        "insert_after": "supplier",
        "module": "RundiNova Tech",
    }).insert(ignore_permissions=True, ignore_if_duplicate=True)


def ensure_task_repository_field():
    """Add RundiNova Repository link to ERPNext Task for better project tracking."""
    fieldname = "rundinova_repository"
    if frappe.db.exists("Custom Field", {"dt": "Task", "fieldname": fieldname}):
        return
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Task",
        "fieldname": fieldname,
        "label": "RundiNova Repository",
        "fieldtype": "Link",
        "options": "RundiNova Repository",
        "insert_after": "project",
        "module": "RundiNova Tech",
    }).insert(ignore_permissions=True, ignore_if_duplicate=True)


def ensure_project_repository_field():
    """Add RundiNova Repository link to ERPNext Project."""
    fieldname = "rundinova_repository"
    if frappe.db.exists("Custom Field", {"dt": "Project", "fieldname": fieldname}):
        return
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Project",
        "fieldname": fieldname,
        "label": "RundiNova Repository",
        "fieldtype": "Link",
        "options": "RundiNova Repository",
        "insert_after": "project_name",
        "module": "RundiNova Tech",
    }).insert(ignore_permissions=True, ignore_if_duplicate=True)
