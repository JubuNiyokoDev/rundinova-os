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
    if frappe.db.exists(
        "Custom Field", {"dt": "Purchase Invoice", "fieldname": fieldname}
    ):
        return
    frappe.get_doc(
        {
            "doctype": "Custom Field",
            "dt": "Purchase Invoice",
            "fieldname": fieldname,
            "label": "RundiNova Food Budget",
            "fieldtype": "Link",
            "options": "RundiNova Food Budget",
            "insert_after": "supplier",
            "module": "RundiNova Tech",
        }
    ).insert(ignore_permissions=True, ignore_if_duplicate=True)


def ensure_task_repository_field():
    """Add RundiNova Repository link to ERPNext Task for better project tracking."""
    fieldname = "rundinova_repository"
    if frappe.db.exists("Custom Field", {"dt": "Task", "fieldname": fieldname}):
        return
    frappe.get_doc(
        {
            "doctype": "Custom Field",
            "dt": "Task",
            "fieldname": fieldname,
            "label": "RundiNova Repository",
            "fieldtype": "Link",
            "options": "RundiNova Repository",
            "insert_after": "project",
            "module": "RundiNova Tech",
        }
    ).insert(ignore_permissions=True, ignore_if_duplicate=True)


def ensure_task_test_fields():
    """Provision the collaborative test fields and expose the result in Task lists."""
    fields = [
        {
            "fieldname": "rundinova_test_section",
            "label": "Recette RundiNova",
            "fieldtype": "Section Break",
            "insert_after": "rundinova_repository",
        },
        {
            "fieldname": "rundinova_test_result",
            "label": "Résultat de recette",
            "fieldtype": "Select",
            "options": "À tester\nValidé\nÀ corriger\nBloqué\nNon applicable",
            "insert_after": "rundinova_test_section",
            "in_list_view": 1,
        },
        {
            "fieldname": "rundinova_last_updated_by",
            "label": "Mis à jour par (technique)",
            "fieldtype": "Link",
            "options": "User",
            "read_only": 1,
            "hidden": 1,
            "insert_after": "rundinova_test_result",
        },
        {
            "fieldname": "rundinova_last_updated_by_name",
            "label": "Mis à jour par",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "rundinova_last_updated_by",
            "in_list_view": 1,
        },
        {
            "fieldname": "rundinova_test_summary",
            "label": "Résumé de mise à jour",
            "fieldtype": "Data",
            "description": "Une phrase courte visible dans la liste des tâches.",
            "insert_after": "rundinova_last_updated_by",
            "in_list_view": 1,
        },
        {
            "fieldname": "rundinova_test_evidence",
            "label": "Preuve de recette (si pertinente)",
            "fieldtype": "Attach",
            "description": "Optionnelle : ajoutez une preuve seulement lorsqu'elle est utile.",
            "insert_after": "rundinova_test_result",
        },
        {
            "fieldname": "rundinova_test_notes",
            "label": "Constat / anomalie",
            "fieldtype": "Small Text",
            "insert_after": "rundinova_test_evidence",
        },
        {
            "fieldname": "rundinova_test_validated_by",
            "label": "Validé par",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "rundinova_test_notes",
        },
        {
            "fieldname": "rundinova_test_validated_on",
            "label": "Date de validation",
            "fieldtype": "Datetime",
            "insert_after": "rundinova_test_validated_by",
        },
    ]
    for values in fields:
        existing = frappe.db.get_value(
            "Custom Field", {"dt": "Task", "fieldname": values["fieldname"]}
        )
        if existing:
            field = frappe.get_doc("Custom Field", existing)
            changed = False
            for key, value in values.items():
                if field.get(key) != value:
                    field.set(key, value)
                    changed = True
            if changed:
                field.save(ignore_permissions=True)
            continue
        frappe.get_doc(
            {
                "doctype": "Custom Field",
                "dt": "Task",
                "module": "RundiNova Tech",
                **values,
            }
        ).insert(ignore_permissions=True, ignore_if_duplicate=True)
    frappe.clear_cache(doctype="Task")


def ensure_project_repository_field():
    """Add RundiNova Repository link to ERPNext Project."""
    fieldname = "rundinova_repository"
    if frappe.db.exists("Custom Field", {"dt": "Project", "fieldname": fieldname}):
        return
    frappe.get_doc(
        {
            "doctype": "Custom Field",
            "dt": "Project",
            "fieldname": fieldname,
            "label": "RundiNova Repository",
            "fieldtype": "Link",
            "options": "RundiNova Repository",
            "insert_after": "project_name",
            "module": "RundiNova Tech",
        }
    ).insert(ignore_permissions=True, ignore_if_duplicate=True)
