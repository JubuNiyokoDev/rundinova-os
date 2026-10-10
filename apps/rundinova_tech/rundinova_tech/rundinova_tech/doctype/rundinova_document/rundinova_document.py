import frappe
from frappe import _
from frappe.model.document import Document
from rundinova_core.governance import document_validation_actions


class RundiNovaDocument(Document):
    def validate(self):
        messages = {
            "review_before_document_date": _(
                "Review date cannot be before the document date."
            ),
            "restricted_document_requires_owner": _(
                "Restricted documents require an owner."
            ),
        }
        actions = document_validation_actions(
            self.review_date,
            self.document_date,
            self.confidentiality,
            self.document_owner,
        )
        if actions:
            frappe.throw(messages[actions[0]])
