"""Application use case for validating food-expense policy."""

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from rundinova_core.food import (
	ACTIVE_EXPENSE_STATUSES,
	food_expense_amount_violation,
	food_expense_limit_violation,
	food_expense_period_violation,
)


@dataclass(frozen=True)
class FoodExpenseCommand:
	expense_name: str | None
	budget: str
	item: str | None
	purchase_date: date
	amount: float
	status: str
	has_justification: bool
	can_exceed_item_plan: bool


@dataclass(frozen=True)
class FoodExpensePolicy:
	period_start: date
	period_end: date
	approved_ceiling: float
	budget_committed: float
	item_committed: float
	item_planned: float


class FoodExpensePolicyPort(Protocol):
	def get_food_expense_policy(
		self,
		budget: str,
		item: str | None,
		exclude_expense: str | None,
		include_limits: bool,
	) -> FoodExpensePolicy: ...


def validate_food_expense(
	command: FoodExpenseCommand, port: FoodExpensePolicyPort
) -> str | None:
	"""Return the first food-expense policy violation in existing order."""
	violation = food_expense_amount_violation(command.amount)
	if violation:
		return violation

	policy = port.get_food_expense_policy(
		command.budget,
		command.item,
		command.expense_name,
		command.status in ACTIVE_EXPENSE_STATUSES,
	)
	violation = food_expense_period_violation(
		command.purchase_date, policy.period_start, policy.period_end
	)
	if violation:
		return violation
	if command.status not in ACTIVE_EXPENSE_STATUSES:
		return None

	return food_expense_limit_violation(
		status=command.status,
		amount=command.amount,
		budget_committed=policy.budget_committed,
		approved_ceiling=policy.approved_ceiling,
		item_committed=policy.item_committed,
		item_planned=policy.item_planned,
		can_exceed_item_plan=command.can_exceed_item_plan,
		has_justification=command.has_justification,
	)
