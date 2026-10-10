"""Framework-independent tests for dashboard currency semantics."""

import unittest

from rundinova_core.currency import currency_for_field


class TestCurrencyDomain(unittest.TestCase):
    def test_monetary_fields_use_burundian_francs(self):
        for field in (
            "amount",
            "actual_amount",
            "balance_amount",
            "business_value",
            "current_balance",
            "current_value",
            "expected_value",
            "total_planned_amount",
        ):
            with self.subTest(field=field):
                self.assertEqual(currency_for_field(field), "BIF")

    def test_counts_and_percentages_are_not_formatted_as_currency(self):
        for field in (
            "participants",
            "beneficiaries",
            "consumed_percent",
            "progress_percent",
            "target_achievement_percent",
            None,
        ):
            with self.subTest(field=field):
                self.assertIsNone(currency_for_field(field))


if __name__ == "__main__":
    unittest.main()
