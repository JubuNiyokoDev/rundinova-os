"""Read-only onboarding checks for the RundiNova production setup."""

import html
import os

import frappe


@frappe.whitelist()
def get_onboarding_status():
    """Return a safe, non-sensitive readiness summary.

    This endpoint never creates or changes business data. It is intended for
    the administrator's first-run checklist before production use.
    """
    checks = []

    def check(key, label, ready, detail):
        checks.append(
            {"key": key, "label": label, "ready": bool(ready), "detail": detail}
        )

    company_count = frappe.db.count("Company")
    check(
        "company",
        "Company configured",
        company_count > 0,
        f"{company_count} company record(s)",
    )

    user_count = frappe.db.count("User", {"enabled": 1, "user_type": "System User"})
    check(
        "users",
        "Active system users",
        user_count >= 1,
        f"{user_count} active system user(s)",
    )

    employee_count = frappe.db.count("Employee", {"status": "Active"})
    check(
        "employees",
        "Active employees",
        employee_count >= 1,
        f"{employee_count} active employee(s)",
    )

    project_count = frappe.db.count("Project", {"status": ["!=", "Cancelled"]})
    check(
        "projects",
        "First project",
        project_count >= 1,
        f"{project_count} active project record(s)",
    )

    task_count = frappe.db.count(
        "Task", {"status": ["not in", ["Completed", "Cancelled"]]}
    )
    check("tasks", "Open work tracking", task_count >= 1, f"{task_count} open task(s)")

    repository_count = frappe.db.count("RundiNova Repository")
    check(
        "repositories",
        "GitHub repositories",
        repository_count >= 1,
        f"{repository_count} repository record(s)",
    )

    expense_count = frappe.db.count("RundiNova Expense")
    check(
        "expenses",
        "General expense tracking",
        expense_count >= 1,
        f"{expense_count} expense record(s)",
    )

    asset_count = frappe.db.count("RundiNova Asset")
    check(
        "assets", "Asset register", asset_count >= 1, f"{asset_count} asset record(s)"
    )

    cash_account_count = frappe.db.count("RundiNova Cash Account", {"status": "Active"})
    check(
        "cash_accounts",
        "Cash accounts",
        cash_account_count >= 1,
        f"{cash_account_count} active cash account(s)",
    )

    movement_count = frappe.db.count(
        "RundiNova Cash Movement", {"status": ["in", ["Approved", "Reconciled"]]}
    )
    check(
        "cash_movements",
        "Approved cash movements",
        movement_count >= 1,
        f"{movement_count} approved movement(s)",
    )

    decision_count = frappe.db.count("RundiNova Decision")
    check(
        "decisions",
        "Internal decision log",
        decision_count >= 1,
        f"{decision_count} decision record(s)",
    )

    document_count = frappe.db.count("RundiNova Document", {"status": "Active"})
    check(
        "documents",
        "Document register",
        document_count >= 1,
        f"{document_count} active document(s)",
    )

    goal_count = frappe.db.count("RundiNova Goal")
    check("goals", "Goals and KPIs", goal_count >= 1, f"{goal_count} goal record(s)")

    budget_count = frappe.db.count("RundiNova Food Budget")
    check(
        "food_budget",
        "Food budget",
        budget_count >= 1,
        f"{budget_count} budget record(s)",
    )

    check(
        "roles",
        "RundiNova roles",
        frappe.db.count("Role", {"role_name": ["like", "RundiNova %"]}) >= 5,
        "Five named roles are expected",
    )

    ready = all(item["ready"] for item in checks)
    return {"ready": ready, "checks": checks}


@frappe.whitelist()
def sync_repository(repository_name):
    """Trigger a read-only GitHub sync for a single repository."""
    doc = frappe.get_doc("RundiNova Repository", repository_name)
    return doc.sync_from_github()


@frappe.whitelist()
def sync_all_repositories():
    """Trigger a read-only GitHub sync for all active repositories."""
    repos = frappe.get_all(
        "RundiNova Repository", filters={"status": "Active"}, pluck="name"
    )
    results = []
    for name in repos:
        try:
            doc = frappe.get_doc("RundiNova Repository", name)
            doc.sync_from_github()
            results.append({"repository": name, "status": "ok"})
        # Continue the sync batch when any single repository fails.
        except Exception as exc:  # noqa: BLE001
            results.append({"repository": name, "status": "error", "message": str(exc)})
    return results


