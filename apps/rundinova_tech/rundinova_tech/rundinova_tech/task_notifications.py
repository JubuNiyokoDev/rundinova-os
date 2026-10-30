"""In-app collaboration notifications for project tasks."""

import frappe
from frappe.desk.doctype.notification_log.notification_log import make_notification_logs


PROJECT_TEAM_ROLE = "RundiNova Project Contributor"
EXCLUDED_RECIPIENTS = {"achbelnkuru@gmail.com"}
TRACKED_FIELDS = {
    "status": "Statut",
    "rundinova_test_result": "Résultat de recette",
    "rundinova_test_summary": "Résumé de mise à jour",
    "rundinova_test_notes": "Constat / anomalie",
}


def _recipients(exclude_user):
    """Return enabled project contributors, excluding the person who acted."""
    users = frappe.get_all(
        "Has Role",
        filters={"role": PROJECT_TEAM_ROLE, "parenttype": "User"},
        pluck="parent",
    )
    return [
        user
        for user in set(users)
        if user not in EXCLUDED_RECIPIENTS
        and user != exclude_user
        and frappe.db.get_value("User", user, "enabled")
    ]


def _project_label(task):
    return frappe.db.get_value("Project", task.project, "project_name") or task.project


def _send(task, subject, description):
    actor = frappe.session.user
    recipients = _recipients(actor)
    if not recipients:
        return
    make_notification_logs(
        {
            "type": None,
            "subject": subject,
            "title": subject,
            "description": description,
            "document_type": "Task",
            "document_name": task.name,
            "from_user": actor,
        },
        recipients,
    )


def notify_task_created(task, method=None):
    """Notify the project team when a new task is created."""
    project = _project_label(task)
    _send(
        task,
        f"[{project}] Nouvelle tâche",
        f"{task.subject} a été créée par {frappe.session.user}.",
    )


def notify_task_updated(task, method=None):
    """Notify the project team once per meaningful task update."""
    previous = task.get_doc_before_save()
    if not previous:
        return

    changed = [
        label
        for fieldname, label in TRACKED_FIELDS.items()
        if task.meta.has_field(fieldname) and task.get(fieldname) != previous.get(fieldname)
    ]
    if not changed:
        return

    project = _project_label(task)
    _send(
        task,
        f"[{project}] Tâche mise à jour",
        f"{task.subject} : {', '.join(changed)} mis à jour par {frappe.session.user}.",
    )
