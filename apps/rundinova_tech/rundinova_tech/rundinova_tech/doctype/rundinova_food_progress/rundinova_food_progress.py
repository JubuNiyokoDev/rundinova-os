import frappe
from frappe import _
from frappe.model.document import Document

from rundinova_core.food import ACTIVE_EXPENSE_STATUSES, calculate_food_progress

ACTIVE_STATUSES = tuple(ACTIVE_EXPENSE_STATUSES)


class RundiNovaFoodProgress(Document):
    def before_insert(self):
        set_progress_title(self)

    def validate(self):
        set_progress_title(self)

    def on_update(self):
        recalculate(self)


def set_progress_title(doc):
    if doc.item and doc.budget:
        budget_title = frappe.db.get_value("RundiNova Food Budget", doc.budget, "budget_title") or doc.budget
        item_title = frappe.db.get_value("Item", doc.item, "item_name") or doc.item
        doc.progress_title = f"{item_title} · {budget_title}"


def recalculate(doc, _method=None):
    if not doc.budget or not doc.item:
        return

    item_row = frappe.get_all(
        "RundiNova Food Budget Item",
        filters={"parent": doc.budget, "item": doc.item},
        fields=["quantity", "unit", "monthly_amount"],
    )
    if not item_row:
        frappe.throw(_("No budget line exists for this item in the selected budget."))
    row = item_row[0]
    expenses = frappe.get_all(
        "RundiNova Food Expense",
        filters={"budget": doc.budget, "item": doc.item, "status": ["in", list(ACTIVE_STATUSES)]},
        fields=["quantity", "amount", "status"],
    )
    try:
        today = frappe.utils.getdate(frappe.utils.nowdate())
        end = frappe.utils.getdate(frappe.db.get_value("RundiNova Food Budget", doc.budget, "period_end"))
    except Exception:
        today = end = None
    result = calculate_food_progress(
        planned_quantity=frappe.utils.flt(row.quantity),
        unit=row.unit,
        planned_amount=frappe.utils.flt(row.monthly_amount),
        expenses=(
            (frappe.utils.flt(expense.quantity), frappe.utils.flt(expense.amount), expense.status)
            for expense in expenses
        ),
        today=today,
        period_end=end,
    )
    for fieldname, value in result.items():
        setattr(doc, fieldname, value)
