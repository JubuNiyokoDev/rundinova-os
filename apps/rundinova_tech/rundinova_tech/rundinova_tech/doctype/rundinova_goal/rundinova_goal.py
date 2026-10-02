import frappe
from frappe import _
from frappe.model.document import Document


class RundiNovaGoal(Document):
    def validate(self):
        if self.period_end < self.period_start:
            frappe.throw(_("Goal end date cannot be before its start date."))
        if frappe.utils.flt(self.target_value) <= 0:
            frappe.throw(_("Target value must be greater than zero."))
        self.achievement_percent = min(100, max(0, frappe.utils.flt(self.current_value) / frappe.utils.flt(self.target_value) * 100))
        if self.achievement_percent >= 100:
            self.status = "Achieved"
