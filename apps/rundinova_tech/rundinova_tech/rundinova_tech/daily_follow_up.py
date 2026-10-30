"""Daily follow-up reminders, compliance reporting, and portfolio onboarding."""

import frappe
from frappe import _
from frappe.utils import getdate, nowdate
from rundinova_tech.rundinova_tech.doctype.rundinova_daily_update.rundinova_daily_update import (
    employee_for_user,
)

PORTFOLIO = (
    "AgriLink",
    "DialGo",
    "Signatures",
    "NjiaNet",
    "Umuragizi",
    "UMS",
    "Gestion de Cooperatives",
    "eBIF",
    "Gestion des evenements",
    "Suivi des malades chroniques",
    "GoalSage AI",
    "RundiNovaOS",
    "Vanish",
    "StoryTus",
    "PartenerWanje",
    "Burundi KYCEngine",
    "DevBoost",
    "ShopSync",
    "MenyaArena",
    "KYMix",
    "Ndabazi",
    "UmwugaHome",
    "JuneTechInscription",
    "Iwanje",
    "CIVIX",
    "ComLab",
    "KitHub360",
    "UmugenziTech",
    "NOVARIS",
    "Absence Tracker",
    "RundiCheck",
    "Table Yawe",
    "Havila Energy",
    "Adren",
    "Ikigabo",
    "TechSafe",
    "REDA",
    "PharmaSync",
    "Imbonakazoza",
)
ACTIVE_PORTFOLIO = frozenset(("NOVARIS", "Imbonakazoza", "ComLab"))


def _is_working_day(date_value=None):
    return getdate(date_value or nowdate()).weekday() < 5


def _active_employees():
    return frappe.get_all(
        "Employee",
        filters={"status": "Active", "user_id": ["is", "set"]},
        fields=["name", "employee_name", "user_id"],
    )


def _has_daily_update(employee, update_date):
    return frappe.db.exists(
        "RundiNova Daily Update", {"employee": employee, "update_date": update_date}
    )


def _reminder_exists(employee, update_date, kind):
    return frappe.db.exists(
        "ToDo",
        {
            "reference_type": "Employee",
            "reference_name": employee,
            "description": ["like", f"%RundiNova {kind} {update_date}%"],
            "status": ["!=", "Cancelled"],
        },
    )


def _create_todo(employee, update_date, kind, priority, description):
    if _reminder_exists(employee["name"], update_date, kind):
        return False
    frappe.get_doc(
        {
            "doctype": "ToDo",
            "allocated_to": employee["user_id"],
            "reference_type": "Employee",
            "reference_name": employee["name"],
            "date": update_date,
            "priority": priority,
            "description": description,
        }
    ).insert(ignore_permissions=True)
    return True


def create_daily_follow_up_reminders():
    """At 07:00 CAT, remind every active employee without today's update."""
    if not _is_working_day():
        return {"created": 0, "reason": "non-working-day"}
    update_date = nowdate()
    created = 0
    for employee in _active_employees():
        if not _has_daily_update(employee["name"], update_date):
            created += _create_todo(
                employee,
                update_date,
                "daily update reminder",
                "Medium",
                _(
                    "RundiNova daily update reminder {0}: record today's primary task, work completed, hours, next action and blockers."
                ).format(update_date),
            )
    return {"created": created, "date": update_date}


def create_missing_daily_follow_up_escalations():
    """At 09:30 CAT, make missing reports visibly overdue for the employee."""
    if not _is_working_day():
        return {"created": 0, "reason": "non-working-day"}
    update_date = nowdate()
    created = 0
    for employee in _active_employees():
        if not _has_daily_update(employee["name"], update_date):
            created += _create_todo(
                employee,
                update_date,
                "missing daily update",
                "High",
                _(
                    "RundiNova missing daily update {0}: submit it now or tell your project lead what is blocking you."
                ).format(update_date),
            )
    return {"created": created, "date": update_date}


