import json

import frappe


def _insert(doctype, name, values):
    if frappe.db.exists(doctype, name):
        return frappe.get_doc(doctype, name)
    doc = frappe.new_doc(doctype)
    doc.name = name
    doc.flags.name_set = True
    doc.flags.ignore_mandatory = True
    for key, value in values.items():
        setattr(doc, key, value)
    doc.insert(ignore_permissions=True, ignore_links=True, ignore_mandatory=True)
    return doc


def seed():
    """Provision app configuration only; never create fictitious business data.

    Companies, users, employees, items, budgets, opening balances, and
    transactions must be entered and approved by the RundiNova team.
    """
    roles = ensure_rundinova_roles()
    permissions = ensure_rundinova_permissions()
    sync_dashboards()
    return {"configured": True, "business_data_created": False, "roles": roles, "permissions": list(permissions)}


def ensure_rundinova_roles():
    """Create only named roles; users and permissions remain administrator-controlled."""
    role_names = [
        "RundiNova Director",
        "RundiNova Finance Manager",
        "RundiNova Project Lead",
        "RundiNova Team Member",
        "RundiNova Communications",
    ]
    created = []
    for role_name in role_names:
        if frappe.db.exists("Role", role_name):
            continue
        frappe.get_doc({
            "doctype": "Role",
            "role_name": role_name,
            "desk_access": 1,
            "is_custom": 1,
        }).insert(ignore_permissions=True)
        created.append(role_name)
    frappe.db.commit()
    return created


def ensure_rundinova_permissions():
    """Apply least-privilege access to custom RundiNova DocTypes."""
    matrix = {
        "RundiNova Director": {"read": 1, "write": 1, "create": 1, "delete": 0},
        "RundiNova Finance Manager": {"read": 1, "write": 1, "create": 1, "delete": 1},
        "RundiNova Project Lead": {"read": 1, "write": 1, "create": 1, "delete": 0},
        "RundiNova Team Member": {"read": 1, "write": 1, "create": 1, "delete": 0},
        "RundiNova Communications": {"read": 1, "write": 1, "create": 1, "delete": 0},
    }
    doctypes = [
        "RundiNova Food Budget", "RundiNova Food Expense", "RundiNova Budget Review",
        "RundiNova KPI Definition", "RundiNova KPI Snapshot", "RundiNova Risk",
        "RundiNova Growth Opportunity", "RundiNova Partnership", "RundiNova Community Impact",
        "RundiNova Office",
        "RundiNova Repository",
    ]
    for doctype in doctypes:
        if not frappe.db.exists("DocType", doctype):
            continue
        doc = frappe.get_doc("DocType", doctype)
        existing = {row.role: row for row in doc.permissions}
        for role, permissions in matrix.items():
            row = existing.get(role)
            if not row:
                row = doc.append("permissions", {"role": role, "permlevel": 0})
            for permission, enabled in permissions.items():
                setattr(row, permission, enabled)
        doc.save(ignore_permissions=True)
    frappe.clear_cache()
    return matrix


def _ensure_number_card(name, label, document_type, function="Count", report_field=None,
                        filters=None, color=None, background_color=None):
    values = {
        "label": label, "type": "Document Type", "function": function,
        "document_type": document_type,
        "aggregate_function_based_on": report_field,
        "filters_json": json.dumps(filters or []), "is_public": 1,
        "show_full_number": 1, "color": color,
        "background_color": background_color, "module": "RundiNova Tech",
    }
    existing = frappe.db.get_value("Number Card", {"module": "RundiNova Tech", "label": label}, "name") or (name if frappe.db.exists("Number Card", name) else None)
    if existing:
        doc = frappe.get_doc("Number Card", existing)
        doc.update(values)
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.get_doc({"doctype": "Number Card", "name": name, **values})
        doc.insert(ignore_permissions=True)
    return doc.name


def _ensure_chart(name, chart_name, chart_type, document_type, chart_kind,
                  group_by=None, based_on=None, value_based_on=None,
                  filters=None, timeseries=False, time_interval="Monthly"):
    values = {
        "chart_name": chart_name, "chart_type": chart_type,
        "document_type": document_type, "group_by_type": "Count",
        "group_by_based_on": group_by, "based_on": based_on,
        "value_based_on": value_based_on,
        "aggregate_function_based_on": value_based_on,
        "type": chart_kind,
        "timeseries": 1 if timeseries else 0, "time_interval": time_interval,
        "filters_json": json.dumps(filters or []), "is_public": 1,
        "module": "RundiNova Tech",
    }
    existing = frappe.db.get_value("Dashboard Chart", {"module": "RundiNova Tech", "chart_name": chart_name}, "name") or frappe.db.get_value("Dashboard Chart", {"chart_name": chart_name}, "name") or (name if frappe.db.exists("Dashboard Chart", name) else None)
    if existing:
        doc = frappe.get_doc("Dashboard Chart", existing)
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
    doc = frappe.get_doc("Dashboard", name) if frappe.db.exists("Dashboard", name) else frappe.new_doc("Dashboard")
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


