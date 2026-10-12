"""RundiNova role policy and assignment-scoped access checks."""

import frappe

ROLES = (
    "RundiNova Director",
    "RundiNova Finance Manager",
    "RundiNova Operations",
    "RundiNova Project Lead",
    "RundiNova Ecosystem Lead",
    "RundiNova Growth Lead",
    "RundiNova Community Relations",
    "RundiNova Team Member",
    "RundiNova Communications",
    "RundiNova People & Culture",
    "RundiNova Developer",
)

READ = {"read": 1, "write": 0, "create": 0, "delete": 0, "report": 1}
ASSIGNED_READ = {**READ, "report": 0}
WRITE = {"read": 1, "write": 1, "create": 1, "delete": 0, "report": 1}
CREATE_EXPENSE = {**ASSIGNED_READ, "create": 1}

FINANCIAL_DOCTYPES = (
    "RundiNova Food Budget",
    "RundiNova Food Expense",
    "RundiNova Food Progress",
    "RundiNova Budget Review",
    "RundiNova Expense",
)
CASH_DOCTYPES = ("RundiNova Cash Account", "RundiNova Cash Movement")
ASSET_DOCTYPES = ("RundiNova Asset",)
PROJECT_DOCTYPES = ("RundiNova Repository", "RundiNova Risk")
DECISION_DOCTYPES = ("RundiNova Decision",)
DOCUMENT_DOCTYPES = ("RundiNova Document",)
KPI_DOCTYPES = ("RundiNova Goal", "RundiNova KPI Definition", "RundiNova KPI Snapshot")
CRM_DOCTYPES = (
    "RundiNova Growth Opportunity",
    "RundiNova Partnership",
    "RundiNova Community Impact",
)
CRM_OPERATIONAL_DOCTYPES = (
    "CRM Lead",
    "CRM Deal",
    "CRM Organization",
    "CRM Task",
    "CRM Call Log",
    "FCRM Note",
)
CRM_LOOKUP_DOCTYPES = (
    "CRM Lead Status",
    "CRM Lead Source",
    "CRM Deal Status",
    "CRM Industry",
    "CRM Territory",
    "CRM Lost Reason",
)
OFFICE_DOCTYPES = ("RundiNova Office",)
DASHBOARD_ROLE_ACCESS = {
    "RundiNova Executive Dashboard": frozenset({"RundiNova Director"}),
    "RundiNova Finance Dashboard": frozenset(
        {"RundiNova Director", "RundiNova Finance Manager", "RundiNova Operations"}
    ),
    "RundiNova People Dashboard": frozenset(
        {"RundiNova Director", "RundiNova People & Culture"}
    ),
    "RundiNova Delivery Dashboard": frozenset(
        {
            "RundiNova Director",
            "RundiNova Project Lead",
            "RundiNova Operations",
            "RundiNova Developer",
        }
    ),
    "RundiNova Ecosystem Dashboard": frozenset(
        {
            "RundiNova Director",
            "RundiNova Ecosystem Lead",
            "RundiNova Growth Lead",
            "RundiNova Communications",
            "RundiNova Community Relations",
        }
    ),
}

ASSIGNED_DOCTYPES = frozenset(
    FINANCIAL_DOCTYPES + PROJECT_DOCTYPES + ("Project", "Task")
)
ASSIGNED_CHILD_DOCTYPES = frozenset(("RundiNova Food Budget Item",))
TEAM_MEMBER_CREATE_DOCTYPES = frozenset(("RundiNova Food Expense", "RundiNova Expense"))


