"""Record a food purchase through a persistence and permission port."""

from dataclasses import dataclass
from typing import Protocol


class FoodPurchaseError(ValueError):
	"""A stable business error code raised before writing a purchase."""

	def __init__(self, code):
		self.code = code
		super().__init__(code)


@dataclass(frozen=True)
class FoodBudgetLine:
	item: str
	unit: str | None


@dataclass(frozen=True)
class FoodBudget:
	name: str
	items: tuple[FoodBudgetLine, ...]


@dataclass(frozen=True)
class FoodProgressRecord:
	name: str
	budget: str
	item: str


@dataclass(frozen=True)
class FoodItemMetadata:
	category: str | None
	stock_unit: str | None


@dataclass(frozen=True)
class FoodPurchaseCommand:
	budget: str
	item: str
	expense_date: str
	quantity: float
	amount: float
	payment_method: str = "Cash"
	supplier: str | None = None
	receipt: str | None = None
	notes: str | None = None
	food_progress: str | None = None


@dataclass(frozen=True)
class FoodPurchaseResult:
	name: str
	title: str | None
	progress: str

	def as_dict(self):
		return {"name": self.name, "title": self.title, "progress": self.progress}


class FoodPurchasePort(Protocol):
	"""Persistence adapter; read methods must enforce the caller's read access."""

	def get_readable_budget(self, budget: str) -> FoodBudget: ...

	def get_readable_progress(self, progress: str) -> FoodProgressRecord: ...

	def find_readable_progress(self, budget: str, item: str) -> FoodProgressRecord | None: ...

	def create_progress(self, budget: str, item: str) -> FoodProgressRecord: ...

	def get_item_metadata(self, item: str) -> FoodItemMetadata: ...

	def insert_food_expense(self, values: dict[str, object]) -> FoodPurchaseResult: ...


def record_food_purchase(command: FoodPurchaseCommand, port: FoodPurchasePort) -> FoodPurchaseResult:
	"""Resolve the budget line and progress, then ask the adapter to insert.

	All Frappe document access and permission checks stay in the adapter. The
	use case owns the relationship checks and maps a purchase command into the
	existing expense workflow, whose controller continues validating limits.
	"""
	budget = port.get_readable_budget(command.budget)
	line = next((row for row in budget.items if row.item == command.item), None)
	if not line:
		raise FoodPurchaseError("item_not_in_budget")

	if command.food_progress:
		progress = port.get_readable_progress(command.food_progress)
	else:
		progress = port.find_readable_progress(budget.name, command.item)
		if progress is None:
			progress = port.create_progress(budget.name, command.item)

	if progress.budget != budget.name or progress.item != command.item:
		raise FoodPurchaseError("progress_mismatch")

	item = port.get_item_metadata(command.item)
	return port.insert_food_expense(
		{
			"expense_date": command.expense_date,
			"budget": budget.name,
			"food_progress": progress.name,
			"item": command.item,
			"category": item.category,
			"quantity": command.quantity,
			"unit": line.unit or item.stock_unit,
			"amount": command.amount,
			"supplier": command.supplier,
			"payment_method": command.payment_method,
			"receipt": command.receipt,
			"notes": command.notes,
			"status": "Submitted",
		}
	)


def record_food_purchases(
	commands: tuple[FoodPurchaseCommand, ...], port: FoodPurchasePort
) -> tuple[FoodPurchaseResult, ...]:
	"""Record one market visit containing multiple budgeted food items.

	The Frappe adapter runs this use case inside one RPC transaction, so a
	validation failure on any line rolls back the full market purchase.
	"""
	if not commands:
		raise FoodPurchaseError("purchase_lines_required")
	return tuple(record_food_purchase(command, port) for command in commands)
