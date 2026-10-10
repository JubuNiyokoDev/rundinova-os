import json

import frappe
from rundinova_core.currency import currency_for_field

from ..access_control import ROLES
from .fields import (
    backfill_budget_titles,
    ensure_project_repository_field,
    ensure_purchase_invoice_budget_field,
    ensure_task_repository_field,
)
from .permissions import ensure_crm_app_access_roles, ensure_rundinova_permissions
from .workspaces import sync_workspaces


def _ensure_number_card(
    name,
    label,
    document_type,
    function="Count",
    report_field=None,
    filters=None,
    color=None,
    background_color=None,
):
    values = {
        "label": label,
        "type": "Document Type",
        "function": function,
        "document_type": document_type,
        "aggregate_function_based_on": report_field,
        "filters_json": json.dumps(filters or []),
        "is_public": 1,
        "show_full_number": 1,
        "color": color,
        "background_color": background_color,
        "module": "RundiNova Tech",
    }
    existing = frappe.db.get_value(
        "Number Card", {"module": "RundiNova Tech", "label": label}, "name"
    ) or (name if frappe.db.exists("Number Card", name) else None)
    if existing:
        doc = frappe.get_doc("Number Card", existing)
        doc.update(values)
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.get_doc({"doctype": "Number Card", "name": name, **values})
        doc.insert(ignore_permissions=True)
    return doc.name


def _ensure_chart(
    name,
    chart_name,
    chart_type,
    document_type,
    chart_kind,
    group_by=None,
    group_by_type="Count",
    based_on=None,
    value_based_on=None,
    filters=None,
    timeseries=False,
    time_interval="Monthly",
):
    values = {
        "chart_name": chart_name,
        "chart_type": chart_type,
        "document_type": document_type,
        "group_by_type": group_by_type,
        "group_by_based_on": group_by,
        "based_on": based_on,
        "value_based_on": value_based_on,
        "aggregate_function_based_on": value_based_on,
        "type": chart_kind,
        "timeseries": 1 if timeseries else 0,
        "time_interval": time_interval,
        "filters_json": json.dumps(filters or []),
        "is_public": 1,
        "module": "RundiNova Tech",
    }
    existing = (
        frappe.db.get_value(
            "Dashboard Chart",
            {"module": "RundiNova Tech", "chart_name": chart_name},
            "name",
        )
        or frappe.db.get_value("Dashboard Chart", {"chart_name": chart_name}, "name")
        or (name if frappe.db.exists("Dashboard Chart", name) else None)
    )
    if existing:
        doc = frappe.get_doc("Dashboard Chart", existing)
        if doc.chart_type != chart_type:
            # Frappe treats chart_type as immutable after creation. These
            # app-owned charts are intentionally migrated between native
            # aggregation modes, so update this one field before normal save.
            frappe.db.set_value("Dashboard Chart", existing, "chart_type", chart_type)
            doc.reload()
        doc.update(values)
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.get_doc({"doctype": "Dashboard Chart", "name": name, **values})
        doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
        if frappe.db.exists("Dashboard Chart", doc.name):
            doc = frappe.get_doc("Dashboard Chart", doc.name)
            doc.update(values)
            doc.save(ignore_permissions=True)
    return doc.name


def _dashboard(name, charts, cards):
    doc = (
        frappe.get_doc("Dashboard", name)
        if frappe.db.exists("Dashboard", name)
        else frappe.new_doc("Dashboard")
    )
    doc.name = name
    doc.dashboard_name = name
    doc.module = "RundiNova Tech"
    doc.is_standard = 0
    doc.charts = []
    for chart, width in charts:
        doc.append("charts", {"chart": chart, "width": width})
    doc.cards = []
    for card in cards:
        doc.append("cards", {"card": card})
    doc.save(ignore_permissions=True)


