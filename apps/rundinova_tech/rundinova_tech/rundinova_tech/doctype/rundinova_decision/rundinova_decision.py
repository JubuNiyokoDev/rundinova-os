import frappe
from frappe import _
from frappe.model.document import Document

from rundinova_core.governance import decision_validation_actions


class RundiNovaDecision(Document):
    def validate(self):
        messages = {
            "completed_decision_requires_follow_up": _(
                "A completed decision must have a follow-up task or meeting evidence."
            ),
            "follow_up_before_decision_date": _(
                "Follow-up date cannot be before the decision date."
            ),
        }
        actions = decision_validation_actions(
            self.status,
            self.action_task,
            self.evidence,
            self.follow_up_date,
            self.decision_date,
        )
        if actions:
            frappe.throw(messages[actions[0]])
