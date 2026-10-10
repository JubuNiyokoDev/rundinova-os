import frappe
from frappe import _
from frappe.model.document import Document

from rundinova_core.governance import asset_validation_actions


class RundiNovaAsset(Document):
    def validate(self):
        messages = {
            "asset_value_negative": _("Asset values cannot be negative."),
            "asset_in_use_requires_assignment_or_location": _(
                "An asset in use must have an assignee or a location."
            ),
        }
        actions = asset_validation_actions(
            frappe.utils.flt(self.purchase_amount),
            frappe.utils.flt(self.current_value),
            self.status,
            self.assigned_to,
            self.location,
        )
        if actions:
            frappe.throw(messages[actions[0]])
