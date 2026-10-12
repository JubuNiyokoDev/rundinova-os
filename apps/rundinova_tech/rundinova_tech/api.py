"""Read-only onboarding checks for the RundiNova production setup."""

import json
import os

import frappe


def _require_access_administrator():
    roles = set(frappe.get_roles())
    if not roles.intersection({"System Manager", "RundiNova Director"}):
        frappe.throw(
            "Seuls la direction RundiNova et l’administrateur peuvent gérer les accès.",
            frappe.PermissionError,
        )


@frappe.whitelist()
def get_rundinova_access_directory():
    """Return employee accounts and only their RundiNova role assignments."""
    _require_access_administrator()
    from rundinova_tech.rundinova_tech.access_control import ROLES

    employees = frappe.get_all(
        "Employee",
        filters={"user_id": ["is", "set"]},
        fields=["user_id", "employee_name", "status"],
        order_by="employee_name asc",
    )
    return {
        "roles": sorted(ROLES),
        "users": [
            {
                "user": row.user_id,
                "name": row.employee_name,
                "status": row.status,
                "enabled": bool(frappe.db.get_value("User", row.user_id, "enabled")),
                "roles": sorted(set(frappe.get_roles(row.user_id)).intersection(ROLES)),
            }
            for row in employees
            if frappe.db.exists("User", row.user_id)
        ],
    }


@frappe.whitelist()
def update_rundinova_user_roles(user, roles):
    """Safely change only RundiNova business roles from the setup workspace."""
    _require_access_administrator()
    from rundinova_tech.rundinova_tech.access_control import ROLES
    from rundinova_tech.rundinova_tech.provisioning.workspaces import (
        DEFAULT_WORKSPACE_BY_ROLE,
    )

    if isinstance(roles, str):
        try:
            roles = json.loads(roles)
        except json.JSONDecodeError:
            roles = None
    if (
        not isinstance(roles, list)
        or any(not isinstance(role, str) for role in roles)
        or not set(roles).issubset(set(ROLES))
    ):
        frappe.throw("La liste contient un rôle RundiNova non autorisé.")
    roles = list(dict.fromkeys(roles))
    if not roles:
        frappe.throw("Chaque compte doit garder au moins un rôle RundiNova.")
    if user == "Administrator" or not frappe.db.exists("User", user):
        frappe.throw("Ce compte ne peut pas être modifié depuis cette page.")

    user_doc = frappe.get_doc("User", user)
    if user_doc.user_type != "System User":
        frappe.throw("Seuls les comptes internes peuvent recevoir ces rôles.")
    actor_roles = set(frappe.get_roles())
    current_roles = {row.role for row in user_doc.roles}
    if not actor_roles.intersection({"System Manager"}) and current_roles.intersection(
        {"System Manager", "Workspace Manager"}
    ):
        frappe.throw("Un administrateur système doit gérer ce compte.", frappe.PermissionError)

    if (
        user == frappe.session.user
        and "RundiNova Director" in actor_roles
        and "RundiNova Director" not in roles
    ):
        frappe.throw("Vous ne pouvez pas retirer votre propre accès de direction.")
    if "RundiNova Director" in current_roles and "RundiNova Director" not in roles:
        other_directors = [
            account
            for account in frappe.get_all(
                "User",
                filters={"user_type": "System User", "enabled": 1},
                pluck="name",
            )
            if account != user and "RundiNova Director" in frappe.get_roles(account)
        ]
        if not other_directors:
            frappe.throw("Au moins un compte de direction doit rester actif.")

    user_doc.set(
        "roles",
        [row for row in user_doc.roles if row.role not in set(ROLES)]
        + [{"role": role} for role in roles],
    )
    default_workspace = next(
        (workspace for role, workspace in DEFAULT_WORKSPACE_BY_ROLE if role in roles),
        None,
    )
    if default_workspace:
        user_doc.default_workspace = default_workspace
    user_doc.save(ignore_permissions=True)
    frappe.clear_cache(user=user)
    return {"user": user, "roles": sorted(roles), "default_workspace": default_workspace}


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
    """Generate a read-only AI review and save it on an authorized repo."""
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
            "Analyse non terminée. Vérifier la configuration GitHub/IA "
            f"et relancer. Type d’erreur : {type(exc).__name__}."
        )
        doc.save()
        frappe.log_error(title="RundiNova AI analysis failed", message=str(exc))
        error = str(exc)
        if "HTTP 401" in error or "HTTP 403" in error:
            message = "La clé du fournisseur IA est refusée. Vérifiez le fournisseur et la clé configurés côté serveur."
        elif "HTTP 429" in error:
            message = "Le fournisseur IA a atteint sa limite temporaire. Réessayez plus tard."
        else:
            message = "L’analyse IA n’a pas abouti. Vérifiez son statut et la configuration du fournisseur, puis réessayez."
        return {"ok": False, "message": message}

    doc.custom_ai_review = render_markdown(report)
    doc.custom_ai_review_status = "Complete"
    doc.custom_ai_reviewed_on = frappe.utils.now_datetime()
    doc.save()
    return {"ok": True, **report}


@frappe.whitelist()
def analyze_github_account(owner):
    """Queue a human-approved, read-only AI analysis of installed repositories."""
    from rundinova_tech.github_sync import fetch_installation_repositories

    if "RundiNova Director" not in frappe.get_roles():
        frappe.throw(
            "Only a RundiNova Director can start an account-wide analysis.",
            frappe.PermissionError,
        )
    provider = os.environ.get("RUNDINOVA_AI_PROVIDER", "gemini").strip().lower()
    api_key = (
        os.environ.get("COHERE_API_KEY", "")
        if provider == "cohere"
        else os.environ.get("RUNDINOVA_GEMINI_API_KEY", "")
    )
    if not api_key.strip():
        frappe.throw(f"Le fournisseur IA {provider} n’est pas configuré sur ce serveur.")

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
            "Analyse non terminée. Vérifier la configuration GitHub/IA "
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
