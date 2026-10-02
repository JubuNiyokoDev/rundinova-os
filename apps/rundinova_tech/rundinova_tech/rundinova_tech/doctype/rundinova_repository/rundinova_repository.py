import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


GITHUB_URL = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$")


class RundiNovaRepository(Document):
    def validate(self):
        if not GITHUB_URL.fullmatch((self.github_url or "").strip()):
            frappe.throw(_("Use a public GitHub repository URL, for example https://github.com/org/repository."))
        if not 0 <= frappe.utils.flt(self.progress_percent) <= 100:
            frappe.throw(_("Progress must be between 0 and 100 percent."))

    @frappe.whitelist()
    def sync_from_github(self):
        """Pull public metadata from GitHub (read-only GET). Updates local fields."""
        from rundinova_tech.github_sync import sync_repository

        try:
            info = sync_repository(self.github_url)
        except Exception as exc:
            frappe.throw(_("GitHub sync failed: {0}").format(str(exc)))

        self.open_issues_count = info.get("open_issues_count", 0)
        self.stargazers_count = info.get("stargazers_count", 0)
        self.forks_count = info.get("forks_count", 0)
        self.default_branch = info.get("default_branch", "")
        self.primary_language = info.get("primary_language", "")
        self.last_push_date = info.get("last_push_date", "")
        self.last_synced_on = now_datetime()
        self.save(ignore_permissions=True)
        frappe.msgprint(_("Repository synced from GitHub successfully."))
        return info
