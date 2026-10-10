"""Frappe controller integration tests for decision follow-up rules."""

import frappe
from frappe.tests import UnitTestCase


class TestRundiNovaDecision(UnitTestCase):
    def test_completed_decision_requires_evidence_or_a_task(self):
        doc = frappe.new_doc("RundiNova Decision")
        doc.status = "Completed"

        with self.assertRaises(frappe.ValidationError):
            doc.validate()

    def test_completed_decision_with_a_follow_up_task_passes(self):
        doc = frappe.new_doc("RundiNova Decision")
        doc.status = "Completed"
        doc.action_task = "TASK-TEST"

        doc.validate()