@frappe.whitelist()
def analyze_repository(repository_name):
    """Generate a read-only Gemini review and save it on an authorized repo."""
    doc = frappe.get_doc("RundiNova Repository", repository_name)
    if not frappe.has_permission("RundiNova Repository", "write", doc):
        frappe.throw(
            "You need write access to save an AI review.", frappe.PermissionError
        )

    from rundinova_tech.ai_review import render_markdown, review_repository
    from rundinova_tech.github_sync import fetch_repository_source_context
    from rundinova_tech.github_sync import sync_repository as fetch_metadata

    doc.custom_ai_review_status = "Analyzing"
    doc.save()
    try:
        info = fetch_metadata(doc.github_url)
        source = fetch_repository_source_context(
            info["owner"], info["repo"], info["default_branch"]
        )
        report = review_repository(info, source, info.get("recent_commits", []))
    # Save a visible failure state even when the upstream API returns an
    # unexpected error.
    except Exception as exc:  # noqa: BLE001
        doc.custom_ai_review_status = "Failed"
        doc.custom_ai_review = (
            "Analyse non terminée. Vérifier la configuration GitHub/Gemini "
            f"et relancer. Type d’erreur : {type(exc).__name__}."
        )
        doc.save()
        frappe.throw(f"AI analysis failed: {html.escape(str(exc))}")

    doc.custom_ai_review = render_markdown(report)
    doc.custom_ai_review_status = "Complete"
    doc.custom_ai_reviewed_on = frappe.utils.now_datetime()
    doc.save()
    return report


@frappe.whitelist()
def analyze_github_account(owner):
    """Queue a human-approved, read-only AI analysis of installed repositories."""
    from rundinova_tech.github_sync import fetch_installation_repositories

    if "RundiNova Director" not in frappe.get_roles():
        frappe.throw(
            "Only a RundiNova Director can start an account-wide analysis.",
            frappe.PermissionError,
        )
    if not os.environ.get("RUNDINOVA_GEMINI_API_KEY", "").strip():
        frappe.throw("Gemini AI is not configured on this deployment.")

    # Check the GitHub installation before queuing a potentially long job.
    repositories = fetch_installation_repositories(owner)
    from rundinova_tech.github_sync import parse_github_url

    existing = {}
    for entry in frappe.get_all("RundiNova Repository", fields=["name", "github_url"]):
        parsed = parse_github_url(entry.github_url)
        if parsed:
            existing[tuple(part.lower() for part in parsed)] = entry.name

    jobs = []
    already_running = 0
    for repository in repositories:
        parsed = parse_github_url(repository["html_url"])
        if not parsed:
            continue
        key = tuple(part.lower() for part in parsed)
        name = existing.get(key)
        if name:
            doc = frappe.get_doc("RundiNova Repository", name)
            if doc.custom_ai_review_status in {"Queued", "Analyzing"}:
                already_running += 1
                continue
        else:
            doc = frappe.get_doc(
                {
                    "doctype": "RundiNova Repository",
                    "repository_name": repository["full_name"],
                    "github_url": repository["html_url"],
                    "repository_type": "Other",
                    "status": "Active",
                    "project_stage": "Discovery",
                    "custom_ai_review_status": "Queued",
                }
            )
            doc.insert(ignore_permissions=True)
            existing[key] = doc.name
        doc.custom_ai_review_status = "Queued"
        doc.save(ignore_permissions=True)
        frappe.enqueue(
            "rundinova_tech.api._analyze_github_repository_job",
            queue="long",
            timeout=900,
            repository_name=doc.name,
            requested_by=frappe.session.user,
            enqueue_after_commit=True,
        )
        jobs.append(doc.name)
    return {"repository_count": len(jobs), "already_running": already_running}


def _analyze_github_repository_job(repository_name, requested_by):
    """Analyze one installed repository; account scans fan out into these jobs."""
    from rundinova_tech.ai_review import render_markdown, review_repository
    from rundinova_tech.github_sync import fetch_repository_source_context
    from rundinova_tech.github_sync import sync_repository as fetch_metadata

    doc = frappe.get_doc("RundiNova Repository", repository_name)
    doc.custom_ai_review_status = "Analyzing"
    doc.save(ignore_permissions=True)
    try:
        info = fetch_metadata(doc.github_url)
        source = fetch_repository_source_context(
            info["owner"],
            info["repo"],
            info["default_branch"],
            max_files=30,
            max_chars=75_000,
        )
        report = review_repository(info, source, info.get("recent_commits", []))
        doc.custom_ai_review = render_markdown(report)
        doc.custom_ai_review_status = "Complete"
        doc.custom_ai_reviewed_on = frappe.utils.now_datetime()
        doc.open_issues_count = info.get("open_issues_count", 0)
        doc.stargazers_count = info.get("stargazers_count", 0)
        doc.forks_count = info.get("forks_count", 0)
        doc.default_branch = info.get("default_branch", "")
        doc.primary_language = info.get("language", "")
        from rundinova_tech.rundinova_tech.doctype.rundinova_repository.rundinova_repository import (
            _github_datetime,
        )

        doc.last_push_date = _github_datetime(info.get("pushed_at"))
        doc.last_synced_on = frappe.utils.now_datetime()
        doc.save(ignore_permissions=True)
        result = "complete"
    # Each queued job records its own failure and leaves sibling jobs running.
    except Exception as exc:  # noqa: BLE001
        doc.custom_ai_review_status = "Failed"
        doc.custom_ai_review = (
            "Analyse non terminée. Vérifier la configuration GitHub/Gemini "
            f"et relancer. Type d’erreur : {type(exc).__name__}."
        )
        doc.save(ignore_permissions=True)
        result = "failed"

    frappe.publish_realtime(
        "rundinova_account_ai_progress",
        {"repository": doc.repository_name, "status": result},
        user=requested_by,
    )
    return {"repository": doc.name, "status": result}