def get_custom_doctype_permissions():
    """Return the role matrix documented in docs/rundinova/06-roles-and-responsibilities.md."""
    permissions = {}

    def grant(doctypes, roles, rule):
        for doctype in doctypes:
            for role in roles:
                permissions[(doctype, role)] = dict(rule)

    all_doctypes = (
        FINANCIAL_DOCTYPES
        + CASH_DOCTYPES
        + ASSET_DOCTYPES
        + PROJECT_DOCTYPES
        + DECISION_DOCTYPES
        + DOCUMENT_DOCTYPES
        + KPI_DOCTYPES
        + CRM_DOCTYPES
        + OFFICE_DOCTYPES
    )
    grant(all_doctypes, ("RundiNova Director",), WRITE)

    # Budget and expense records are assigned to individual team members;
    # the access hooks below filter those records by owner or active ToDo.
    grant(
        FINANCIAL_DOCTYPES, ("RundiNova Finance Manager", "RundiNova Operations"), WRITE
    )
    grant(FINANCIAL_DOCTYPES, ("RundiNova Project Lead",), READ)
    grant(FINANCIAL_DOCTYPES, ("RundiNova Team Member",), ASSIGNED_READ)
    for doctype in TEAM_MEMBER_CREATE_DOCTYPES:
        permissions[(doctype, "RundiNova Team Member")] = dict(CREATE_EXPENSE)

    grant(CASH_DOCTYPES, ("RundiNova Finance Manager",), WRITE)
    grant(CASH_DOCTYPES, ("RundiNova Operations",), READ)

    grant(
        ASSET_DOCTYPES, ("RundiNova Finance Manager", "RundiNova Project Lead"), WRITE
    )
    grant(
        ASSET_DOCTYPES,
        (
            "RundiNova Operations",
            "RundiNova Communications",
            "RundiNova People & Culture",
            "RundiNova Team Member",
        ),
        READ,
    )

    grant(PROJECT_DOCTYPES, ("RundiNova Project Lead",), WRITE)
    grant(
        PROJECT_DOCTYPES,
        (
            "RundiNova Operations",
            "RundiNova Ecosystem Lead",
            "RundiNova Growth Lead",
            "RundiNova Communications",
            "RundiNova Community Relations",
            "RundiNova People & Culture",
            "RundiNova Team Member",
            "RundiNova Developer",
        ),
        READ,
    )

    grant(
        DECISION_DOCTYPES,
        (
            "RundiNova Operations",
            "RundiNova Project Lead",
            "RundiNova Ecosystem Lead",
            "RundiNova Growth Lead",
            "RundiNova Communications",
            "RundiNova Community Relations",
            "RundiNova People & Culture",
        ),
        WRITE,
    )
    grant(DECISION_DOCTYPES, ("RundiNova Team Member",), READ)

    # The role table marks shared documents as available to the full team.
    grant(DOCUMENT_DOCTYPES, ROLES[1:], WRITE)

    grant(KPI_DOCTYPES, ("RundiNova Project Lead",), WRITE)
    grant(
        KPI_DOCTYPES,
        (
            "RundiNova Finance Manager",
            "RundiNova Operations",
            "RundiNova Team Member",
            "RundiNova Ecosystem Lead",
            "RundiNova Growth Lead",
            "RundiNova Communications",
            "RundiNova Community Relations",
            "RundiNova People & Culture",
        ),
        READ,
    )

    grant(CRM_DOCTYPES, ("RundiNova Communications",), WRITE)
    grant(
        ("RundiNova Partnership", "RundiNova Growth Opportunity"),
        ("RundiNova Ecosystem Lead",),
        WRITE,
    )
    grant(
        ("RundiNova Community Impact",),
        ("RundiNova Community Relations",),
        WRITE,
    )
    grant(
        CRM_DOCTYPES,
        (
            "RundiNova Operations",
            "RundiNova Project Lead",
            "RundiNova People & Culture",
        ),
        READ,
    )
    grant(
        (
            "RundiNova Growth Opportunity",
            "RundiNova Partnership",
            "RundiNova Community Impact",
        ),
        ("RundiNova Growth Lead", "RundiNova Community Relations"),
        READ,
    )
    # Specific ownership grants must follow the broader read-only grants.
    grant(("RundiNova Growth Opportunity",), ("RundiNova Growth Lead",), WRITE)
    grant(("RundiNova Community Impact",), ("RundiNova Community Relations",), WRITE)

    grant(OFFICE_DOCTYPES, ("RundiNova People & Culture",), WRITE)
    grant(
        OFFICE_DOCTYPES,
        (
            "RundiNova Operations",
            "RundiNova Project Lead",
            "RundiNova Team Member",
            "RundiNova Communications",
        ),
        READ,
    )

    return permissions