def sync_dashboard_currencies():
    """Format only monetary dashboard values as BIF, never counts or ratios."""
    updated = {}
    for doctype, fieldname in (
        ("Number Card", "aggregate_function_based_on"),
        ("Dashboard Chart", "value_based_on"),
    ):
        updated[doctype] = 0
        names = frappe.get_all(
            doctype,
            filters={"module": "RundiNova Tech"},
            pluck="name",
        )
        for name in names:
            doc = frappe.get_doc(doctype, name)
            currency = currency_for_field(doc.get(fieldname))
            if doc.currency != currency:
                doc.currency = currency
                doc.save(ignore_permissions=True)
                updated[doctype] += 1
    return updated


def sync_dashboards():
    """Provision rich, clickable dashboards and the branded app workspace."""
    ensure_rundinova_permissions()
    ensure_purchase_invoice_budget_field()
    ensure_task_repository_field()
    ensure_project_repository_field()
    backfill_budget_titles()
    cards = {
        "employees": _ensure_number_card(
            "RundiNova Active Employees",
            "Employés actifs",
            "Employee",
            filters=[["Employee", "status", "=", "Active"]],
            color="#2563EB",
            background_color="#EFF6FF",
        ),
        "budgets": _ensure_number_card(
            "RundiNova Food Budgets",
            "Budgets alimentaires",
            "RundiNova Food Budget",
            color="#0F766E",
            background_color="#ECFDF5",
        ),
        "planned": _ensure_number_card(
            "RundiNova Planned Budget",
            "Budget planifié",
            "RundiNova Food Budget",
            "Sum",
            "total_planned_amount",
            color="#7C3AED",
            background_color="#F5F3FF",
        ),
        "committed": _ensure_number_card(
            "RundiNova Committed Food Spend",
            "Dépenses engagées",
            "RundiNova Food Expense",
            "Sum",
            "amount",
            filters=[
                [
                    "RundiNova Food Expense",
                    "status",
                    "in",
                    ["Submitted", "Approved", "Paid"],
                ]
            ],
            color="#EA580C",
            background_color="#FFF7ED",
        ),
        "actual": _ensure_number_card(
            "RundiNova Actual Food Spend",
            "Dépenses payées",
            "RundiNova Food Expense",
            "Sum",
            "amount",
            filters=[["RundiNova Food Expense", "status", "=", "Paid"]],
            color="#B91C1C",
            background_color="#FEF2F2",
        ),
        "remaining": _ensure_number_card(
            "RundiNova Food Budget Remaining",
            "Solde alimentaire",
            "RundiNova Food Budget",
            "Sum",
            "balance_amount",
            color="#059669",
            background_color="#ECFDF5",
        ),
        "risks": _ensure_number_card(
            "RundiNova Open Risks",
            "Risques ouverts",
            "RundiNova Risk",
            filters=[["RundiNova Risk", "status", "in", ["Open", "Monitoring"]]],
            color="#DC2626",
            background_color="#FEF2F2",
        ),
        "opportunities": _ensure_number_card(
            "RundiNova Opportunities",
            "Opportunités",
            "RundiNova Growth Opportunity",
            color="#D97706",
            background_color="#FFFBEB",
        ),
        "pipeline": _ensure_number_card(
            "RundiNova Pipeline Value",
            "Valeur du pipeline (FBu)",
            "RundiNova Growth Opportunity",
            "Sum",
            "expected_value",
            color="#0891B2",
            background_color="#ECFEFF",
        ),
        "partnerships": _ensure_number_card(
            "RundiNova Partnerships",
            "Partenariats actifs",
            "RundiNova Partnership",
            filters=[["RundiNova Partnership", "status", "=", "Active"]],
            color="#DB2777",
            background_color="#FDF2F8",
        ),
        "kpis": _ensure_number_card(
            "RundiNova KPI Snapshots",
            "Mesures KPI",
            "RundiNova KPI Snapshot",
            color="#4F46E5",
            background_color="#EEF2FF",
        ),
        "repositories": _ensure_number_card(
            "RundiNova Active Repositories",
            "Dépôts actifs",
            "RundiNova Repository",
            filters=[["RundiNova Repository", "status", "=", "Active"]],
            color="#111827",
            background_color="#F3F4F6",
        ),
        "cash_accounts": _ensure_number_card(
            "RundiNova Active Cash Accounts",
            "Comptes actifs",
            "RundiNova Cash Account",
            filters=[["RundiNova Cash Account", "status", "=", "Active"]],
            color="#1D4ED8",
            background_color="#EFF6FF",
        ),
        "cash_balance": _ensure_number_card(
            "RundiNova Cash Balance",
            "Solde de trésorerie",
            "RundiNova Cash Account",
            "Sum",
            "current_balance",
            filters=[["RundiNova Cash Account", "status", "=", "Active"]],
            color="#047857",
            background_color="#ECFDF5",
        ),
        "cash_movements": _ensure_number_card(
            "RundiNova Approved Cash Movements",
            "Mouvements approuvés",
            "RundiNova Cash Movement",
            "Sum",
            "amount",
            filters=[
                ["RundiNova Cash Movement", "status", "in", ["Approved", "Reconciled"]]
            ],
            color="#7C3AED",
            background_color="#F5F3FF",
        ),
        "projects": _ensure_number_card(
            "RundiNova Active Projects",
            "Projets actifs",
            "Project",
            filters=[["Project", "status", "!=", "Cancelled"]],
            color="#2563EB",
            background_color="#EFF6FF",
        ),
        "open_tasks": _ensure_number_card(
            "RundiNova Open Tasks",
            "Tâches ouvertes",
            "Task",
            filters=[["Task", "status", "not in", ["Completed", "Cancelled"]]],
            color="#D97706",
            background_color="#FFFBEB",
        ),
        "completed_tasks": _ensure_number_card(
            "RundiNova Completed Tasks",
            "Tâches terminées",
            "Task",
            filters=[["Task", "status", "=", "Completed"]],
            color="#059669",
            background_color="#ECFDF5",
        ),
        "overdue_tasks": _ensure_number_card(
            "RundiNova Overdue Tasks",
            "Tâches en retard",
            "Task",
            filters=[
                ["Task", "status", "not in", ["Completed", "Cancelled"]],
                ["Task", "exp_end_date", "<", "Today"],
            ],
            color="#DC2626",
            background_color="#FEF2F2",
        ),
        "goals": _ensure_number_card(
            "RundiNova Active Goals",
            "Objectifs actifs",
            "RundiNova Goal",
            filters=[
                ["RundiNova Goal", "status", "in", ["Planned", "Active", "At Risk"]]
            ],
            color="#4F46E5",
            background_color="#EEF2FF",
        ),
        "goals_achieved": _ensure_number_card(
            "RundiNova Achieved Goals",
            "Objectifs atteints",
            "RundiNova Goal",
            filters=[["RundiNova Goal", "status", "=", "Achieved"]],
            color="#059669",
            background_color="#ECFDF5",
        ),
        "goals_at_risk": _ensure_number_card(
            "RundiNova Goals At Risk",
            "Objectifs à risque",
            "RundiNova Goal",
            filters=[["RundiNova Goal", "status", "=", "At Risk"]],
            color="#DC2626",
            background_color="#FEF2F2",
        ),
        "repositories_development": _ensure_number_card(
            "RundiNova Repositories in Development",
            "Dépôts en développement",
            "RundiNova Repository",
            filters=[
                ["RundiNova Repository", "project_stage", "=", "Development"],
                ["RundiNova Repository", "status", "=", "Active"],
            ],
            color="#3B82F6",
            background_color="#EFF6FF",
        ),
        "repositories_high_risk": _ensure_number_card(
            "RundiNova High Risk Repositories",
            "Dépôts à haut risque",
            "RundiNova Repository",
            filters=[
                ["RundiNova Repository", "risk_level", "in", ["High", "Critical"]],
                ["RundiNova Repository", "status", "=", "Active"],
            ],
            color="#DC2626",
            background_color="#FEF2F2",
        ),
        "repositories_critical": _ensure_number_card(
            "RundiNova Critical Priority Repositories",
            "Dépôts priorité critique",
            "RundiNova Repository",
            filters=[
                ["RundiNova Repository", "priority", "=", "Critical"],
                ["RundiNova Repository", "status", "=", "Active"],
            ],
            color="#7C3AED",
            background_color="#F5F3FF",
        ),
    }
    charts = {
        "employees_branch": _ensure_chart(
            "RundiNova Employees by Branch",
            "Employés par bureau",
            "Group By",
            "Employee",
            "Donut",
            group_by="branch",
            filters=[["Employee", "status", "=", "Active"]],
        ),
        "employees_department": _ensure_chart(
            "RundiNova Employees by Department",
            "Employés par département",
            "Group By",
            "Employee",
            "Bar",
            group_by="department",
            filters=[["Employee", "status", "=", "Active"]],
        ),
        "budget_branch": _ensure_chart(
            "RundiNova Budgets by Branch",
            "Budgets par bureau",
            "Group By",
            "RundiNova Food Budget",
            "Bar",
            group_by="branch",
        ),
        "budget_trend": _ensure_chart(
            "RundiNova Budget Trend",
            "Évolution du budget planifié",
            "Sum",
            "RundiNova Food Budget",
            "Line",
            based_on="period_start",
            value_based_on="total_planned_amount",
            timeseries=True,
        ),
        "expense_trend": _ensure_chart(
            "RundiNova Food Expense Trend",
            "Consommation alimentaire quotidienne",
            "Sum",
            "RundiNova Food Expense",
            "Line",
            based_on="expense_date",
            value_based_on="amount",
            filters=[
                [
                    "RundiNova Food Expense",
                    "status",
                    "in",
                    ["Submitted", "Approved", "Paid"],
                ]
            ],
            timeseries=True,
            time_interval="Daily",
        ),
        "food_progress": _ensure_chart(
            "RundiNova Food Progress",
            "Budget consommé par aliment (%)",
            "Group By",
            "RundiNova Food Progress",
            "Bar",
            group_by="item",
            group_by_type="Average",
            value_based_on="consumed_percent",
        ),
        "food_status": _ensure_chart(
            "RundiNova Food Status",
            "Statut des aliments",
            "Group By",
            "RundiNova Food Progress",
            "Donut",
            group_by="status",
        ),
        "risk_status": _ensure_chart(
            "RundiNova Risks by Status",
            "Risques par statut",
            "Group By",
            "RundiNova Risk",
            "Donut",
            group_by="status",
        ),
        "risk_impact": _ensure_chart(
            "RundiNova Risks by Impact",
            "Risques par impact",
            "Group By",
            "RundiNova Risk",
            "Bar",
            group_by="impact",
        ),
        "opportunity_stage": _ensure_chart(
            "RundiNova Opportunities by Stage",
            "Opportunités par étape",
            "Group By",
            "RundiNova Growth Opportunity",
            "Bar",
            group_by="stage",
        ),
        "opportunity_trend": _ensure_chart(
            "RundiNova KPI Trend",
            "Tendance des résultats KPI",
            "Average",
            "RundiNova KPI Snapshot",
            "Line",
            based_on="period_start",
            value_based_on="target_achievement_percent",
            timeseries=True,
        ),
        "partnership_status": _ensure_chart(
            "RundiNova Partnerships by Status",
            "Partenariats par statut",
            "Group By",
            "RundiNova Partnership",
            "Donut",
            group_by="status",
        ),
        "community_status": _ensure_chart(
            "RundiNova Community Activities",
            "Activités communautaires",
            "Group By",
            "RundiNova Community Impact",
            "Bar",
            group_by="status",
        ),
        # Finance Dashboard - Additional Charts
        "cash_movement_trend": _ensure_chart(
            "RundiNova Cash Movement Trend",
            "Mouvements de trésorerie",
            "Sum",
            "RundiNova Cash Movement",
            "Line",
            based_on="movement_date",
            value_based_on="amount",
            filters=[
                ["RundiNova Cash Movement", "status", "in", ["Approved", "Reconciled"]]
            ],
            timeseries=True,
            time_interval="Daily",
        ),
        "cash_movement_type": _ensure_chart(
            "RundiNova Cash Movement by Type",
            "Mouvements par type",
            "Group By",
            "RundiNova Cash Movement",
            "Pie",
            group_by="movement_type",
            filters=[
                ["RundiNova Cash Movement", "status", "in", ["Approved", "Reconciled"]]
            ],
        ),
        "cash_movement_category": _ensure_chart(
            "RundiNova Cash Movement by Category",
            "Mouvements par catégorie",
            "Group By",
            "RundiNova Cash Movement",
            "Bar",
            group_by="category",
            filters=[
                ["RundiNova Cash Movement", "status", "in", ["Approved", "Reconciled"]]
            ],
        ),
        "cash_movement_source": _ensure_chart(
            "RundiNova Cash Movement by Source",
            "Mouvements par source",
            "Group By",
            "RundiNova Cash Movement",
            "Donut",
            group_by="source_type",
            filters=[
                ["RundiNova Cash Movement", "status", "in", ["Approved", "Reconciled"]]
            ],
        ),
        "cash_account_balance": _ensure_chart(
            "RundiNova Cash Account Balance",
            "Solde par compte",
            "Group By",
            "RundiNova Cash Account",
            "Bar",
            group_by="account_name",
            group_by_type="Sum",
            value_based_on="current_balance",
            filters=[["RundiNova Cash Account", "status", "=", "Active"]],
        ),
        "general_expense_trend": _ensure_chart(
            "RundiNova General Expense Trend",
            "Dépenses générales",
            "Sum",
            "RundiNova Expense",
            "Line",
            based_on="expense_date",
            value_based_on="amount",
            filters=[
                ["RundiNova Expense", "status", "in", ["Submitted", "Approved", "Paid"]]
            ],
            timeseries=True,
            time_interval="Daily",
        ),
        "general_expense_category": _ensure_chart(
            "RundiNova General Expense by Category",
            "Dépenses générales par catégorie",
            "Group By",
            "RundiNova Expense",
            "Donut",
            group_by="category",
            filters=[
                ["RundiNova Expense", "status", "in", ["Submitted", "Approved", "Paid"]]
            ],
        ),
        "budget_consumption": _ensure_chart(
            "RundiNova Budget Consumption",
            "Budget consommé par période (%)",
            "Group By",
            "RundiNova Food Budget",
            "Bar",
            group_by="budget_title",
            group_by_type="Average",
            value_based_on="consumed_percent",
        ),
        "expense_vs_budget": _ensure_chart(
            "RundiNova Expense vs Budget",
            "Dépenses vs Budget",
            "Sum",
            "RundiNova Food Budget",
            "Line",
            based_on="period_start",
            value_based_on="actual_amount",
            timeseries=True,
        ),
        "asset_value": _ensure_chart(
            "RundiNova Asset Value by Category",
            "Valeur des actifs par catégorie",
            "Group By",
            "RundiNova Asset",
            "Bar",
            group_by="asset_type",
            group_by_type="Sum",
            value_based_on="current_value",
            filters=[["RundiNova Asset", "status", "=", "Active"]],
        ),
        "asset_status": _ensure_chart(
            "RundiNova Asset Status",
            "Statut des actifs",
            "Group By",
            "RundiNova Asset",
            "Pie",
            group_by="status",
        ),
        # Executive Dashboard - Additional Charts
        "goal_progress": _ensure_chart(
            "RundiNova Goal Progress",
            "Progression moyenne des objectifs (%)",
            "Group By",
            "RundiNova Goal",
            "Bar",
            group_by="goal_title",
            group_by_type="Average",
            value_based_on="achievement_percent",
            filters=[
                ["RundiNova Goal", "status", "in", ["Planned", "Active", "At Risk"]]
            ],
        ),
        "kpi_achievement": _ensure_chart(
            "RundiNova KPI Achievement",
            "Atteinte moyenne des KPI (%)",
            "Group By",
            "RundiNova KPI Snapshot",
            "Bar",
            group_by="kpi_definition",
            group_by_type="Average",
            value_based_on="target_achievement_percent",
        ),
        "decision_status": _ensure_chart(
            "RundiNova Decisions by Status",
            "Décisions par statut",
            "Group By",
            "RundiNova Decision",
            "Donut",
            group_by="status",
        ),
        "document_category": _ensure_chart(
            "RundiNova Documents by Category",
            "Documents par catégorie",
            "Group By",
            "RundiNova Document",
            "Bar",
            group_by="document_type",
        ),
        # People Dashboard - Additional Charts
        "employee_designation": _ensure_chart(
            "RundiNova Employees by Designation",
            "Employés par fonction",
            "Group By",
            "Employee",
            "Bar",
            group_by="designation",
            filters=[["Employee", "status", "=", "Active"]],
        ),
        "employee_gender": _ensure_chart(
            "RundiNova Employees by Gender",
            "Employés par genre",
            "Group By",
            "Employee",
            "Pie",
            group_by="gender",
            filters=[["Employee", "status", "=", "Active"]],
        ),
        "kpi_frequency": _ensure_chart(
            "RundiNova KPI by Frequency",
            "KPI par fréquence",
            "Group By",
            "RundiNova KPI Definition",
            "Donut",
            group_by="frequency",
            filters=[["RundiNova KPI Definition", "active", "=", "1"]],
        ),
        # Delivery Dashboard - Additional Charts
        "project_status": _ensure_chart(
            "RundiNova Projects by Status",
            "Projets par statut",
            "Group By",
            "Project",
            "Donut",
            group_by="status",
            filters=[["Project", "status", "!=", "Cancelled"]],
        ),
        "project_stage": _ensure_chart(
            "RundiNova Projects by Stage",
            "Projets par étape",
            "Group By",
            "RundiNova Repository",
            "Bar",
            group_by="project_stage",
            filters=[["RundiNova Repository", "status", "=", "Active"]],
        ),
        "project_priority": _ensure_chart(
            "RundiNova Projects by Priority",
            "Projets par priorité",
            "Group By",
            "RundiNova Repository",
            "Donut",
            group_by="priority",
            filters=[["RundiNova Repository", "status", "=", "Active"]],
        ),
        "project_risk": _ensure_chart(
            "RundiNova Projects by Risk Level",
            "Projets par niveau de risque",
            "Group By",
            "RundiNova Repository",
            "Bar",
            group_by="risk_level",
            filters=[["RundiNova Repository", "status", "=", "Active"]],
        ),
        "task_status": _ensure_chart(
            "RundiNova Tasks by Status",
            "Tâches par statut",
            "Group By",
            "Task",
            "Bar",
            group_by="status",
        ),
        "repository_type": _ensure_chart(
            "RundiNova Repositories by Type",
            "Dépôts par type",
            "Group By",
            "RundiNova Repository",
            "Pie",
            group_by="repository_type",
            filters=[["RundiNova Repository", "status", "=", "Active"]],
        ),
        "repository_progress": _ensure_chart(
            "RundiNova Repository Progress",
            "Avancement des dépôts (%)",
            "Group By",
            "RundiNova Repository",
            "Bar",
            group_by="repository_name",
            group_by_type="Average",
            value_based_on="progress_percent",
            filters=[["RundiNova Repository", "status", "=", "Active"]],
        ),
        "repository_business_value": _ensure_chart(
            "RundiNova Repository Business Value",
            "Valeur métier par dépôt",
            "Group By",
            "RundiNova Repository",
            "Bar",
            group_by="repository_name",
            group_by_type="Sum",
            value_based_on="business_value",
            filters=[["RundiNova Repository", "status", "=", "Active"]],
        ),
        # Ecosystem Dashboard - Additional Charts
        "partnership_type": _ensure_chart(
            "RundiNova Partnerships by Type",
            "Partenariats par type",
            "Group By",
            "RundiNova Partnership",
            "Bar",
            group_by="partner_type",
        ),
        "community_participants": _ensure_chart(
            "RundiNova Community Participants",
            "Participants par activité",
            "Group By",
            "RundiNova Community Impact",
            "Bar",
            group_by="activity_name",
            group_by_type="Sum",
            value_based_on="participants",
        ),
        "community_beneficiaries": _ensure_chart(
            "RundiNova Community Beneficiaries",
            "Bénéficiaires par mois",
            "Sum",
            "RundiNova Community Impact",
            "Line",
            based_on="activity_date",
            value_based_on="beneficiaries",
            timeseries=True,
        ),
        "growth_opportunity_value": _ensure_chart(
            "RundiNova Opportunity Value",
            "Valeur du pipeline par étape (FBu)",
            "Group By",
            "RundiNova Growth Opportunity",
            "Bar",
            group_by="stage",
            group_by_type="Sum",
            value_based_on="expected_value",
        ),
    }
    _dashboard(
        "RundiNova Executive Dashboard",
        [
            (charts["budget_trend"], "Full"),
            (charts["cash_movement_trend"], "Full"),
            (charts["project_status"], "Half"),
            (charts["task_status"], "Half"),
            (charts["growth_opportunity_value"], "Half"),
            (charts["risk_status"], "Half"),
            (charts["goal_progress"], "Full"),
        ],
        [
            cards["projects"],
            cards["open_tasks"],
            cards["cash_balance"],
            cards["planned"],
            cards["risks"],
            cards["pipeline"],
        ],
    )
    _dashboard(
        "RundiNova Finance Dashboard",
        [
            (charts["budget_trend"], "Full"),
            (charts["expense_trend"], "Full"),
            (charts["cash_movement_trend"], "Full"),
            (charts["budget_branch"], "Half"),
            (charts["food_progress"], "Half"),
            (charts["food_status"], "Half"),
            (charts["cash_movement_type"], "Half"),
            (charts["cash_account_balance"], "Half"),
            (charts["general_expense_category"], "Half"),
        ],
        [
            cards["cash_balance"],
            cards["cash_movements"],
            cards["planned"],
            cards["committed"],
            cards["actual"],
            cards["remaining"],
        ],
    )
    _dashboard(
        "RundiNova People Dashboard",
        [
            (charts["employees_branch"], "Half"),
            (charts["employees_department"], "Half"),
            (charts["employee_designation"], "Full"),
            (charts["employee_gender"], "Half"),
            (charts["kpi_frequency"], "Half"),
            (charts["opportunity_trend"], "Full"),
        ],
        [cards["employees"], cards["goals"], cards["goals_achieved"], cards["kpis"]],
    )
    _dashboard(
        "RundiNova Delivery Dashboard",
        [
            (charts["project_status"], "Half"),
            (charts["task_status"], "Half"),
            (charts["project_stage"], "Half"),
            (charts["project_risk"], "Half"),
            (charts["repository_progress"], "Full"),
            (charts["risk_impact"], "Half"),
        ],
        [
            cards["projects"],
            cards["open_tasks"],
            cards["overdue_tasks"],
            cards["repositories"],
            cards["repositories_high_risk"],
        ],
    )
    _dashboard(
        "RundiNova Ecosystem Dashboard",
        [
            (charts["partnership_status"], "Half"),
            (charts["partnership_type"], "Half"),
            (charts["community_status"], "Half"),
            (charts["community_participants"], "Half"),
            (charts["community_beneficiaries"], "Full"),
            (charts["growth_opportunity_value"], "Full"),
        ],
        [cards["partnerships"], cards["opportunities"], cards["pipeline"]],
    )

    sync_dashboard_currencies()
    sync_workspaces(
        overview_charts=[
            (charts["budget_trend"], "Évolution du budget planifié"),
            (charts["cash_movement_trend"], "Mouvements de trésorerie"),
            (charts["project_status"], "Projets par statut"),
            (charts["task_status"], "Tâches par statut"),
        ],
        overview_number_cards=[
            (cards["projects"], "Projets actifs"),
            (cards["open_tasks"], "Tâches ouvertes"),
            (cards["cash_balance"], "Solde de trésorerie"),
            (cards["planned"], "Budget planifié"),
        ],
    )
    # User.save validates its default workspace link. Recreate/sync workspaces
    # first because a migration can temporarily remove stale custom workspaces.
    ensure_crm_app_access_roles()
    frappe.db.commit()
