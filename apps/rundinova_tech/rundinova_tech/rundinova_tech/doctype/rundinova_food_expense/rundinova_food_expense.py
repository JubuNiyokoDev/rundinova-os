import json

import frappe
from frappe import _
from frappe.model.document import Document

from rundinova_core.application.food_purchase import (
	FoodPurchaseCommand,
	FoodPurchaseError,
	record_food_purchases as execute_food_purchases,
	record_food_purchase as execute_food_purchase,
)
from rundinova_core.application.food_expense import (
	FoodExpenseCommand,
	validate_food_expense,
)
from rundinova_core.application.food_progress_link import ensure_food_progress_link
from rundinova_core.cash import (
	FOOD_EXPENSE_CASH_PROTECTED_FIELDS,
	food_expense_cash_mutation_violation,
)

from .food_expense_policy_adapter import FrappeFoodExpensePolicyPort
from .food_progress_link_adapter import FrappeFoodProgressLinkPort
from .food_purchase_adapter import FrappeFoodPurchasePort

FOOD_EXPENSE_POLICY_MESSAGES = {
	"amount_must_be_positive": "Expense amount must be greater than zero.",
	"purchase_date_outside_budget_period": "The purchase date must be inside the selected budget period.",
	"item_plan_exceeded_without_authority": "This expense would exceed the planned amount for {item}. Only the Director can approve an over-budget entry with a justification.",
	"item_plan_exceeded_without_justification": "A justification note is required when exceeding the planned amount for this item.",
	"approved_ceiling_exceeded": "This expense would exceed the approved budget ceiling.",
}


class RundiNovaFoodExpense(Document):
    def before_insert(self):
        set_expense_title(self)

    def validate(self):
        validate_expense(self)

    def on_update(self):
        refresh_budget(self.budget)
        refresh_food_progress(self)

    def on_trash(self):
        ensure_cash_link_not_stale(self, deleting=True)
        refresh_budget(self.budget)
        refresh_food_progress(self)


def set_expense_title(doc):
    if doc.expense_date and doc.item and doc.budget:
        item_title = frappe.db.get_value("Item", doc.item, "item_name") or doc.item
        doc.expense_title = f"Achat alimentaire · {frappe.utils.getdate(doc.expense_date).strftime('%d/%m/%Y')} · {item_title}"


def auto_link_food_progress(doc):
    doc.food_progress = ensure_food_progress_link(
        doc.budget,
        doc.item,
        doc.food_progress,
        FrappeFoodProgressLinkPort(),
    )


def refresh_food_progress(doc):
    if doc.budget and doc.item:
        auto_link_food_progress(doc)
        if doc.food_progress:
            from rundinova_tech.rundinova_tech.doctype.rundinova_food_progress.rundinova_food_progress import recalculate

            progress = frappe.get_doc("RundiNova Food Progress", doc.food_progress)
            recalculate(progress)
            progress.db_update()


def validate_expense(doc, _method=None):
    ensure_cash_link_not_stale(doc)
    auto_link_food_progress(doc)
    if doc.item and not doc.category:
        doc.category = frappe.db.get_value("Item", doc.item, "item_group")
    if doc.item and not doc.unit and doc.budget:
        doc.unit = frappe.db.get_value(
            "RundiNova Food Budget Item",
            {"parent": doc.budget, "item": doc.item},
            "unit",
        ) or frappe.db.get_value("Item", doc.item, "stock_uom")
    set_expense_title(doc)
    violation = validate_food_expense(
        FoodExpenseCommand(
            expense_name=doc.name,
            budget=doc.budget,
            item=doc.item,
            purchase_date=frappe.utils.getdate(doc.expense_date),
            amount=frappe.utils.flt(doc.amount),
            status=doc.status,
            has_justification=bool(doc.notes),
            can_exceed_item_plan=(
                frappe.session.user == "Administrator"
                or "RundiNova Director" in frappe.get_roles(frappe.session.user)
            ),
        ),
        FrappeFoodExpensePolicyPort(),
    )
    if violation:
        message = _(FOOD_EXPENSE_POLICY_MESSAGES[violation])
        if violation == "item_plan_exceeded_without_authority":
            message = message.format(item=doc.item)
        frappe.throw(message)


