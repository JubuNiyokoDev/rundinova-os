"""Framework-independent tests for cash validation and balance rules."""

import unittest

from rundinova_core.cash import (
    calculate_cash_account_balance,
    cash_account_opening_balance_violation,
    cash_movement_violation,
    food_expense_cash_mutation_violation,
    food_expense_cash_link_violation,
    food_expense_movement_fields,
)


class TestCashDomain(unittest.TestCase):
    def test_cash_linked_purchase_cannot_be_deleted_until_movement_is_cancelled(self):
        self.assertEqual(
            food_expense_cash_mutation_violation(
                has_active_cash_movement=True, deleting=True
            ),
            "cash_movement_must_be_cancelled_before_delete",
        )
        self.assertIsNone(
            food_expense_cash_mutation_violation(
                has_active_cash_movement=False, deleting=True
            )
        )

    def test_cash_linked_purchase_protected_fields_require_cancellation_before_change(self):
        previous = {"amount": 45000, "status": "Paid", "notes": "market purchase"}
        unchanged = dict(previous)
        changed = {**previous, "amount": 46000}

        self.assertIsNone(
            food_expense_cash_mutation_violation(
                has_active_cash_movement=True,
                previous_values=previous,
                current_values=unchanged,
            )
        )
        self.assertIsNone(
            food_expense_cash_mutation_violation(
                has_active_cash_movement=True,
                previous_values=previous,
                current_values={**previous, "notes": "updated note"},
            )
        )
        self.assertEqual(
            food_expense_cash_mutation_violation(
                has_active_cash_movement=True,
                previous_values=previous,
                current_values=changed,
            ),
            "cash_movement_must_be_cancelled_before_change",
        )

    def test_income_and_expense_update_the_source_account(self):
        movements = [
            ("Income", "cash", None, 100.0),
            ("Expense", "cash", None, 25.0),
        ]

        self.assertEqual(calculate_cash_account_balance(10.0, "cash", movements), 85.0)

    def test_transfer_debits_source_and_credits_destination(self):
        transfer = [("Transfer", "cash-a", "cash-b", 40.0)]

        self.assertEqual(calculate_cash_account_balance(100.0, "cash-a", transfer), 60.0)
        self.assertEqual(calculate_cash_account_balance(5.0, "cash-b", transfer), 45.0)

    def test_movement_validation_keeps_existing_precedence(self):
        self.assertEqual(
            cash_movement_violation(
                amount=0,
                movement_type="Transfer",
                destination_account=None,
                status="Submitted",
                evidence_present=False,
            ),
            "amount_must_be_positive",
        )
        self.assertEqual(
            cash_movement_violation(
                amount=10,
                movement_type="Transfer",
                destination_account=None,
                status="Submitted",
                evidence_present=False,
            ),
            "transfer_requires_destination",
        )

    def test_destinations_are_transfer_only(self):
        self.assertEqual(
            cash_movement_violation(
                amount=10,
                movement_type="Income",
                destination_account="cash-b",
                status="Draft",
                evidence_present=False,
            ),
            "destination_only_valid_for_transfer",
        )

    def test_evidence_requirement_depends_on_status(self):
        base = {
            "amount": 10,
            "movement_type": "Expense",
            "destination_account": None,
            "evidence_present": False,
        }

        self.assertEqual(
            cash_movement_violation(**base, status="Approved"), "evidence_required"
        )
        self.assertIsNone(cash_movement_violation(**base, status="Draft"))
        self.assertIsNone(
            cash_movement_violation(
                **{**base, "evidence_present": True}, status="Reconciled"
            )
        )

    def test_opening_balance_must_not_be_negative(self):
        self.assertEqual(
            cash_account_opening_balance_violation(-0.01),
            "opening_balance_cannot_be_negative",
        )
        self.assertIsNone(cash_account_opening_balance_violation(0))

    def test_cash_link_requires_paid_purchase_and_prevents_duplicates(self):
        self.assertEqual(
            food_expense_cash_link_violation(expense_status="Submitted"),
            "food_expense_must_be_paid",
        )
        self.assertEqual(
            food_expense_cash_link_violation(expense_status="Paid", duplicate_movement=True),
            "food_expense_already_linked",
        )
        self.assertIsNone(food_expense_cash_link_violation(expense_status="Paid"))

    def test_food_expense_derives_cash_movement_fields(self):
        movement = food_expense_movement_fields(
            {
                "expense_date": "2026-10-07",
                "item": "Riz",
                "category": "Cereals",
                "quantity": 5,
                "unit": "Kg",
                "amount": 72500,
                "supplier": "Market Supplier",
                "receipt": "/private/files/rice-receipt.jpg",
            }
        )

        self.assertEqual(movement["movement_date"], "2026-10-07")
        self.assertEqual(movement["movement_type"], "Expense")
        self.assertEqual(movement["amount"], 72500)
        self.assertEqual(movement["category"], "Cereals")
        self.assertEqual(movement["destination_type"], "Supplier")
        self.assertEqual(movement["description"], "Food purchase: 5 Kg Riz")
        self.assertEqual(movement["evidence"], "/private/files/rice-receipt.jpg")


if __name__ == "__main__":
    unittest.main()
