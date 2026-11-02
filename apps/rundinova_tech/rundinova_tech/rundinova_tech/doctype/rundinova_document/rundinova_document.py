import frappe
from frappe import _
from frappe.model.document import Document
from rundinova_core.governance import document_validation_actions


class RundiNovaDocument(Document):
    def validate(self):
        self._apply_folder_defaults()
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

    def _apply_folder_defaults(self):
        if not self.document_folder:
            return
        folder = frappe.db.get_value(
            "RundiNova Document Folder",
            self.document_folder,
            ["project", "default_confidentiality", "access_scope", "status"],
            as_dict=True,
        )
        if not folder or folder.status != "Active":
            frappe.throw(_("Select an active document folder."))
        if folder.project and not self.project:
            self.project = folder.project
        # A folder is the classification boundary: its confidentiality policy must
        # take precedence over the generic document default.
        if folder.default_confidentiality:
            self.confidentiality = folder.default_confidentiality
        if folder.access_scope:
            self.access_scope = folder.access_scope
