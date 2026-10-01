import re

import frappe
from frappe import _
from frappe.model.document import Document


GITHUB_URL = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$")


class RundiNovaRepository(Document):
    def validate(self):
        if not GITHUB_URL.fullmatch((self.github_url or "").strip()):
            frappe.throw(_("Use a public GitHub repository URL, for example https://github.com/org/repository."))
        if not 0 <= frappe.utils.flt(self.progress_percent) <= 100:
            frappe.throw(_("Progress must be between 0 and 100 percent."))