def get_standard_doctype_permissions():
    """Limit built-in ERPNext and HR data to the roles that need it."""
    permissions = {}

    def grant(doctypes, roles, rule=READ):
        for doctype in doctypes:
            for role in roles:
                permissions[(doctype, role)] = dict(rule)

    setup_doctypes = (
        "Branch",
        "Cost Center",
        "Company",
        "Department",
        "Designation",
        "Item",
        "Warehouse",
        "UOM",
    )
    grant(setup_doctypes, ROLES, READ)
    grant(setup_doctypes, ("RundiNova Director",), WRITE)
    grant(("Project", "Task"), ROLES, READ)
    grant(
        ("Project", "Task"),
        ("RundiNova Director", "RundiNova Operations", "RundiNova Project Lead"),
        WRITE,
    )
    grant(("Task",), ("RundiNova Team Member",), WRITE)
    grant(("Task",), ("RundiNova Developer",), WRITE)
    grant(("Project",), ("RundiNova Developer",), READ)
    dashboard_roles = set().union(*DASHBOARD_ROLE_ACCESS.values())
    grant(("Dashboard", "Dashboard Chart", "Number Card"), dashboard_roles, READ)
    grant(
        ("Dashboard", "Dashboard Chart", "Number Card"),
        ("RundiNova Director",),
        WRITE,
    )
    grant(
        ("Supplier",),
        ("RundiNova Director", "RundiNova Finance Manager", "RundiNova Operations"),
    )
    grant(("Employee",), ("RundiNova People & Culture",), WRITE)
    grant(("HR Settings",), ("RundiNova People & Culture",), WRITE)
    grant(("Employee", "HR Settings"), ("RundiNova Director",), WRITE)
    grant(
        CRM_OPERATIONAL_DOCTYPES,
        (
            "RundiNova Director",
            "RundiNova Communications",
            "RundiNova Growth Lead",
        ),
        WRITE,
    )
    grant(
        CRM_OPERATIONAL_DOCTYPES + CRM_LOOKUP_DOCTYPES,
        (
            "RundiNova Operations",
            "RundiNova Project Lead",
            "RundiNova Ecosystem Lead",
            "RundiNova Community Relations",
        ),
    )
    grant(
        CRM_LOOKUP_DOCTYPES,
        (
            "RundiNova Director",
            "RundiNova Communications",
            "RundiNova Growth Lead",
        ),
    )
    grant(
        ("Account", "GL Entry", "Mode of Payment"),
        ("RundiNova Director", "RundiNova Finance Manager"),
    )
    for role in ROLES:
        permissions[("Page", role)] = {
            "read": 1,
            "write": 0,
            "create": 0,
            "delete": 0,
            "report": 0,
        }
    permissions[("Page", "RundiNova Director")] = dict(WRITE)
    return permissions


def _team_member_is_scoped(user, doctype=None):
    if not user or user == "Administrator":
        return False
    roles = set(frappe.get_roles(user))
    if "RundiNova Team Member" not in roles or "System Manager" in roles:
        return False
    if "RundiNova Developer" in roles and doctype in PROJECT_DOCTYPES + ("Project", "Task"):
        return False
    if doctype in FINANCIAL_DOCTYPES or doctype == "RundiNova Food Budget Item":
        return not roles.intersection(
            {"RundiNova Director", "RundiNova Finance Manager", "RundiNova Operations"}
        )
    if doctype in PROJECT_DOCTYPES or doctype in {"Project", "Task"}:
        return not roles.intersection(
            {"RundiNova Director", "RundiNova Operations", "RundiNova Project Lead"}
        )
    return "RundiNova Director" not in roles


def _assigned_to_user(doctype, name, user):
    if not name or not doctype or not user:
        return False
    if frappe.db.get_value(doctype, name, "owner") == user:
        return True
    return bool(
        frappe.db.exists(
            "ToDo",
            {
                "reference_type": doctype,
                "reference_name": name,
                "allocated_to": user,
                "status": ["!=", "Cancelled"],
            },
        )
    )


def _assigned_parent_tables(child_doctype):
    return frappe.get_all(
        "DocField",
        filters={
            "fieldtype": "Table",
            "options": child_doctype,
            "parent": ["in", list(ASSIGNED_DOCTYPES)],
        },
        pluck="parent",
    )