def _workspace_content():
    links = [
        ("rundinova-onboarding", "Préparation au démarrage", "tool"),
        ("RundiNova Executive Dashboard", "Pilotage exécutif", "dashboard"),
        ("RundiNova Finance Dashboard", "Finance & budgets", "accounting"),
        ("RundiNova People Dashboard", "Équipe & RH", "users"),
        ("RundiNova Delivery Dashboard", "Projets & livraison", "project"),
        ("RundiNova Ecosystem Dashboard", "Écosystème & croissance", "crm"),
    ]
    content = [{"id": "rundinova-title", "type": "header", "data": {"text": "RundiNova Tech · Centre de pilotage", "col": 12}}]
    for idx, (target, label, icon) in enumerate(links):
        target_type = "Page" if target == "rundinova-onboarding" else "Dashboard"
        content.append({"id": f"rundinova-shortcut-{idx}", "type": "shortcut", "data": {"type": target_type, "link_to": target, "label": label, "icon": icon, "col": 4}})
    return json.dumps(content)


def sync_dashboards():
    """Provision rich, clickable dashboards and the branded app workspace."""
    ensure_purchase_invoice_budget_field()
    backfill_budget_titles()
    cards = {
        "employees": _ensure_number_card("RundiNova Active Employees", "Employés actifs", "Employee", filters=[["Employee", "status", "=", "Active"]], color="#2563EB", background_color="#EFF6FF"),
        "budgets": _ensure_number_card("RundiNova Food Budgets", "Budgets alimentaires", "RundiNova Food Budget", color="#0F766E", background_color="#ECFDF5"),
        "planned": _ensure_number_card("RundiNova Planned Budget", "Budget planifié", "RundiNova Food Budget", "Sum", "total_planned_amount", color="#7C3AED", background_color="#F5F3FF"),
        "committed": _ensure_number_card("RundiNova Committed Food Spend", "Dépenses engagées", "RundiNova Food Expense", "Sum", "amount", filters=[["RundiNova Food Expense", "status", "in", ["Submitted", "Approved", "Paid"]]], color="#EA580C", background_color="#FFF7ED"),
        "actual": _ensure_number_card("RundiNova Actual Food Spend", "Dépenses payées", "RundiNova Food Expense", "Sum", "amount", filters=[["RundiNova Food Expense", "status", "=", "Paid"]], color="#B91C1C", background_color="#FEF2F2"),
        "remaining": _ensure_number_card("RundiNova Food Budget Remaining", "Solde alimentaire", "RundiNova Food Budget", "Sum", "balance_amount", color="#059669", background_color="#ECFDF5"),
        "risks": _ensure_number_card("RundiNova Open Risks", "Risques ouverts", "RundiNova Risk", filters=[["RundiNova Risk", "status", "in", ["Open", "Monitoring"]]], color="#DC2626", background_color="#FEF2F2"),
        "opportunities": _ensure_number_card("RundiNova Opportunities", "Opportunités", "RundiNova Growth Opportunity", color="#D97706", background_color="#FFFBEB"),
        "pipeline": _ensure_number_card("RundiNova Pipeline Value", "Valeur du pipeline", "RundiNova Growth Opportunity", "Sum", "expected_value", color="#0891B2", background_color="#ECFEFF"),
        "partnerships": _ensure_number_card("RundiNova Partnerships", "Partenariats actifs", "RundiNova Partnership", filters=[["RundiNova Partnership", "status", "=", "Active"]], color="#DB2777", background_color="#FDF2F8"),
        "kpis": _ensure_number_card("RundiNova KPI Snapshots", "Mesures KPI", "RundiNova KPI Snapshot", color="#4F46E5", background_color="#EEF2FF"),
    }
    charts = {
        "employees_branch": _ensure_chart("RundiNova Employees by Branch", "Employés par bureau", "Group By", "Employee", "Donut", group_by="branch", filters=[["Employee", "status", "=", "Active"]]),
        "employees_department": _ensure_chart("RundiNova Employees by Department", "Employés par département", "Group By", "Employee", "Bar", group_by="department", filters=[["Employee", "status", "=", "Active"]]),
        "budget_branch": _ensure_chart("RundiNova Budgets by Branch", "Budgets par bureau", "Group By", "RundiNova Food Budget", "Bar", group_by="branch"),
        "budget_trend": _ensure_chart("RundiNova Budget Trend", "Évolution du budget planifié", "Sum", "RundiNova Food Budget", "Line", based_on="period_start", value_based_on="total_planned_amount", timeseries=True),
        "expense_trend": _ensure_chart("RundiNova Food Expense Trend", "Consommation alimentaire quotidienne", "Sum", "RundiNova Food Expense", "Line", based_on="expense_date", value_based_on="amount", filters=[["RundiNova Food Expense", "status", "in", ["Submitted", "Approved", "Paid"]]], timeseries=True, time_interval="Daily"),
        "expense_category": _ensure_chart("RundiNova Food Expense by Category", "Dépenses par catégorie", "Group By", "RundiNova Food Expense", "Donut", group_by="category", filters=[["RundiNova Food Expense", "status", "in", ["Submitted", "Approved", "Paid"]]]),
        "risk_status": _ensure_chart("RundiNova Risks by Status", "Risques par statut", "Group By", "RundiNova Risk", "Donut", group_by="status"),
        "risk_impact": _ensure_chart("RundiNova Risks by Impact", "Risques par impact", "Group By", "RundiNova Risk", "Bar", group_by="impact"),
        "opportunity_stage": _ensure_chart("RundiNova Opportunities by Stage", "Opportunités par étape", "Group By", "RundiNova Growth Opportunity", "Bar", group_by="stage"),
        "opportunity_trend": _ensure_chart("RundiNova KPI Trend", "Mesures KPI dans le temps", "Average", "RundiNova KPI Snapshot", "Line", based_on="period_start", value_based_on="target_achievement_percent", timeseries=True),
        "partnership_status": _ensure_chart("RundiNova Partnerships by Status", "Partenariats par statut", "Group By", "RundiNova Partnership", "Donut", group_by="status"),
        "community_status": _ensure_chart("RundiNova Community Activities", "Activités communautaires", "Group By", "RundiNova Community Impact", "Bar", group_by="status"),
    }
    _dashboard("RundiNova Executive Dashboard", [(charts["employees_branch"], "Half"), (charts["budget_trend"], "Half"), (charts["opportunity_stage"], "Half"), (charts["risk_status"], "Half")], [cards["employees"], cards["planned"], cards["risks"], cards["pipeline"]])
    _dashboard("RundiNova Finance Dashboard", [(charts["budget_branch"], "Half"), (charts["budget_trend"], "Half"), (charts["expense_trend"], "Full"), (charts["expense_category"], "Half")], [cards["budgets"], cards["planned"], cards["committed"], cards["actual"], cards["remaining"]])
    _dashboard("RundiNova People Dashboard", [(charts["employees_branch"], "Half"), (charts["employees_department"], "Half"), (charts["opportunity_trend"], "Full")], [cards["employees"], cards["kpis"]])
    _dashboard("RundiNova Delivery Dashboard", [(charts["opportunity_stage"], "Half"), (charts["risk_impact"], "Half"), (charts["opportunity_trend"], "Full")], [cards["opportunities"], cards["risks"]])
    _dashboard("RundiNova Ecosystem Dashboard", [(charts["partnership_status"], "Half"), (charts["community_status"], "Half"), (charts["opportunity_stage"], "Full")], [cards["partnerships"], cards["opportunities"], cards["pipeline"]])

    workspace = frappe.get_doc("Workspace", "RundiNova Tech") if frappe.db.exists("Workspace", "RundiNova Tech") else frappe.new_doc("Workspace")
    workspace.update({"label": "RundiNova Tech", "title": "RundiNova Tech", "module": "RundiNova Tech", "app": "rundinova_tech", "type": "Workspace", "icon": "organization", "indicator_color": "blue", "public": 1, "is_hidden": 0, "content": _workspace_content()})
    workspace.save(ignore_permissions=True)
    frappe.db.commit()


def backfill_budget_titles():
    """Populate human-readable titles and consumption totals on legacy budgets."""
    from rundinova_tech.rundinova_tech.doctype.rundinova_food_budget.rundinova_food_budget import (
        set_budget_title,
        update_budget_totals,
    )

    for name in frappe.get_all("RundiNova Food Budget", pluck="name"):
        budget = frappe.get_doc("RundiNova Food Budget", name)
        set_budget_title(budget)
        update_budget_totals(budget)
        budget.db_update()


def ensure_purchase_invoice_budget_field():
    """Add the optional budget selector to ERPNext Purchase Invoice once."""
    fieldname = "rundinova_food_budget"
    if frappe.db.exists("Custom Field", {"dt": "Purchase Invoice", "fieldname": fieldname}):
        return
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Purchase Invoice",
        "fieldname": fieldname,
        "label": "RundiNova Food Budget",
        "fieldtype": "Link",
        "options": "RundiNova Food Budget",
        "insert_after": "supplier",
        "module": "RundiNova Tech",
    }).insert(ignore_permissions=True, ignore_if_duplicate=True)
