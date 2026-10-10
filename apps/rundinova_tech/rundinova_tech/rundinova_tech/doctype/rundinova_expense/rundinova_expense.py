import frappe
from frappe import _
from frappe.model.document import Document
from rundinova_core.expense import expense_validation_actions

EXPENSE_VALIDATION_MESSAGES = {
    "amount_must_be_positive": "Expense amount must be greater than zero.",
    "evidence_required": "Attach a receipt or other evidence before submitting an expense.",
    "payment_method_required": "Payment method is required for a paid expense.",
}


class RundiNovaExpense(Document):
    def before_insert(self):
        set_expense_title(self)

    def validate(self):
        set_expense_title(self)
        actions = expense_validation_actions(
            amount=frappe.utils.flt(self.amount),
            status=self.status,
            receipt_present=bool(self.receipt),
            approved_by_present=bool(self.approved_by),
            payment_method=self.payment_method,
        )
        for action in actions:
            if action == "stamp_approver":
                self.approved_by = frappe.session.user
            else:
                frappe.throw(_(EXPENSE_VALIDATION_MESSAGES[action]))


def set_expense_title(doc):
    if doc.expense_date and doc.category and doc.description:
        doc.expense_title = (
            f"{doc.expense_date} - {doc.category} - {doc.description[:60]}"
        )
