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

ASSIGNED_DOCTYPES = frozenset(FINANCIAL_DOCTYPES)
ASSIGNED_CHILD_DOCTYPES = frozenset(("RundiNova Food Budget Item",))
TEAM_MEMBER_CREATE_DOCTYPES = frozenset(("RundiNova Food Expense", "RundiNova Expense"))
PRIVILEGED_RUNDINOVA_ROLES = frozenset(ROLES) - {"RundiNova Team Member"}


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
    grant(
        FINANCIAL_DOCTYPES,
        (
            "RundiNova Project Lead",
            "RundiNova Ecosystem Lead",
            "RundiNova Growth Lead",
            "RundiNova Communications",
            "RundiNova Community Relations",
            "RundiNova People & Culture",
        ),
        READ,
    )
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

    grant(
        (
            "Branch",
            "Cost Center",
            "Company",
            "Department",
            "Designation",
            "Item",
            "Warehouse",
            "UOM",
        ),
        ROLES,
    )
    grant(
        ("Project", "Task"),
        (
            "RundiNova Director",
            "RundiNova Operations",
            "RundiNova Project Lead",
            "RundiNova Communications",
            "RundiNova People & Culture",
            "RundiNova Team Member",
        ),
    )
    grant(
        ("Supplier",),
        ("RundiNova Director", "RundiNova Finance Manager", "RundiNova Operations"),
    )
    grant(("Employee",), ("RundiNova Director", "RundiNova People & Culture"))
    grant(("HR Settings",), ("RundiNova Director", "RundiNova People & Culture"))
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
    return permissions


def _team_member_is_scoped(user):
    if not user or user == "Administrator":
        return False
    roles = set(frappe.get_roles(user))
    return (
        "RundiNova Team Member" in roles
        and not roles.intersection(PRIVILEGED_RUNDINOVA_ROLES)
        and "System Manager" not in roles
    )


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
    """Restrict team-member list queries to owned or assigned financial records."""
    user = user or frappe.session.user
    if not _team_member_is_scoped(user):
        return ""

    escaped_user = frappe.db.escape(user)
    if doctype in ASSIGNED_DOCTYPES:
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
    conditions = []
    for parent in parents:
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
    if not _team_member_is_scoped(user):
        # Frappe 16 treats a falsy controller hook result (including None)
        # as an explicit denial. Users outside the restricted team-member
        # cohort must therefore pass this controller check explicitly.
        return True

    permission_type = permission_type or ptype
    if permission_type == "create":
        return doc.doctype in TEAM_MEMBER_CREATE_DOCTYPES

    if permission_type == "write":
        # Team members may submit their own expense records, but cannot edit
        # budgets, approvals, progress snapshots, or existing expenses.
        return False

    if permission_type not in ("read", "select"):
        return False

    if doc.doctype in ASSIGNED_DOCTYPES:
        return _assigned_to_user(doc.doctype, doc.name, user)

    if doc.doctype in ASSIGNED_CHILD_DOCTYPES:
        parent_type = doc.parenttype
        if parent_type not in ASSIGNED_DOCTYPES:
            return False
        return _assigned_to_user(parent_type, doc.parent, user)

    return None