def get_daily_follow_up_compliance(update_date=None):
    """Return one compliance row per active employee for a manager report."""
    update_date = update_date or nowdate()
    updates = {
        row.employee: row
        for row in frappe.get_all(
            "RundiNova Daily Update",
            filters={"update_date": update_date},
            fields=[
                "employee",
                "name",
                "primary_task",
                "project",
                "review_status",
                "blocker_status",
                "time_spent_hours",
            ],
        )
    }
    rows = []
    for employee in _active_employees():
        update = updates.get(employee.name)
        rows.append(
            {
                "employee": employee.name,
                "employee_name": employee.employee_name,
                "user": employee.user_id,
                "status": "Missing" if not update else update.review_status,
                "daily_update": update.name if update else None,
                "primary_task": update.primary_task if update else None,
                "project": update.project if update else None,
                "blocker_status": update.blocker_status if update else None,
                "time_spent_hours": update.time_spent_hours if update else None,
            }
        )
    return rows


def _director_user():
    directors = frappe.get_all(
        "Has Role",
        filters={"role": "RundiNova Director", "parenttype": "User"},
        pluck="parent",
    )
    return directors[0] if directors else None


def _ensure_project_field(fieldname, label, fieldtype="Data", options=None):
    if frappe.db.exists("Custom Field", {"dt": "Project", "fieldname": fieldname}):
        return
    doc = {
        "doctype": "Custom Field",
        "dt": "Project",
        "fieldname": fieldname,
        "label": label,
        "fieldtype": fieldtype,
        "insert_after": "rundinova_repository",
        "module": "RundiNova Tech",
    }
    if options:
        doc["options"] = options
    frappe.get_doc(doc).insert(ignore_permissions=True)


def ensure_portfolio_project_fields():
    _ensure_project_field(
        "rundinova_portfolio_status",
        "Portfolio Status",
        "Select",
        "Active\nBacklog\nPaused\nArchived",
    )
    _ensure_project_field("rundinova_business_owner", "Business Owner", "Link", "User")
    _ensure_project_field(
        "rundinova_technical_owner", "Technical Owner", "Link", "User"
    )


@frappe.whitelist()
def seed_rundinova_portfolio(create_initial_tasks=False):
    """Idempotently register the approved 39-project portfolio.

    Only NOVARIS, Imbonakazoza and ComLab are marked Active. The optional task
    flag creates one truthful intake/backlog task per active project; it never
    invents product-delivery work.
    """
    frappe.only_for(("RundiNova Director", "System Manager"))
    ensure_portfolio_project_fields()
    owner = _director_user()
    if not owner:
        frappe.throw(
            _("A RundiNova Director user is required before seeding the portfolio.")
        )
    result = {"created": [], "updated": [], "tasks_created": []}
    for project_name in PORTFOLIO:
        project = frappe.db.exists("Project", {"project_name": project_name})
        values = {
            "rundinova_portfolio_status": (
                "Active" if project_name in ACTIVE_PORTFOLIO else "Backlog"
            ),
            "rundinova_business_owner": owner,
            "rundinova_technical_owner": owner,
        }
        if project:
            frappe.db.set_value("Project", project, values, update_modified=False)
            result["updated"].append(project_name)
        else:
            doc = frappe.get_doc(
                {
                    "doctype": "Project",
                    "project_name": project_name,
                    "status": "Open",
                    "project_manager": owner,
                    **values,
                }
            ).insert(ignore_permissions=True)
            project = doc.name
            result["created"].append(project_name)
        if create_initial_tasks and project_name in ACTIVE_PORTFOLIO:
            subject = (
                "Define product scope, repository links and first delivery backlog"
            )
            if not frappe.db.exists("Task", {"project": project, "subject": subject}):
                frappe.get_doc(
                    {
                        "doctype": "Task",
                        "project": project,
                        "subject": subject,
                        "status": "Open",
                        "priority": "High",
                        "exp_end_date": nowdate(),
                    }
                ).insert(ignore_permissions=True)
                result["tasks_created"].append(project_name)
    frappe.db.commit()
    return result
