"""Framework-independent tests for general expense validation."""

import unittest

from rundinova_core.expense import expense_validation_actions


class TestExpenseDomain(unittest.TestCase):
    def test_amount_error_has_precedence(self):
        self.assertEqual(
            expense_validation_actions(
                amount=0,
                status="Paid",
                receipt_present=False,
                approved_by_present=False,
                payment_method=None,
            ),
            ("amount_must_be_positive",),
        )

    def test_submitted_expense_requires_evidence(self):
        self.assertEqual(
            expense_validation_actions(
                amount=10,
                status="Submitted",
                receipt_present=False,
                approved_by_present=False,
                payment_method=None,
            ),
            ("evidence_required",),
        )

    def test_approval_stamps_approver_before_paid_method_validation(self):
        self.assertEqual(
            expense_validation_actions(
                amount=10,
                status="Paid",
                receipt_present=True,
                approved_by_present=False,
                payment_method=None,
            ),
            ("stamp_approver", "payment_method_required"),
        )

    def test_valid_paid_expense_needs_no_validation_actions(self):
        self.assertEqual(
            expense_validation_actions(
                amount=10,
                status="Paid",
                receipt_present=True,
                approved_by_present=True,
                payment_method="Cash",
            ),
            (),
        )

    def test_draft_expense_does_not_require_receipt_or_payment_method(self):
        self.assertEqual(
            expense_validation_actions(
                amount=10,
                status="Draft",
                receipt_present=False,
                approved_by_present=False,
                payment_method=None,
            ),
            (),
        )


if __name__ == "__main__":
    unittest.main()
