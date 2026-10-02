"""Read-only onboarding checks for the RundiNova production setup."""

import frappe


@frappe.whitelist()
def get_onboarding_status():
    """Return a safe, non-sensitive readiness summary.

    This endpoint never creates or changes business data. It is intended for
    the administrator's first-run checklist before production use.
    """
    checks = []

    def check(key, label, ready, detail):
        checks.append({"key": key, "label": label, "ready": bool(ready), "detail": detail})

    company_count = frappe.db.count("Company")
    check("company", "Company configured", company_count > 0, f"{company_count} company record(s)")

    user_count = frappe.db.count("User", {"enabled": 1, "user_type": "System User"})
    check("users", "Active system users", user_count >= 1, f"{user_count} active system user(s)")

    employee_count = frappe.db.count("Employee", {"status": "Active"})
    check("employees", "Active employees", employee_count >= 1, f"{employee_count} active employee(s)")

    project_count = frappe.db.count("Project", {"status": ["!=", "Cancelled"]})
    check("projects", "First project", project_count >= 1, f"{project_count} active project record(s)")

    repository_count = frappe.db.count("RundiNova Repository")
    check("repositories", "GitHub repositories", repository_count >= 1, f"{repository_count} repository record(s)")

    expense_count = frappe.db.count("RundiNova Expense")
    check("expenses", "General expense tracking", expense_count >= 1, f"{expense_count} expense record(s)")

    asset_count = frappe.db.count("RundiNova Asset")
    check("assets", "Asset register", asset_count >= 1, f"{asset_count} asset record(s)")

    cash_account_count = frappe.db.count("RundiNova Cash Account", {"status": "Active"})
    check("cash_accounts", "Cash accounts", cash_account_count >= 1, f"{cash_account_count} active cash account(s)")

    movement_count = frappe.db.count("RundiNova Cash Movement", {"status": ["in", ["Approved", "Reconciled"]]})
    check("cash_movements", "Approved cash movements", movement_count >= 1, f"{movement_count} approved movement(s)")

    budget_count = frappe.db.count("RundiNova Food Budget")
    check("food_budget", "Food budget", budget_count >= 1, f"{budget_count} budget record(s)")

    check("roles", "RundiNova roles", frappe.db.count("Role", {"role_name": ["like", "RundiNova %"]}) >= 5, "Five named roles are expected")

    ready = all(item["ready"] for item in checks)
    return {"ready": ready, "checks": checks}
