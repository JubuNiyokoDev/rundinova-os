import unittest

from rundinova_core.application.food_purchase import (
	FoodBudget,
	FoodBudgetLine,
	FoodItemMetadata,
	FoodProgressRecord,
	FoodPurchaseCommand,
	FoodPurchaseError,
	FoodPurchaseResult,
	record_food_purchases,
	record_food_purchase,
)


class FakeFoodPurchasePort:
	def __init__(self, progress=None):
		self.budget = FoodBudget(
			name="budget-1",
			items=(FoodBudgetLine(item="rice", unit="kg"),),
		)
		self.progress = progress
		self.calls = []
		self.expense_values = None

	def get_readable_budget(self, budget):
		self.calls.append(("get_budget", budget))
		return self.budget

	def get_readable_progress(self, progress):
		self.calls.append(("get_progress", progress))
		return self.progress

	def find_readable_progress(self, budget, item):
		self.calls.append(("find_progress", budget, item))
		return self.progress

	def create_progress(self, budget, item):
		self.calls.append(("create_progress", budget, item))
		self.progress = FoodProgressRecord(name="progress-new", budget=budget, item=item)
		return self.progress

	def get_item_metadata(self, item):
		self.calls.append(("get_item", item))
		return FoodItemMetadata(category="Cereals", stock_unit="bag")

	def insert_food_expense(self, values):
		self.calls.append(("insert_expense",))
		self.expense_values = values
		return FoodPurchaseResult(name="expense-1", title="Rice purchase", progress=values["food_progress"])


class TestFoodPurchaseUseCase(unittest.TestCase):
	def command(self, **overrides):
		values = {
			"budget": "budget-1",
			"item": "rice",
			"expense_date": "2026-01-12",
			"quantity": 5.0,
			"amount": 45000.0,
		}
		values.update(overrides)
		return FoodPurchaseCommand(**values)

	def test_records_purchase_against_existing_readable_progress(self):
		port = FakeFoodPurchasePort(
			FoodProgressRecord(name="progress-1", budget="budget-1", item="rice")
		)

		result = record_food_purchase(self.command(), port)

		self.assertEqual(result.as_dict(), {
			"name": "expense-1",
			"title": "Rice purchase",
			"progress": "progress-1",
		})
		self.assertNotIn(("create_progress", "budget-1", "rice"), port.calls)
		self.assertEqual(port.expense_values["unit"], "kg")
		self.assertEqual(port.expense_values["category"], "Cereals")
		self.assertEqual(port.expense_values["status"], "Submitted")

	def test_creates_missing_progress_and_uses_item_stock_unit_fallback(self):
		port = FakeFoodPurchasePort()
		port.budget = FoodBudget(
			name="budget-1", items=(FoodBudgetLine(item="rice", unit=None),)
		)

		record_food_purchase(self.command(payment_method="Mobile Money"), port)

		self.assertIn(("create_progress", "budget-1", "rice"), port.calls)
		self.assertEqual(port.expense_values["food_progress"], "progress-new")
		self.assertEqual(port.expense_values["unit"], "bag")
		self.assertEqual(port.expense_values["payment_method"], "Mobile Money")

	def test_rejects_item_outside_budget_before_any_write(self):
		port = FakeFoodPurchasePort()
		with self.assertRaises(FoodPurchaseError) as raised:
			record_food_purchase(self.command(item="beans"), port)

		self.assertEqual(raised.exception.code, "item_not_in_budget")
		self.assertFalse(any(call[0] in {"create_progress", "insert_expense"} for call in port.calls))

	def test_rejects_progress_for_another_budget_or_item(self):
		port = FakeFoodPurchasePort(
			FoodProgressRecord(name="progress-2", budget="another-budget", item="rice")
		)
		with self.assertRaises(FoodPurchaseError) as raised:
			record_food_purchase(self.command(food_progress="progress-2"), port)

		self.assertEqual(raised.exception.code, "progress_mismatch")
		self.assertNotIn(("insert_expense",), port.calls)

	def test_explicit_progress_uses_permission_checked_port_path(self):
		port = FakeFoodPurchasePort(
			FoodProgressRecord(name="progress-1", budget="budget-1", item="rice")
		)

		record_food_purchase(self.command(food_progress="progress-1"), port)

		self.assertIn(("get_progress", "progress-1"), port.calls)
		self.assertNotIn(("find_progress", "budget-1", "rice"), port.calls)

	def test_records_multiple_market_items_through_the_same_validated_use_case(self):
		port = FakeFoodPurchasePort(
			FoodProgressRecord(name="progress-1", budget="budget-1", item="rice")
		)

		results = record_food_purchases((self.command(), self.command(amount=12000)), port)

		self.assertEqual(len(results), 2)
		self.assertEqual(sum(call[0] == "insert_expense" for call in port.calls), 2)

	def test_rejects_an_empty_market_purchase(self):
		port = FakeFoodPurchasePort()
		with self.assertRaises(FoodPurchaseError) as raised:
			record_food_purchases((), port)

		self.assertEqual(raised.exception.code, "purchase_lines_required")
		self.assertEqual(port.calls, [])


if __name__ == "__main__":
	unittest.main()
