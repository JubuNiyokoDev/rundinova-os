"""Framework-independent tests for the food-budget business rules."""

import unittest
from datetime import date

from rundinova_core.food import (
    calculate_food_budget_plan,
    calculate_food_budget_usage,
    food_expense_amount_violation,
    food_expense_limit_violation,
    food_expense_period_violation,
    validate_food_budget_plan,
)


class TestFoodBudgetDomain(unittest.TestCase):
    def test_budget_plan_totals_match_current_monthly_formulas(self):
        plan = calculate_food_budget_plan([145000.0, 90000.0, 33000.0], 6)

        self.assertEqual(plan["total_planned_amount"], 268000.0)
        self.assertEqual(plan["annual_planned_amount"], 3216000.0)
        self.assertAlmostEqual(plan["daily_planned_amount"], 8933.333333333334)
        self.assertAlmostEqual(plan["per_person_daily_amount"], 1488.888888888889)

    def test_zero_people_keeps_existing_zero_fallback(self):
        plan = calculate_food_budget_plan([120.0], 0)
        self.assertEqual(plan["per_person_daily_amount"], 0)
        self.assertIsNone(validate_food_budget_plan(120.0, 120.0, 0, False, False))

    def test_budget_validation_keeps_existing_precedence(self):
        self.assertEqual(
            validate_food_budget_plan(121.0, 120.0, -1, True, False),
            "planned_total_exceeds_ceiling",
        )
        self.assertEqual(
            validate_food_budget_plan(120.0, 120.0, -1, True, False),
            "covered_people_must_be_positive",
        )
        self.assertEqual(
            validate_food_budget_plan(120.0, 120.0, 1, True, False),
            "branch_requires_cost_center",
        )

    def test_budget_usage_separates_committed_and_paid_amounts(self):
        usage = calculate_food_budget_usage(
            100.0,
            [
                (10.0, "Submitted"),
                (15.0, "Approved"),
                (40.0, "Paid"),
                (500.0, "Cancelled"),
            ],
        )

        self.assertEqual(usage["committed_amount"], 65.0)
        self.assertEqual(usage["actual_amount"], 40.0)
        self.assertEqual(usage["balance_amount"], 35.0)
        self.assertEqual(usage["consumed_percent"], 65.0)

    def test_amount_and_period_rules(self):
        self.assertEqual(food_expense_amount_violation(0), "amount_must_be_positive")
        self.assertIsNone(food_expense_amount_violation(0.01))
        start = date(2026, 1, 1)
        end = date(2026, 1, 31)
        self.assertIsNone(food_expense_period_violation(start, start, end))
        self.assertIsNone(food_expense_period_violation(end, start, end))
        self.assertEqual(
            food_expense_period_violation(date(2026, 2, 1), start, end),
            "purchase_date_outside_budget_period",
        )

    def test_item_limit_precedes_budget_ceiling(self):
        violation = food_expense_limit_violation(
            status="Submitted",
            amount=20.0,
            budget_committed=90.0,
            approved_ceiling=100.0,
            item_committed=90.0,
            item_planned=80.0,
            can_exceed_item_plan=False,
            has_justification=False,
        )
        self.assertEqual(violation, "item_plan_exceeded_without_authority")

    def test_purchase_within_item_and_budget_limits_passes(self):
        self.assertIsNone(
            food_expense_limit_violation(
                status="Approved",
                amount=20.0,
                budget_committed=40.0,
                approved_ceiling=100.0,
                item_committed=30.0,
                item_planned=60.0,
                can_exceed_item_plan=False,
                has_justification=False,
            )
        )

    def test_director_requires_justification_and_cannot_bypass_ceiling(self):
        common = {
            "status": "Paid",
            "amount": 20.0,
            "budget_committed": 90.0,
            "approved_ceiling": 100.0,
            "item_committed": 70.0,
            "item_planned": 80.0,
            "can_exceed_item_plan": True,
        }
        self.assertEqual(
            food_expense_limit_violation(**common, has_justification=False),
            "item_plan_exceeded_without_justification",
        )
        self.assertEqual(
            food_expense_limit_violation(**common, has_justification=True),
            "approved_ceiling_exceeded",
        )

    def test_inactive_expenses_do_not_consume_budget_limits(self):
        self.assertIsNone(
            food_expense_limit_violation(
                status="Cancelled",
                amount=200.0,
                budget_committed=100.0,
                approved_ceiling=100.0,
                item_committed=100.0,
                item_planned=10.0,
                can_exceed_item_plan=False,
                has_justification=False,
            )
        )


if __name__ == "__main__":
    unittest.main()
