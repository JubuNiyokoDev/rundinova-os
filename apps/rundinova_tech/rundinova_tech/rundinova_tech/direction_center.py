"""Read model for the executive direction centre."""

import frappe
from frappe import _
from frappe.utils import add_days, get_datetime, getdate, now_datetime, today

from .governance import has_governance_access


def _require_council():
    if not has_governance_access():
        frappe.throw(_("Only the Executive Council can access this centre."), frappe.PermissionError)


def _event_date(value):
    return getdate(value).isoformat() if value else None


@frappe.whitelist()
def get_direction_overview():
    """Return a compact, permission-checked 30-day direction workboard."""
    _require_council()
    start = getdate(today())
    end = add_days(start, 30)
    week_end = add_days(start, 6)
    now = now_datetime()

    meetings = frappe.get_all(
        "RundiNova Governance Meeting",
        filters={"meeting_date": ["between", [start, end]], "status": "Planifiée"},
        fields=[
            "name",
            "meeting_title",
            "meeting_type",
            "meeting_date",
            "start_time",
            "end_time",
            "chair",
            "secretary",
            "minutes_status",
            "status",
        ],
        order_by="meeting_date asc, start_time asc",
        limit_page_length=60,
    )
    reports = frappe.get_all(
        "RundiNova Weekly Management Report",
        filters={"submission_deadline": ["between", [start, f"{end} 23:59:59"]]},
        fields=[
            "name",
            "report_title",
            "report_type",
            "responsible",
            "report_date",
            "submission_deadline",
            "status",
        ],
        order_by="submission_deadline asc",
        limit_page_length=80,
    )
    due_this_week = [
        report
        for report in reports
        if getdate(report.submission_deadline) <= week_end
        and report.status in ("À préparer", "À corriger")
    ]
    overdue = [
        report
        for report in frappe.get_all(
            "RundiNova Weekly Management Report",
            filters={"status": ["in", ["À préparer", "À corriger"]]},
            fields=["name", "submission_deadline"],
            limit_page_length=200,
        )
        if report.submission_deadline and get_datetime(report.submission_deadline) < now
    ]
    decisions_open = frappe.db.count(
        "RundiNova Decision",
        {"governance_scope": "Executive Council", "status": ["in", ["Open", "In Progress"]]},
    )
    risks_open = frappe.db.count("RundiNova Risk", {"status": ["in", ["Open", "Monitoring"]]})
    decisions = frappe.get_all(
        "RundiNova Decision",
        filters={"governance_scope": "Executive Council"},
        fields=["name", "decision_title", "decision_date", "decision_owner", "follow_up_date", "status"],
        order_by="decision_date desc",
        limit_page_length=20,
    )
    risks = frappe.get_all(
        "RundiNova Risk",
        filters={"status": ["in", ["Open", "Monitoring"]]},
        fields=["name", "risk_title", "area", "risk_owner", "impact", "review_date", "status"],
        order_by="review_date asc, modified desc",
        limit_page_length=20,
    )

    events = []
    for meeting in meetings:
        events.append(
            {
                "kind": "meeting",
                "date": _event_date(meeting.meeting_date),
                "name": meeting.name,
                "title": meeting.meeting_title,
                "subtitle": f"{meeting.meeting_type} · {meeting.start_time or '—'}–{meeting.end_time or '—'} CAT",
                "status": meeting.status,
                "doctype": "RundiNova Governance Meeting",
            }
        )
    for report in reports:
        events.append(
            {
                "kind": "report",
                "date": _event_date(report.submission_deadline),
                "name": report.name,
                "title": report.report_title,
                "subtitle": f"À transmettre avant 16 h CAT · {report.responsible}",
                "status": report.status,
                "doctype": "RundiNova Weekly Management Report",
            }
        )
    events.sort(key=lambda event: (event["date"], 0 if event["kind"] == "meeting" else 1))
    next_meeting = meetings[0] if meetings else None
    return {
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "next_meeting": next_meeting,
        "summary": {
            "reports_due_this_week": len(due_this_week),
            "overdue_reports": len(overdue),
            "open_decisions": decisions_open,
            "open_risks": risks_open,
        },
        "events": events,
        "meetings": meetings,
        "reports": reports,
        "reports_due_this_week": due_this_week,
        "decisions": decisions,
        "risks": risks,
    }
