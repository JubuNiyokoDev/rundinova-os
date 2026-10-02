import frappe
from frappe import _
from frappe.model.document import Document


class RundiNovaCashAccount(Document):
    def validate(self):
        if frappe.utils.flt(self.opening_balance) < 0:
            frappe.throw(_("Opening balance cannot be negative."))
        if not self.currency:
            self.currency = "BIF"
