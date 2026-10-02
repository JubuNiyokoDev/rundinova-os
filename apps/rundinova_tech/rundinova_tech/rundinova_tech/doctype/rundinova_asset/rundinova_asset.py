import frappe
from frappe import _
from frappe.model.document import Document


class RundiNovaAsset(Document):
    def validate(self):
        if frappe.utils.flt(self.purchase_amount) < 0 or frappe.utils.flt(self.current_value) < 0:
            frappe.throw(_("Asset values cannot be negative."))
        if self.status == "In Use" and not self.assigned_to and not self.location:
            frappe.throw(_("An asset in use must have an assignee or a location."))
