"""Frappe controller integration tests for goal calculation."""

import frappe
from frappe.tests import UnitTestCase


class TestRundiNovaGoal(UnitTestCase):
    def test_invalid_period_is_rejected(self):
        doc = frappe.new_doc("RundiNova Goal")
        doc.period_start = "2026-02-01"
        doc.period_end = "2026-01-01"
        doc.target_value = 10

        with self.assertRaises(frappe.ValidationError):
            doc.validate()

    def test_achievement_is_bounded_and_status_updates(self):
        doc = frappe.new_doc("RundiNova Goal")
        doc.period_start = "2026-01-01"
        doc.period_end = "2026-12-31"
        doc.target_value = 10
        doc.current_value = 12
        doc.status = "Active"

        doc.validate()

        self.assertEqual(doc.achievement_percent, 100)
        self.assertEqual(doc.status, "Achieved")
