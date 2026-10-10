import unittest
from datetime import date

from rundinova_core.application.food_expense import (
    FoodExpenseCommand,
    FoodExpensePolicy,
    validate_food_expense,
)


class FakeFoodExpensePolicyPort:
    def __init__(self, **overrides):
        values = {
            "period_start": date(2026, 1, 1),
            "period_end": date(2026, 1, 31),
            "approved_ceiling": 100000,
            "budget_committed": 50000,
            "item_committed": 40000,
            "item_planned": 80000,
        }
        values.update(overrides)
        self.policy = FoodExpensePolicy(**values)
        self.calls = []

    def get_food_expense_policy(self, budget, item, exclude_expense, include_limits):
        self.calls.append((budget, item, exclude_expense, include_limits))
        return self.policy


class TestFoodExpenseUseCase(unittest.TestCase):
    def command(self, **overrides):
        values = {
            "expense_name": "expense-1",
            "budget": "budget-1",
            "item": "rice",
            "purchase_date": date(2026, 1, 12),
            "amount": 10000,
            "status": "Submitted",
            "has_justification": False,
            "can_exceed_item_plan": False,
        }
        values.update(overrides)
        return FoodExpenseCommand(**values)

    def test_rejects_nonpositive_amount_before_loading_policy(self):
        port = FakeFoodExpensePolicyPort()
        self.assertEqual(
            validate_food_expense(self.command(amount=0), port),
            "amount_must_be_positive",
        )
        self.assertEqual(port.calls, [])

    def test_period_violation_precedes_amount_limits(self):
        port = FakeFoodExpensePolicyPort()
        result = validate_food_expense(
            self.command(purchase_date=date(2026, 2, 1), amount=200000), port
        )
        self.assertEqual(result, "purchase_date_outside_budget_period")

    def test_draft_still_checks_period_but_skips_committed_limits(self):
        port = FakeFoodExpensePolicyPort(approved_ceiling=1, item_planned=1)
        self.assertIsNone(validate_food_expense(self.command(status="Draft"), port))
        self.assertEqual(port.calls, [("budget-1", "rice", "expense-1", False)])

    def test_exceeding_item_plan_requires_director_authority_and_justification(self):
        port = FakeFoodExpensePolicyPort(item_committed=75000, item_planned=80000)
        self.assertEqual(
            validate_food_expense(self.command(amount=10000), port),
            "item_plan_exceeded_without_authority",
        )
        self.assertEqual(
            validate_food_expense(
                self.command(amount=10000, can_exceed_item_plan=True), port
            ),
            "item_plan_exceeded_without_justification",
        )
        self.assertIsNone(
            validate_food_expense(
                self.command(
                    amount=10000, can_exceed_item_plan=True, has_justification=True
                ),
                port,
            )
        )

    def test_budget_ceiling_still_applies_after_item_override(self):
        port = FakeFoodExpensePolicyPort(
            item_committed=75000,
            item_planned=80000,
            budget_committed=95000,
            approved_ceiling=100000,
        )
        self.assertEqual(
            validate_food_expense(
                self.command(
                    amount=10000, can_exceed_item_plan=True, has_justification=True
                ),
                port,
            ),
            "approved_ceiling_exceeded",
        )


if __name__ == "__main__":
    unittest.main()
