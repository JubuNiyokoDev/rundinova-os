"""Framework-independent cash movement and account balance rules."""

from collections.abc import Iterable


MOVEMENTS_REQUIRING_EVIDENCE = frozenset(("Submitted", "Approved", "Reconciled"))
BALANCE_STATUSES = ("Approved", "Reconciled")
FOOD_EXPENSE_CASH_PROTECTED_FIELDS = (
	"expense_date",
	"budget",
	"item",
	"category",
	"quantity",
	"unit",
	"amount",
	"supplier",
	"receipt",
	"status",
	"purchase_invoice",
	"purchase_invoice_item",
)


def cash_movement_violation(
    *,
    amount,
    movement_type,
    destination_account,
    status,
    evidence_present,
):
    """Return the first movement rule violation in the current policy order."""
    if amount <= 0:
        return "amount_must_be_positive"
    if movement_type == "Transfer" and not destination_account:
        return "transfer_requires_destination"
    if movement_type != "Transfer" and destination_account:
        return "destination_only_valid_for_transfer"
    if status in MOVEMENTS_REQUIRING_EVIDENCE and not evidence_present:
        return "evidence_required"
    return None


def cash_account_opening_balance_violation(opening_balance):
    if opening_balance < 0:
        return "opening_balance_cannot_be_negative"
    return None


def food_expense_cash_link_violation(*, expense_status, duplicate_movement=False):
    """Return the first rule violation for a food expense cash link."""
    if expense_status != "Paid":
        return "food_expense_must_be_paid"
    if duplicate_movement:
        return "food_expense_already_linked"
    return None


def food_expense_cash_mutation_violation(
	*, has_active_cash_movement, deleting=False, previous_values=None, current_values=None
):
	"""Require cancellation before deleting or changing cash-linked purchase data."""
	if not has_active_cash_movement:
		return None
	if deleting:
		return "cash_movement_must_be_cancelled_before_delete"
	if previous_values is None:
		return None
	current_values = current_values or {}
	if any(
		current_values.get(field) != previous_values.get(field)
		for field in FOOD_EXPENSE_CASH_PROTECTED_FIELDS
	):
		return "cash_movement_must_be_cancelled_before_change"
	return None


def food_expense_movement_fields(expense):
    """Derive the cash movement fields that belong to a paid food purchase."""
    item = expense.get("item") or "Food purchase"
    quantity = expense.get("quantity")
    unit = expense.get("unit")
    supplier = expense.get("supplier")
    quantity_text = f"{quantity:g}" if isinstance(quantity, (int, float)) else quantity
    item_detail = " ".join(str(value) for value in (quantity_text, unit, item) if value)

    return {
        "movement_date": expense.get("expense_date"),
        "movement_type": "Expense",
        "destination_account": None,
        "amount": expense.get("amount"),
        "category": expense.get("category") or "Food",
        "source_type": None,
        "source_description": None,
        "destination_type": "Supplier" if supplier else "Expense",
        "destination_description": supplier or item,
        "description": f"Food purchase: {item_detail}",
        "expense": None,
        "evidence": expense.get("receipt"),
    }


def calculate_cash_account_balance(opening_balance, account_name, movements: Iterable[tuple]):
    """Apply approved movement rows to an account's opening balance."""
    balance = opening_balance
    for movement_type, source_account, destination_account, amount in movements:
        if source_account == account_name:
            balance += amount if movement_type == "Income" else -amount
        if movement_type == "Transfer" and destination_account == account_name:
            balance += amount
    return balance
