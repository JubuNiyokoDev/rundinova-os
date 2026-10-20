"""Manager report showing who has submitted the required daily follow-up."""

from frappe import _
from frappe.utils import nowdate

from rundinova_tech.rundinova_tech.daily_follow_up import get_daily_follow_up_compliance


def execute(filters=None):
    filters = filters or {}
    update_date = filters.get("date") or nowdate()
    columns = [
        {"fieldname": "employee_name", "label": _("Employee"), "fieldtype": "Data", "width": 190},
        {"fieldname": "status", "label": _("Status"), "fieldtype": "Data", "width": 110},
        {"fieldname": "daily_update", "label": _("Daily Update"), "fieldtype": "Link", "options": "RundiNova Daily Update", "width": 170},
        {"fieldname": "primary_task", "label": _("Primary Task"), "fieldtype": "Link", "options": "Task", "width": 170},
        {"fieldname": "project", "label": _("Project"), "fieldtype": "Link", "options": "Project", "width": 170},
        {"fieldname": "blocker_status", "label": _("Blockers"), "fieldtype": "Data", "width": 110},
        {"fieldname": "time_spent_hours", "label": _("Hours"), "fieldtype": "Float", "width": 80},
    ]
    return columns, get_daily_follow_up_compliance(update_date)
