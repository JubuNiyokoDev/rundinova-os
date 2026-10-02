import frappe
from frappe import _
from frappe.model.document import Document


class RundiNovaExpense(Document):
    def before_insert(self):
        set_expense_title(self)

    def validate(self):
        set_expense_title(self)
        if frappe.utils.flt(self.amount) <= 0:
            frappe.throw(_("Expense amount must be greater than zero."))
        if self.status in ("Submitted", "Approved", "Paid") and not self.receipt:
            frappe.throw(_("Attach a receipt or other evidence before submitting an expense."))
        if self.status in ("Approved", "Paid") and not self.approved_by:
            self.approved_by = frappe.session.user
        if self.status == "Paid" and not self.payment_method:
            frappe.throw(_("Payment method is required for a paid expense."))


def set_expense_title(doc):
    if doc.expense_date and doc.category and doc.description:
        doc.expense_title = f"{doc.expense_date} - {doc.category} - {doc.description[:60]}"
