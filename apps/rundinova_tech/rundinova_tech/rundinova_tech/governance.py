"""Executive governance schedule, access membership, and reminders."""

from datetime import date, timedelta

import frappe
from frappe.utils import getdate, now_datetime, today


EXECUTIVE_ROLE = "RundiNova Executive Council"
EXECUTIVE_USERS = (
    "joffre.niyondiko@kit-hub.com",
    "chris.igiraneza@kit-hub.com",
    "achbelnkuru@gmail.com",
)
JOFFRE = EXECUTIVE_USERS[0]
CHRIS = EXECUTIVE_USERS[1]
ACHBEL = EXECUTIVE_USERS[2]
FRAMEWORK_START = date(2026, 11, 2)
FRAMEWORK_END = date(2027, 3, 31)


def has_governance_access(user=None):
    """Return whether a user is a member of the executive council."""
    user = user or frappe.session.user
    return user == "Administrator" or EXECUTIVE_ROLE in set(frappe.get_roles(user))


def ensure_executive_council_members():
    """Grant the governance role to the approved accounts without removing roles."""
    changed, missing = [], []
    for user_name in EXECUTIVE_USERS:
        if not frappe.db.exists("User", user_name):
            missing.append(user_name)
            continue
        if EXECUTIVE_ROLE in set(frappe.get_roles(user_name)):
            continue
        user = frappe.get_doc("User", user_name)
        user.append("roles", {"role": EXECUTIVE_ROLE})
        user.save(ignore_permissions=True)
        changed.append(user_name)
    frappe.db.commit()
    return {"granted": changed, "missing": missing}


def _last_friday(year, month):
    if month == 12:
        day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        day = date(year, month + 1, 1) - timedelta(days=1)
    while day.weekday() != 4:
        day -= timedelta(days=1)
    return day


def _ensure_meeting(values):
    existing = frappe.db.exists(
        "RundiNova Governance Meeting", {"meeting_title": values["meeting_title"]}
    )
    if existing:
        return existing, False
    return frappe.get_doc({"doctype": "RundiNova Governance Meeting", **values}).insert(
        ignore_permissions=True
    ).name, True


def _ensure_weekly_report(values):
    existing = frappe.db.exists(
        "RundiNova Weekly Management Report", {"report_title": values["report_title"]}
    )
    if existing:
        return existing, False
    return frappe.get_doc(
        {"doctype": "RundiNova Weekly Management Report", **values}
    ).insert(ignore_permissions=True).name, True


def _weekly_meeting_values(meeting_date, next_date):
    label = meeting_date.strftime("%d/%m/%Y")
    return {
        "meeting_title": f"Direction — {label}",
        "meeting_type": "Réunion hebdomadaire de direction",
        "meeting_date": meeting_date.isoformat(),
        "start_time": "10:00:00",
        "end_time": "11:00:00",
        "chair": CHRIS,
        "secretary": ACHBEL,
        "attendees": "Chris Clément Igiraneza ; Joffre Niyondiko ; Achbel Clara Nkurunziza",
        "agenda": (
            "00–10 min : décisions précédentes et actions en retard.\n"
            "10–25 min : activités, produit et progression commerciale.\n"
            "25–35 min : finances, administration et trésorerie.\n"
            "35–50 min : décisions, risques et priorités.\n"
            "50–60 min : engagements et délais."
        ),
        "next_meeting_date": next_date.isoformat() if next_date else None,
        "status": "Planifiée",
    }


def _month_meeting_values(meeting_date, meeting_type):
    return {
        "meeting_title": f"{meeting_type} — {meeting_date.strftime('%d/%m/%Y')}",
        "meeting_type": meeting_type,
        "meeting_date": meeting_date.isoformat(),
        "start_time": "10:00:00",
        "end_time": "11:30:00",
        "chair": JOFFRE,
        "secretary": ACHBEL,
        "attendees": "Toute l’équipe RundiNova Tech",
        "agenda": (
            "Bilan global, résultats, blocages transversaux, décisions et objectifs du mois suivant."
        ),
        "status": "Planifiée",
    }


