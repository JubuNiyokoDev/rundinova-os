"""Frappe controller checks for cash movements linked to food purchases."""

from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from .rundinova_cash_movement import RundiNovaCashMovement


class TestRundiNovaCashMovement(UnitTestCase):
    @patch(
        "rundinova_tech.rundinova_tech.doctype.rundinova_cash_movement.rundinova_cash_movement.frappe.get_doc"
    )
    def test_purchase_must_be_paid(self, get_doc):
        get_doc.return_value = frappe._dict(
            {
                "status": "Submitted",
                "expense_date": "2026-10-07",
                "item": "Riz",
                "quantity": 5,
                "unit": "Kg",
                "amount": 72500,
            }
        )
        movement = frappe._dict(
            {"food_expense": "FOOD-EXP-001", "status": "Draft", "evidence": None}
        )

        with self.assertRaises(frappe.ValidationError):
            RundiNovaCashMovement.validate(movement)

    @patch(
        "rundinova_tech.rundinova_tech.doctype.rundinova_cash_movement.rundinova_cash_movement.frappe.db.exists",
        return_value=None,
    )
    @patch(
        "rundinova_tech.rundinova_tech.doctype.rundinova_cash_movement.rundinova_cash_movement.frappe.get_doc"
    )
    def test_paid_purchase_fills_movement_and_preserves_selected_evidence(
        self, get_doc, _exists
    ):
        get_doc.return_value = frappe._dict(
            {
                "status": "Paid",
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
        movement = frappe._dict(
            {
                "food_expense": "FOOD-EXP-001",
                "status": "Draft",
                "evidence": "/private/files/other-proof.jpg",
            }
        )

        RundiNovaCashMovement.validate(movement)

        self.assertEqual(movement.movement_type, "Expense")
        self.assertEqual(movement.movement_date, "2026-10-07")
        self.assertEqual(movement.amount, 72500)
        self.assertEqual(movement.category, "Cereals")
        self.assertEqual(movement.destination_type, "Supplier")
        self.assertEqual(movement.destination_description, "Market Supplier")
        self.assertEqual(movement.description, "Food purchase: 5 Kg Riz")
        self.assertIsNone(movement.destination_account)
        self.assertEqual(movement.evidence, "/private/files/other-proof.jpg")

    @patch(
        "rundinova_tech.rundinova_tech.doctype.rundinova_cash_movement.rundinova_cash_movement.frappe.db.exists",
        return_value="CASH-MOVE-001",
    )
    @patch(
        "rundinova_tech.rundinova_tech.doctype.rundinova_cash_movement.rundinova_cash_movement.frappe.get_doc"
    )
    def test_paid_purchase_cannot_be_linked_twice(self, get_doc, _exists):
        get_doc.return_value = frappe._dict(
            {
                "status": "Paid",
                "expense_date": "2026-10-07",
                "item": "Riz",
                "quantity": 5,
                "unit": "Kg",
                "amount": 72500,
            }
        )
        movement = frappe._dict(
            {"food_expense": "FOOD-EXP-001", "status": "Draft", "evidence": None}
        )

        with self.assertRaises(frappe.ValidationError):
            RundiNovaCashMovement.validate(movement)
