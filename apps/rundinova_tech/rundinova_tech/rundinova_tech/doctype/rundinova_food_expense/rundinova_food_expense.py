import frappe
from frappe import _
from frappe.model.document import Document


ACTIVE_STATUSES = ("Submitted", "Approved", "Paid")


class RundiNovaFoodExpense(Document):
    def before_insert(self):
        set_expense_title(self)

    def validate(self):
        validate_expense(self)

    def on_update(self):
        refresh_budget(self.budget)

    def on_trash(self):
        refresh_budget(self.budget)


def set_expense_title(doc):
    if doc.expense_date and doc.item and doc.budget:
        doc.expense_title = f"Food Expense - {doc.expense_date} - {doc.item}"


def validate_expense(doc, _method=None):
    set_expense_title(doc)
    amount = frappe.utils.flt(doc.amount)
    if amount <= 0:
        frappe.throw(_("Expense amount must be greater than zero."))
    budget = frappe.get_doc("RundiNova Food Budget", doc.budget)
    purchase_date = frappe.utils.getdate(doc.expense_date)
    if purchase_date < frappe.utils.getdate(budget.period_start) or purchase_date > frappe.utils.getdate(budget.period_end):
        frappe.throw(_("The purchase date must be inside the selected budget period."))
    if doc.status in ACTIVE_STATUSES:
        existing = frappe.db.sql(
            """select coalesce(sum(amount), 0) from `tabRundiNova Food Expense`
               where budget=%s and status in ('Submitted','Approved','Paid') and name != %s""",
            (doc.budget, doc.name or ""),
        )[0][0]
        if frappe.utils.flt(existing) + amount > frappe.utils.flt(budget.approved_ceiling):
            frappe.throw(_("This expense would exceed the approved budget ceiling."))


def refresh_budget(budget_name):
    if not budget_name or not frappe.db.exists("RundiNova Food Budget", budget_name):
        return
    from rundinova_tech.rundinova_tech.doctype.rundinova_food_budget.rundinova_food_budget import refresh_budget_totals

    refresh_budget_totals(budget_name)


def sync_purchase_invoice(doc, _method=None):
    """Create submitted food expenses from a submitted Purchase Invoice.

    The invoice must carry the custom `rundinova_food_budget` field.  Every
    invoice line becomes one expense, preserving the invoice as the source of
    truth for supplier, amount and date.
    """
    budget_name = doc.get("rundinova_food_budget")
    if not budget_name:
        return
    for row in doc.items or []:
        if not row.item_code:
            continue
        existing = frappe.db.get_value(
            "RundiNova Food Expense",
            {"purchase_invoice": doc.name, "purchase_invoice_item": row.name},
            "name",
        )
        values = {
            "expense_date": doc.posting_date,
            "budget": budget_name,
            "item": row.item_code,
            "category": frappe.db.get_value("Item", row.item_code, "item_group"),
            "quantity": row.qty,
            "unit": row.uom,
            "amount": row.amount,
            "supplier": doc.supplier,
            "purchase_invoice": doc.name,
            "purchase_invoice_item": row.name,
            "status": "Submitted",
            "notes": _("Created from Purchase Invoice {0}").format(doc.name),
        }
        if existing:
            expense = frappe.get_doc("RundiNova Food Expense", existing)
            expense.update(values)
            expense.save(ignore_permissions=True)
        else:
            expense = frappe.get_doc({"doctype": "RundiNova Food Expense", **values})
            expense.insert(ignore_permissions=True)
    refresh_budget(budget_name)


def cancel_purchase_invoice_expenses(doc, _method=None):
    expenses = frappe.get_all(
        "RundiNova Food Expense",
        filters={"purchase_invoice": doc.name},
        pluck="name",
    )
    budgets = set()
    for name in expenses:
        expense = frappe.get_doc("RundiNova Food Expense", name)
        budgets.add(expense.budget)
        expense.status = "Cancelled"
        expense.save(ignore_permissions=True)
    for budget in budgets:
        refresh_budget(budget)
