app_name = "rundinova_tech"
app_title = "RundiNova Tech"
app_publisher = "RundiNova Tech"
app_description = "Operations, budgets, impact and governance for RundiNova Tech"
app_email = "operations@rundinova.com"
app_license = "MIT"

api_version = 1

required_apps = ["frappe", "erpnext", "hrms", "crm"]

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
after_migrate = "rundinova_tech.rundinova_tech.setup.sync_dashboards"