@frappe.whitelist()
def record_food_purchase(
	budget,
	item,
	expense_date,
	quantity,
	amount,
	payment_method="Cash",
	supplier=None,
	receipt=None,
	notes=None,
	food_progress=None,
):
	"""Record one purchase from a selected food-budget line.

	The linked budget and item are revalidated on the server. The UI is only a
	shortcut; the existing expense controller still enforces dates and limits.
	"""
	command = FoodPurchaseCommand(
		budget=budget,
		item=item,
		expense_date=expense_date,
		quantity=frappe.utils.flt(quantity),
		amount=frappe.utils.flt(amount),
		payment_method=payment_method,
		supplier=supplier,
		receipt=receipt,
		notes=notes,
		food_progress=food_progress,
	)
	messages = {
		"item_not_in_budget": _("This item is not part of the selected food budget."),
		"progress_mismatch": _("The selected item does not match its food progress record."),
	}
	try:
		result = execute_food_purchase(command, FrappeFoodPurchasePort())
	except FoodPurchaseError as error:
		frappe.throw(messages[error.code])
	return result.as_dict()


@frappe.whitelist()
def record_food_purchases(
	budget,
	items,
	expense_date,
	payment_method="Cash",
	supplier=None,
	receipt=None,
	notes=None,
):
	"""Record all lines from one market visit in the current RPC transaction."""
	rows = json.loads(items) if isinstance(items, str) else items
	if not isinstance(rows, list) or not rows:
		frappe.throw(_("Add at least one item to this purchase."))
	commands = []
	for row in rows:
		if not isinstance(row, dict) or not row.get("item"):
			frappe.throw(_("Every purchase line needs an item."))
		commands.append(
			FoodPurchaseCommand(
				budget=budget,
				item=row["item"],
				expense_date=expense_date,
				quantity=frappe.utils.flt(row.get("quantity")),
				amount=frappe.utils.flt(row.get("amount")),
				payment_method=payment_method,
				supplier=supplier,
				receipt=receipt,
				notes=notes,
			)
		)
	messages = {
			"item_not_in_budget": _("This item is not part of the selected food budget."),
			"progress_mismatch": _("The selected item does not match its food progress record."),
			"purchase_lines_required": _("Add at least one item to this purchase."),
		}
	try:
		results = execute_food_purchases(tuple(commands), FrappeFoodPurchasePort())
	except FoodPurchaseError as error:
		frappe.throw(messages[error.code])
	return [result.as_dict() for result in results]


def ensure_cash_link_not_stale(doc, deleting=False):
    """Require linked cash movements to be cancelled before a purchase changes."""
    if not doc.name:
        return
    linked = frappe.get_all(
        "RundiNova Cash Movement",
        filters={
            "food_expense": doc.name,
            "status": ["!=", "Cancelled"],
            "docstatus": ["<", 2],
        },
        fields=["name"],
        limit=1,
    )
    if not linked:
        return
    previous = doc.get_doc_before_save() if not deleting else None
    previous_values = (
        {fieldname: previous.get(fieldname) for fieldname in FOOD_EXPENSE_CASH_PROTECTED_FIELDS}
        if previous
        else None
    )
    current_values = {
        fieldname: doc.get(fieldname) for fieldname in FOOD_EXPENSE_CASH_PROTECTED_FIELDS
    }
    violation = food_expense_cash_mutation_violation(
        has_active_cash_movement=True,
        deleting=deleting,
        previous_values=previous_values,
        current_values=current_values,
    )
    messages = {
        "cash_movement_must_be_cancelled_before_delete": _(
            "Cancel the linked cash movement before deleting this food purchase."
        ),
        "cash_movement_must_be_cancelled_before_change": _(
            "Cancel the linked cash movement before changing this food purchase."
        ),
    }
    if violation:
        frappe.throw(messages[violation])


def refresh_budget(budget_name):
    if not budget_name or not frappe.db.exists("RundiNova Food Budget", budget_name):
        return
    from rundinova_tech.rundinova_tech.doctype.rundinova_food_budget.rundinova_food_budget import refresh_budget_totals

    refresh_budget_totals(budget_name)


def sync_purchase_invoice(doc, _method=None):
	"""Adapt a submitted ERPNext invoice and run the independent use case."""
	from rundinova_core.application.food_invoice import sync_food_invoice

	from .food_invoice_adapter import FrappeFoodInvoicePort, food_invoice_command

	return sync_food_invoice(food_invoice_command(doc), FrappeFoodInvoicePort())


def cancel_purchase_invoice_expenses(doc, _method=None):
	"""Adapt cancellation and delegate linked-expense handling to core."""
	from rundinova_core.application.food_invoice import cancel_food_invoice

	from .food_invoice_adapter import FrappeFoodInvoicePort, food_invoice_command

	return cancel_food_invoice(food_invoice_command(doc), FrappeFoodInvoicePort())
