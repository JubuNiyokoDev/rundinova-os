app_name = "rundinova_tech"
app_title = "RundiNova Tech"
app_publisher = "RundiNova Tech"
app_description = "Operations, budgets, impact and governance for RundiNova Tech"
app_email = "operations@rundinova.com"
app_license = "MIT"

app_include_js = [
    "/assets/rundinova_tech/js/workspace_sidebar.js",
    "/assets/rundinova_tech/js/rundinova_branding_2.js",
    "/assets/rundinova_tech/js/rundinova_route_aliases.js",
]
app_include_css = "/assets/rundinova_tech/css/rundinova_desk.css"
web_include_js = ["/assets/rundinova_tech/js/rundinova_branding_2.js"]
page_js = {
    "rundinova-home": "public/js/rundinova_home.js",
    "rundinova-setup": "public/js/rundinova_setup.js",
    "configuration-rundinova": "public/js/rundinova_route_aliases.js",
    "rundinova-équipe": "public/js/rundinova_route_aliases.js",
    "rundinova-equipe": "public/js/rundinova_route_aliases.js",
}

# RundiNova branding used by the Desk sidebar, login page and app switcher.
# The image is shipped with this app so it is available in every deployment.
app_logo_url = "/assets/rundinova_tech/images/rundinova-logo-wide.svg"

api_version = 1

required_apps = ["frappe", "erpnext", "hrms", "crm"]

doctype_js = {
    "RundiNova Cash Movement": "public/js/rundinova_cash_movement.js",
    "RundiNova Food Budget": "public/js/rundinova_food_purchase.js",
    "RundiNova Food Progress": "public/js/rundinova_food_purchase.js",
    "RundiNova Food Expense": "public/js/rundinova_food_purchase.js",
}

doctype_list_js = {
    doctype: "public/js/rundinova_list_view.js"
    for doctype in (
        "RundiNova Decision",
        "RundiNova Repository",
        "RundiNova Growth Opportunity",
        "RundiNova KPI Definition",
        "RundiNova Goal",
        "RundiNova KPI Snapshot",
        "RundiNova Partnership",
        "RundiNova Food Progress",
        "RundiNova Food Budget",
        "RundiNova Risk",
        "RundiNova Office",
        "RundiNova Asset",
        "RundiNova Community Impact",
        "RundiNova Cash Movement",
        "RundiNova Food Expense",
        "RundiNova Budget Review",
        "RundiNova Expense",
        "RundiNova Cash Account",
        "RundiNova Document",
    )
}
doctype_list_js["RundiNova Food Progress"] = "public/js/rundinova_food_purchase.js"
doctype_list_js["RundiNova Food Budget"] = "public/js/rundinova_food_purchase.js"
doctype_list_js["RundiNova Food Expense"] = "public/js/rundinova_food_purchase.js"
doctype_list_js["Item"] = "public/js/rundinova_food_purchase.js"

doc_events = {
    "RundiNova Food Budget": {
        "validate": "rundinova_tech.rundinova_tech.doctype.rundinova_food_budget.rundinova_food_budget.validate_budget"
    },
    "RundiNova KPI Snapshot": {
        "validate": "rundinova_tech.rundinova_tech.doctype.rundinova_kpi_snapshot.rundinova_kpi_snapshot.validate_snapshot"
    },
    "RundiNova Food Expense": {
        "validate": "rundinova_tech.rundinova_tech.doctype.rundinova_food_expense.rundinova_food_expense.validate_expense",
    },
    "Purchase Invoice": {
        "on_submit": "rundinova_tech.rundinova_tech.doctype.rundinova_food_expense.rundinova_food_expense.sync_purchase_invoice",
        "on_cancel": "rundinova_tech.rundinova_tech.doctype.rundinova_food_expense.rundinova_food_expense.cancel_purchase_invoice_expenses",
    },
}

fixtures = [
    {"dt": "Role", "filters": [["name", "like", "RundiNova%"]]},
    {"dt": "Workflow", "filters": [["name", "like", "RundiNova%"]]},
]

after_install = "rundinova_tech.rundinova_tech.setup.seed"

# Workspace fixtures can reference custom roles while `bench migrate` syncs
# them, so create the role records before Frappe processes fixtures.
before_migrate = [
    "rundinova_tech.rundinova_tech.provisioning.roles.ensure_rundinova_roles",
]

# `bench migrate` re-syncs standard workspaces and resets is_hidden, so the
# module hiding must be re-applied after every migrate to stay effective.
after_migrate = [
    "rundinova_tech.rundinova_tech.provisioning.branding.sync_branding",
    "rundinova_tech.rundinova_tech.provisioning.form_layouts.sync_form_layouts",
    "rundinova_tech.rundinova_tech.setup.sync_dashboards",
    "rundinova_tech.rundinova_tech.bootstrap.hide_unused_workspaces",
    "rundinova_tech.rundinova_tech.bootstrap.hide_unused_desktop_icons",
    "rundinova_tech.rundinova_tech.setup.fix_company_currency",
]

# List and document permission checks share the same assignment boundary.
# Frappe's permission_query_conditions protects get_list; has_permission
# covers direct document reads and writes for assigned financial records.
_access_control = "rundinova_tech.rundinova_tech.access_control."
permission_query_conditions = {
    "RundiNova Food Budget": _access_control + "food_budget_query",
    "RundiNova Food Expense": _access_control + "food_expense_query",
    "RundiNova Food Progress": _access_control + "food_progress_query",
    "RundiNova Budget Review": _access_control + "budget_review_query",
    "RundiNova Expense": _access_control + "expense_query",
    "RundiNova Food Budget Item": _access_control + "food_budget_item_query",
}
has_permission = {
    doctype: _access_control + "has_permission"
    for doctype in permission_query_conditions
}
