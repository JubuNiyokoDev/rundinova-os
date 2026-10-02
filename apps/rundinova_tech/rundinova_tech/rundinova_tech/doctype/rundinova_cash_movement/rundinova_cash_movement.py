import frappe
from frappe import _
from frappe.model.document import Document


class RundiNovaCashMovement(Document):
    def before_insert(self):
        set_movement_title(self)

    def validate(self):
        set_movement_title(self)
        if frappe.utils.flt(self.amount) <= 0:
            frappe.throw(_("Movement amount must be greater than zero."))
        if self.movement_type == "Transfer" and not self.destination_account:
            frappe.throw(_("A transfer requires a destination account."))
        if self.movement_type != "Transfer" and self.destination_account:
            frappe.throw(_("Destination account is only used for transfers."))
        if self.status in ("Submitted", "Approved", "Reconciled") and not self.evidence:
            frappe.throw(_("Evidence is required before submitting a movement."))
        if self.status in ("Approved", "Reconciled") and not self.approved_by:
            self.approved_by = frappe.session.user


def set_movement_title(doc):
    if doc.movement_date and doc.movement_type and doc.category:
        doc.movement_title = f"{doc.movement_date} - {doc.movement_type} - {doc.category}"
