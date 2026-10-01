import frappe
from frappe import _
from frappe.model.document import Document


class RundiNovaFoodBudget(Document):
    def validate(self):
        validate_budget(self)

    def before_insert(self):
        set_budget_title(self)


def validate_budget(doc, _method=None):
    set_budget_title(doc)
    total = sum(frappe.utils.flt(item.monthly_amount) for item in (doc.items or []))
    ceiling = frappe.utils.flt(doc.approved_ceiling)

    if total > ceiling:
        frappe.throw(
            _("The item total {0} BIF exceeds the approved ceiling of {1} BIF.").format(
                frappe.utils.fmt_money(total, currency="BIF"),
                frappe.utils.fmt_money(ceiling, currency="BIF"),
            )
        )

    if doc.covered_people and doc.covered_people < 1:
        frappe.throw(_("Covered people must be at least one."))

    if doc.branch and not doc.cost_center:
        frappe.throw(_("A cost center is required when a branch is selected."))

    doc.total_planned_amount = total
    doc.annual_planned_amount = total * 12
    doc.daily_planned_amount = total / 30
    doc.per_person_daily_amount = (
        total / 30 / doc.covered_people if doc.covered_people else 0
    )
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
    committed = sum(frappe.utils.flt(row.amount) for row in expenses)
    actual = sum(frappe.utils.flt(row.amount) for row in expenses if row.status == "Paid")
    doc.committed_amount = committed
    doc.actual_amount = actual
    doc.balance_amount = frappe.utils.flt(doc.approved_ceiling) - committed
    doc.consumed_percent = (committed / frappe.utils.flt(doc.approved_ceiling) * 100) if doc.approved_ceiling else 0


def refresh_budget_totals(budget_name):
    if not budget_name or not frappe.db.exists("RundiNova Food Budget", budget_name):
        return
    budget = frappe.get_doc("RundiNova Food Budget", budget_name)
    update_budget_totals(budget)
    budget.db_update()
