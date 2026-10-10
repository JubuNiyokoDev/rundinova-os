import unittest
from datetime import date

from rundinova_core.food import calculate_food_progress


class TestFoodProgressCalculation(unittest.TestCase):
    def test_aggregates_only_active_expenses_and_calculates_remaining_days(self):
        result = calculate_food_progress(
            planned_quantity=20,
            unit="kg",
            planned_amount=100000,
            expenses=((5, 45000, "Paid"), (2, 10000, "Draft"), (3, 25000, "Submitted")),
            today=date(2026, 1, 10),
            period_end=date(2026, 1, 31),
        )

        self.assertEqual(result["unit"], "kg")
        self.assertEqual(result["consumed_quantity"], 8)
        self.assertEqual(result["consumed_amount"], 70000)
        self.assertEqual(result["remaining_amount"], 30000)
        self.assertEqual(result["consumed_percent"], 70)
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["remaining_days"], 21)

    def test_warning_threshold_and_zero_plan(self):
        warning = calculate_food_progress(
            planned_quantity=1,
            unit="sac",
            planned_amount=100,
            expenses=((1, 90, "Approved"),),
        )
        zero_plan = calculate_food_progress(
            planned_quantity=0,
            unit="kg",
            planned_amount=0,
            expenses=((1, 10, "Paid"),),
        )

        self.assertEqual(warning["status"], "Warning")
        self.assertEqual(warning["consumed_percent"], 90)
        self.assertEqual(zero_plan["status"], "Over")
        self.assertEqual(zero_plan["consumed_percent"], 0)

    def test_over_budget_caps_percent_and_expired_budget_has_zero_days(self):
        result = calculate_food_progress(
            planned_quantity=1,
            unit="kg",
            planned_amount=100,
            expenses=((2, 125, "Paid"),),
            today=date(2026, 2, 1),
            period_end=date(2026, 1, 31),
        )

        self.assertEqual(result["status"], "Over")
        self.assertEqual(result["consumed_percent"], 100)
        self.assertEqual(result["remaining_amount"], -25)
        self.assertEqual(result["remaining_days"], 0)


if __name__ == "__main__":
    unittest.main()
