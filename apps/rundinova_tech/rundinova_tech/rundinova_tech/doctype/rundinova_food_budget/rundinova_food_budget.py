import frappe
from frappe import _
from frappe.model.document import Document

from rundinova_core.food import (
    calculate_food_budget_plan,
    calculate_food_budget_usage,
    validate_food_budget_plan,
)


class RundiNovaFoodBudget(Document):
    def validate(self):
        validate_budget(self)

    def before_insert(self):
        set_budget_title(self)


def validate_budget(doc, _method=None):
    set_budget_title(doc)
    monthly_amounts = [
        frappe.utils.flt(item.monthly_amount) for item in (doc.items or [])
    ]
    total = sum(monthly_amounts)
    ceiling = frappe.utils.flt(doc.approved_ceiling)

    violation = validate_food_budget_plan(
        total,
        ceiling,
        doc.covered_people,
        bool(doc.branch),
        bool(doc.cost_center),
    )
    if violation == "planned_total_exceeds_ceiling":
        frappe.throw(
            _("The item total {0} BIF exceeds the approved ceiling of {1} BIF.").format(
                frappe.utils.fmt_money(total, currency="BIF"),
                frappe.utils.fmt_money(ceiling, currency="BIF"),
            )
        )

    if violation == "covered_people_must_be_positive":
        frappe.throw(_("Covered people must be at least one."))

    if violation == "branch_requires_cost_center":
        frappe.throw(_("A cost center is required when a branch is selected."))

    plan = calculate_food_budget_plan(monthly_amounts, doc.covered_people)
    for field, value in plan.items():
        setattr(doc, field, value)
    update_budget_totals(doc)


def set_budget_title(doc):
    if doc.period_start and doc.branch:
        period = frappe.utils.getdate(doc.period_start).strftime("%Y-%m")
        doc.budget_title = f"Food Budget - {doc.branch} - {period}"


def update_budget_totals(doc):
    """Refresh committed, paid and remaining amounts from daily expenses."""
    expenses = frappe.get_all(
        "RundiNova Food Expense",
        filters={"budget": doc.name, "status": ["in", ["Submitted", "Approved", "Paid"]]},
        fields=["amount", "status"],
    ) if doc.name and frappe.db.exists("RundiNova Food Expense", {"budget": doc.name}) else []
    usage = calculate_food_budget_usage(
        frappe.utils.flt(doc.approved_ceiling),
        [(frappe.utils.flt(row.amount), row.status) for row in expenses],
    )
    for field, value in usage.items():
        setattr(doc, field, value)


def refresh_budget_totals(budget_name):
    if not budget_name or not frappe.db.exists("RundiNova Food Budget", budget_name):
        return
    budget = frappe.get_doc("RundiNova Food Budget", budget_name)
    update_budget_totals(budget)
    budget.db_update()
