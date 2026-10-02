import frappe
from frappe import _
from frappe.model.document import Document


class RundiNovaDocument(Document):
    def validate(self):
        if self.review_date and self.document_date and self.review_date < self.document_date:
            frappe.throw(_("Review date cannot be before the document date."))
        if self.confidentiality == "Restricted" and not self.owner:
            frappe.throw(_("Restricted documents require an owner."))
