import frappe
from frappe import _
from frappe.model.document import Document


class RundiNovaDecision(Document):
    def validate(self):
        if self.status == "Completed" and not self.action_task and not self.evidence:
            frappe.throw(_("A completed decision must have a follow-up task or meeting evidence."))
        if self.follow_up_date and self.decision_date and self.follow_up_date < self.decision_date:
            frappe.throw(_("Follow-up date cannot be before the decision date."))
