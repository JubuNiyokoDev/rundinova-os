import frappe
from frappe import _
from frappe.model.document import Document

from rundinova_core.governance import goal_achievement, goal_validation_actions


class RundiNovaGoal(Document):
    def validate(self):
        target_value = frappe.utils.flt(self.target_value)
        messages = {
            "goal_period_invalid": _(
                "Goal end date cannot be before its start date."
            ),
            "goal_target_not_positive": _("Target value must be greater than zero."),
        }
        actions = goal_validation_actions(
            self.period_start, self.period_end, target_value
        )
        if actions:
            frappe.throw(messages[actions[0]])

        self.achievement_percent, achieved_status = goal_achievement(
            frappe.utils.flt(self.current_value), target_value
        )
        if achieved_status:
            self.status = achieved_status