def get_permission_query_conditions(user=None, doctype=None):
    """Restrict team-member list queries to owned or assigned records."""
    user = user or frappe.session.user
    if doctype in ASSIGNED_DOCTYPES:
        if not _team_member_is_scoped(user, doctype):
            return ""
        escaped_user = frappe.db.escape(user)
        escaped_doctype = frappe.db.escape(doctype)
        table = f"`tab{doctype}`"
        return (
            f"({table}.owner = {escaped_user} OR EXISTS ("
            "SELECT 1 FROM `tabToDo` assigned_task "
            f"WHERE assigned_task.reference_type = {escaped_doctype} "
            f"AND assigned_task.reference_name = {table}.name "
            f"AND assigned_task.allocated_to = {escaped_user} "
            "AND assigned_task.status != 'Cancelled'))"
        )

    parents = (
        _assigned_parent_tables(doctype) if doctype in ASSIGNED_CHILD_DOCTYPES else []
    )
    if not parents:
        return ""
    escaped_user = frappe.db.escape(user)
    conditions = []
    for parent in parents:
        if not _team_member_is_scoped(user, parent):
            conditions.append(
                f"(`tab{doctype}`.`parenttype` = {frappe.db.escape(parent)})"
            )
            continue
        parent_table = f"`tab{parent}`"
        escaped_parent = frappe.db.escape(parent)
        conditions.append(
            "EXISTS (SELECT 1 FROM "
            f"{parent_table} assigned_parent WHERE assigned_parent.name = `tab{doctype}`.parent "
            f"AND `tab{doctype}`.parenttype = {escaped_parent} "
            f"AND (assigned_parent.owner = {escaped_user} OR EXISTS ("
            "SELECT 1 FROM `tabToDo` assigned_task "
            f"WHERE assigned_task.reference_type = {escaped_parent} "
            "AND assigned_task.reference_name = assigned_parent.name "
            f"AND assigned_task.allocated_to = {escaped_user} "
            "AND assigned_task.status != 'Cancelled')))"
        )
    return "(" + " OR ".join(conditions) + ")" if conditions else ""


def _query_for(doctype, user=None):
    return get_permission_query_conditions(user=user, doctype=doctype)


def food_budget_query(user=None):
    return _query_for("RundiNova Food Budget", user)


def project_query(user=None):
    return _query_for("Project", user)


def task_query(user=None):
    return _query_for("Task", user)


def repository_query(user=None):
    return _query_for("RundiNova Repository", user)


def risk_query(user=None):
    return _query_for("RundiNova Risk", user)


def dashboard_query(user=None):
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    if "System Manager" in roles or "RundiNova Director" in roles:
        return ""
    allowed = [
        frappe.db.escape(name)
        for name, permitted_roles in DASHBOARD_ROLE_ACCESS.items()
        if roles.intersection(permitted_roles)
    ]
    if not allowed:
        return "1=0"
    return f"`tabDashboard`.`name` in ({', '.join(allowed)})"


def _dashboard_widget_query(doctype, child_doctype, child_field, user=None):
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    if "System Manager" in roles or "RundiNova Director" in roles:
        return ""
    dashboards = [
        frappe.db.escape(name)
        for name, permitted_roles in DASHBOARD_ROLE_ACCESS.items()
        if roles.intersection(permitted_roles)
    ]
    if not dashboards:
        return "1=0"
    return (
        f"`tab{doctype}`.`name` in (SELECT `{child_field}` FROM `tab{child_doctype}` "
        f"WHERE `parent` in ({', '.join(dashboards)}))"
    )


def dashboard_chart_query(user=None):
    return _dashboard_widget_query(
        "Dashboard Chart", "Dashboard Chart Link", "chart", user
    )


def number_card_query(user=None):
    return _dashboard_widget_query("Number Card", "Number Card Link", "card", user)


def workspace_query(user=None):
    """Keep hidden and role-restricted workspaces out of Desk list responses."""
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    if user == "Administrator" or "System Manager" in roles:
        return ""
    escaped_user = frappe.db.escape(user)
    role_clause = "1=0"
    if roles:
        escaped_roles = ", ".join(frappe.db.escape(role) for role in sorted(roles))
        role_clause = (
            "NOT EXISTS (SELECT 1 FROM `tabHas Role` any_workspace_role "
            "WHERE any_workspace_role.parent = `tabWorkspace`.name "
            "AND any_workspace_role.parenttype = 'Workspace') OR EXISTS ("
            "SELECT 1 FROM `tabHas Role` workspace_role "
            "WHERE workspace_role.parent = `tabWorkspace`.name "
            "AND workspace_role.parenttype = 'Workspace' "
            f"AND workspace_role.role IN ({escaped_roles}))"
        )
    return (
        "(`tabWorkspace`.is_hidden = 0 AND "
        f"(`tabWorkspace`.for_user = {escaped_user} OR `tabWorkspace`.public = 1) AND "
        f"({role_clause}))"
    )


