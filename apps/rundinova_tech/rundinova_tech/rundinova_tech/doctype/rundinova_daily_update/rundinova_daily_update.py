"""The required end-of-day update for each active RundiNova employee."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, now_datetime, today


REVIEWER_ROLES = (
    "RundiNova Director",
    "RundiNova Operations",
    "RundiNova Project Lead",
    "RundiNova People & Culture",
    "System Manager",
)


def employee_for_user(user):
    """Return the active Employee linked to a system user, if one exists."""
    return frappe.db.get_value(
        "Employee", {"user_id": user, "status": "Active"}, "name"
    )


def user_can_review(user=None):
    return bool(set(frappe.get_roles(user or frappe.session.user)).intersection(REVIEWER_ROLES))


class RundiNovaDailyUpdate(Document):
    def validate(self):
        self._set_employee_from_session()
        self._validate_date_and_progress()
        self._validate_blocker()
        self._validate_one_update_per_day()

    def _set_employee_from_session(self):
        if user_can_review():
            return
        employee = employee_for_user(frappe.session.user)
        if not employee:
            frappe.throw(
                _("Your user account must be linked to an active Employee before submitting a daily update.")
            )
        self.employee = employee

    def _validate_date_and_progress(self):
        if getdate(self.update_date) > getdate(today()):
            frappe.throw(_("A daily update cannot be dated in the future."))
        if flt(self.time_spent_hours) <= 0:
            frappe.throw(_("Time spent must be greater than zero."))
        if not 0 <= flt(self.progress_percent) <= 100:
            frappe.throw(_("Task progress must be between 0 and 100 percent."))

    def _validate_blocker(self):
        if self.blocker_status == "Blocked" and not (self.blocker_details or "").strip():
            frappe.throw(_("Describe the blocker and the help needed."))

    def _validate_one_update_per_day(self):
        duplicate = frappe.db.exists(
            "RundiNova Daily Update",
            {"employee": self.employee, "update_date": self.update_date, "name": ["!=", self.name]},
        )
        if duplicate:
            frappe.throw(_("This employee already has a daily update for this date."))

    @frappe.whitelist()
    def mark_reviewed(self):
        if not user_can_review():
            frappe.throw(_("Only a project lead or manager can review daily updates."), frappe.PermissionError)
        self.review_status = "Reviewed"
        self.reviewed_by = frappe.session.user
        self.reviewed_on = now_datetime()
        self.save()
        return self.as_dict()
