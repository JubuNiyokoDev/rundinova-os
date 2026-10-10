"""Synchronize food expenses with supplier invoices through a persistence port."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class FoodInvoiceLine:
	name: str
	item: str | None
	quantity: float
	unit: str | None
	amount: float


@dataclass(frozen=True)
class FoodInvoiceCommand:
	name: str
	budget: str | None
	posting_date: str
	supplier: str | None
	source_note: str
	items: tuple[FoodInvoiceLine, ...]


@dataclass(frozen=True)
class FoodInvoiceSyncResult:
	created: int
	updated: int


@dataclass(frozen=True)
class FoodInvoiceCancelResult:
	cancelled: int


class FoodInvoicePort(Protocol):
	"""Frappe adapter port for invoice-linked food expenses."""

	def find_expense(self, invoice: str, invoice_line: str) -> str | None: ...

	def get_item_category(self, item: str) -> str | None: ...

	def create_expense(self, values: dict[str, object]) -> None: ...

	def update_expense(self, name: str, values: dict[str, object]) -> None: ...

	def list_invoice_expenses(self, invoice: str) -> list[tuple[str, str | None]]: ...

	def cancel_expense(self, name: str) -> None: ...

	def refresh_budget(self, budget: str) -> None: ...


def sync_food_invoice(command: FoodInvoiceCommand, port: FoodInvoicePort) -> FoodInvoiceSyncResult:
	"""Create or update exactly one expense per eligible invoice line."""
	if not command.budget:
		return FoodInvoiceSyncResult(created=0, updated=0)

	created = updated = 0
	for line in command.items:
		if not line.item:
			continue

		values = {
			"expense_date": command.posting_date,
			"budget": command.budget,
			"item": line.item,
			"category": port.get_item_category(line.item),
			"quantity": line.quantity,
			"unit": line.unit,
			"amount": line.amount,
			"supplier": command.supplier,
			"purchase_invoice": command.name,
			"purchase_invoice_item": line.name,
			"status": "Submitted",
			"notes": command.source_note,
		}
		existing = port.find_expense(command.name, line.name)
		if existing:
			port.update_expense(existing, values)
			updated += 1
		else:
			port.create_expense(values)
			created += 1

	port.refresh_budget(command.budget)
	return FoodInvoiceSyncResult(created=created, updated=updated)


def cancel_food_invoice(command: FoodInvoiceCommand, port: FoodInvoicePort) -> FoodInvoiceCancelResult:
	"""Cancel every linked expense and refresh each affected budget once."""
	rows = port.list_invoice_expenses(command.name)
	budgets = []
	for name, budget in rows:
		port.cancel_expense(name)
		if budget and budget not in budgets:
			budgets.append(budget)

	for budget in budgets:
		port.refresh_budget(budget)
	return FoodInvoiceCancelResult(cancelled=len(rows))
