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

    def before_save(self):
        """Update task counts before saving."""
        self.update_task_counts()

    def update_task_counts(self):
        """Count tasks linked to this repository."""
        if self.name:
            total_tasks = frappe.db.count("Task", {"rundinova_repository": self.name})
            completed_tasks = frappe.db.count("Task", {"rundinova_repository": self.name, "status": "Completed"})
            self.tasks_count = total_tasks
            self.completed_tasks_count = completed_tasks

    @frappe.whitelist()
    def sync_from_github(self):
        """Pull public metadata from GitHub (read-only GET). Updates local fields."""
        if not frappe.has_permission("RundiNova Repository", "write", self):
            frappe.throw(_("You need write access to sync this repository."), frappe.PermissionError)

        from rundinova_tech.github_sync import sync_repository

        try:
            info = sync_repository(self.github_url)
        except Exception as exc:
            frappe.throw(_("GitHub sync failed: {0}").format(str(exc)))

        self.open_issues_count = info.get("open_issues_count", 0)
        self.stargazers_count = info.get("stargazers_count", 0)
        self.forks_count = info.get("forks_count", 0)
        self.default_branch = info.get("default_branch", "")
        self.primary_language = info.get("language", "")
        self.last_push_date = info.get("pushed_at", "")
        self.last_synced_on = now_datetime()
        self.save()
        frappe.msgprint(_("Repository synced from GitHub successfully."))
        return info

    @frappe.whitelist()
    def view_tasks(self):
        """Redirect to Task list filtered by this repository."""
        frappe.response.type = "redirect"
        frappe.response.location = "/app/task?rundinova_repository={0}".format(self.name)