def food_expense_query(user=None):
    return _query_for("RundiNova Food Expense", user)


def food_progress_query(user=None):
    return _query_for("RundiNova Food Progress", user)


def budget_review_query(user=None):
    return _query_for("RundiNova Budget Review", user)


def expense_query(user=None):
    return _query_for("RundiNova Expense", user)


def food_budget_item_query(user=None):
    return _query_for("RundiNova Food Budget Item", user)


def has_permission(doc, user=None, ptype=None, permission_type=None, **kwargs):
    """Enforce the assignment boundary on both direct reads and writes."""
    user = user or frappe.session.user
    permission_type = permission_type or ptype
    if doc.doctype == "Workspace":
        roles = set(frappe.get_roles(user))
        if user == "Administrator" or roles.intersection(
            {"System Manager", "RundiNova Director"}
        ):
            return True
        if permission_type not in ("read", "select") or doc.get("is_hidden"):
            return False
        if doc.get("for_user") and doc.for_user != user:
            return False
        required_roles = {row.role for row in doc.get("roles", [])}
        if required_roles:
            return bool(roles.intersection(required_roles))
        return bool(doc.get("public") or doc.get("for_user") == user)
    if doc.doctype == "Page":
        roles = set(frappe.get_roles(user))
        if user == "Administrator" or roles.intersection(
            {"System Manager", "RundiNova Director"}
        ):
            return True
        if permission_type not in ("read", "select"):
            return False
        required_roles = {row.role for row in doc.get("roles", [])}
        return not required_roles or bool(roles.intersection(required_roles))
    if doc.doctype == "Workspace":
        roles = set(frappe.get_roles(user))
        if user == "Administrator" or "System Manager" in roles:
            return True
        if doc.get("is_hidden"):
            return False
        workspace_roles = {row.role for row in doc.get("roles", [])}
        if workspace_roles:
            return bool(roles.intersection(workspace_roles))
        if doc.get("for_user"):
            return doc.for_user == user
        return bool(doc.get("public"))
    if doc.doctype in (
        "Dashboard",
        "Dashboard Chart",
        "Number Card",
    ) and permission_type in (
        "read",
        "select",
    ):
        roles = set(frappe.get_roles(user))
        if "System Manager" in roles or "RundiNova Director" in roles:
            return True
        if doc.doctype == "Dashboard":
            return bool(roles.intersection(DASHBOARD_ROLE_ACCESS.get(doc.name, ())))
        links = (
            "Dashboard Chart Link"
            if doc.doctype == "Dashboard Chart"
            else "Number Card Link"
        )
        field = "chart" if doc.doctype == "Dashboard Chart" else "card"
        permitted_dashboards = [
            name
            for name, permitted_roles in DASHBOARD_ROLE_ACCESS.items()
            if roles.intersection(permitted_roles)
        ]
        return bool(
            permitted_dashboards
            and frappe.db.exists(
                links,
                {field: doc.name, "parent": ["in", permitted_dashboards]},
            )
        )
    if not _team_member_is_scoped(user, doc.doctype):
        # Frappe 16 treats a falsy controller hook result (including None)
        # as an explicit denial. Users outside the restricted team-member
        # cohort must therefore pass this controller check explicitly.
        return True

    if permission_type == "create":
        return doc.doctype in TEAM_MEMBER_CREATE_DOCTYPES

    if permission_type == "write":
        # Team members may submit their own expense records, but cannot edit
        # budgets, approvals, progress snapshots, or existing expenses.
        if doc.doctype == "Task":
            return _assigned_to_user(doc.doctype, doc.name, user)
        return False

    if permission_type not in ("read", "select"):
        return False

    if doc.doctype in ASSIGNED_DOCTYPES:
        return _assigned_to_user(doc.doctype, doc.name, user)

    if doc.doctype in ASSIGNED_CHILD_DOCTYPES:
        parent_type = doc.parenttype
        if parent_type not in ASSIGNED_DOCTYPES:
            return False
        if not _team_member_is_scoped(user, parent_type):
            return True
        return _assigned_to_user(parent_type, doc.parent, user)

    return None
