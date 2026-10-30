import frappe
from frappe import _
from frappe.model.document import Document


class RundiNovaDocumentFolder(Document):
    def validate(self):
        if self.parent_folder == self.name:
            frappe.throw(_("A folder cannot be its own parent."))
        self._validate_parent_chain()

    def _validate_parent_chain(self):
        parent = self.parent_folder
        visited = {self.name} if self.name else set()
        while parent:
            if parent in visited:
                frappe.throw(_("A document folder cannot be placed in one of its children."))
            visited.add(parent)
            parent = frappe.db.get_value("RundiNova Document Folder", parent, "parent_folder")