def ensure_governance_framework():
    """Create the approved 2 Nov 2026–31 Mar 2027 governance cadence once."""
    membership = ensure_executive_council_members()
    created = {"meetings": 0, "reports": 0, "decision": False}
    folder_name = "Direction & gouvernance"
    if not frappe.db.exists("RundiNova Document Folder", {"folder_name": folder_name}):
        frappe.get_doc(
            {
                "doctype": "RundiNova Document Folder",
                "folder_name": folder_name,
                "folder_owner": JOFFRE,
                "access_scope": "Executive Council",
                "default_confidentiality": "Restricted",
                "status": "Active",
                "description": "Cadre de gestion, procès-verbaux et décisions réservés au Conseil de direction.",
            }
        ).insert(ignore_permissions=True)
    mondays = []
    cursor = FRAMEWORK_START
    while cursor <= FRAMEWORK_END:
        if cursor.weekday() == 0:
            mondays.append(cursor)
        cursor += timedelta(days=1)
    for index, meeting_date in enumerate(mondays):
        next_date = mondays[index + 1] if index + 1 < len(mondays) else None
        _, was_created = _ensure_meeting(_weekly_meeting_values(meeting_date, next_date))
        created["meetings"] += int(was_created)

    for year, month in ((2026, 11), (2026, 12), (2027, 1), (2027, 2), (2027, 3)):
        meeting_date = date(2026, 12, 18) if (year, month) == (2026, 12) else _last_friday(year, month)
        meeting_type = "Bilan trimestriel" if (year, month) == (2027, 3) else "Réunion mensuelle de toute l’équipe"
        _, was_created = _ensure_meeting(_month_meeting_values(meeting_date, meeting_type))
        created["meetings"] += int(was_created)

    cursor = FRAMEWORK_START
    while cursor <= FRAMEWORK_END:
        if cursor.weekday() == 4:
            deadline_date = cursor
            # Christmas Day and New Year's Day reports are submitted on the
            # preceding working day, as adopted in the framework.
            if cursor in (date(2026, 12, 25), date(2027, 1, 1)):
                deadline_date -= timedelta(days=1)
            period_start = cursor - timedelta(days=6)
            for report_type, responsible in (("Opérations", JOFFRE), ("Finances et administration", ACHBEL)):
                title = f"{report_type} — semaine du {cursor.strftime('%d/%m/%Y')}"
                _, was_created = _ensure_weekly_report(
                    {
                        "report_title": title,
                        "report_type": report_type,
                        "responsible": responsible,
                        "report_date": cursor.isoformat(),
                        "period_start": period_start.isoformat(),
                        "period_end": cursor.isoformat(),
                        "submission_deadline": f"{deadline_date.isoformat()} 16:00:00",
                        "status": "À préparer",
                    }
                )
                created["reports"] += int(was_created)
        cursor += timedelta(days=1)

    adoption_title = "Adoption du cadre stratégique de gestion et de redevabilité — novembre 2026 à mars 2027"
    if not frappe.db.exists("RundiNova Decision", {"decision_title": adoption_title}):
        action_subject = "Lancer le cadre de gestion et tenir la première réunion de direction"
        action_task = frappe.db.exists("Task", {"subject": action_subject})
        if not action_task:
            action_task = frappe.get_doc(
                {
                    "doctype": "Task",
                    "subject": action_subject,
                    "description": "Mettre en service le cadre adopté, vérifier les accès de direction et tenir la réunion du 2 novembre 2026.",
                    "exp_end_date": FRAMEWORK_START.isoformat(),
                    "status": "Open",
                    "priority": "High",
                }
            ).insert(ignore_permissions=True).name
        first_meeting = frappe.db.get_value(
            "RundiNova Governance Meeting",
            {"meeting_title": "Direction — 02/11/2026"},
            "name",
        )
        frappe.get_doc(
            {
                "doctype": "RundiNova Decision",
                "decision_title": adoption_title,
                "decision_date": FRAMEWORK_START.isoformat(),
                "decision_type": "Operations",
                "governance_scope": "Executive Council",
                "meeting_reference": first_meeting,
                "decision_text": (
                    "Le Conseil de direction adopte le cadre de gestion interne du 2 novembre 2026 au 31 mars 2027 : réunion de direction le lundi, rapports du vendredi, réunion mensuelle, procès-verbaux, suivi des actions, risques et indicateurs."
                ),
                "decision_owner": JOFFRE,
                "status": "Completed",
                "action_task": action_task,
                "notes": "Adopté par Joffre avec accès de gouvernance réservé à Joffre, Chris Clement et Achbel.",
            }
        ).insert(ignore_permissions=True)
        created["decision"] = True
    frappe.db.commit()
    return {"membership": membership, "created": created}


def _todo_exists(doctype, name, user):
    return frappe.db.exists(
        "ToDo",
        {
            "reference_type": doctype,
            "reference_name": name,
            "allocated_to": user,
            "status": ["!=", "Cancelled"],
        },
    )


def _create_todo(doctype, name, user, due_date, description, priority="High"):
    if _todo_exists(doctype, name, user):
        return False
    frappe.get_doc(
        {
            "doctype": "ToDo",
            "allocated_to": user,
            "reference_type": doctype,
            "reference_name": name,
            "date": due_date,
            "priority": priority,
            "description": description,
        }
    ).insert(ignore_permissions=True)
    return True


def create_governance_reminders():
    """Create in-app reminders for upcoming direction meetings and Friday reports."""
    current = getdate(today())
    next_working_day = current + timedelta(days=1)
    if current.weekday() == 4:
        next_working_day += timedelta(days=2)
    created = 0
    for meeting in frappe.get_all(
        "RundiNova Governance Meeting",
        filters={"meeting_date": next_working_day.isoformat(), "status": "Planifiée"},
        fields=["name", "meeting_title", "meeting_date"],
    ):
        for member in EXECUTIVE_USERS:
            created += int(
                _create_todo(
                    "RundiNova Governance Meeting",
                    meeting.name,
                    member,
                    current.isoformat(),
                    f"Préparer la réunion de direction : {meeting.meeting_title}.",
                )
            )
    for report in frappe.get_all(
        "RundiNova Weekly Management Report",
        filters={"status": "À préparer"},
        fields=["name", "report_title", "responsible", "submission_deadline"],
    ):
        if getdate(report.submission_deadline) != current:
            continue
        created += int(
            _create_todo(
                "RundiNova Weekly Management Report",
                report.name,
                report.responsible,
                current.isoformat(),
                f"Transmettre avant 16 h 00 CAT : {report.report_title}.",
            )
        )
    frappe.db.commit()
    return {"created": created, "date": current.isoformat()}
