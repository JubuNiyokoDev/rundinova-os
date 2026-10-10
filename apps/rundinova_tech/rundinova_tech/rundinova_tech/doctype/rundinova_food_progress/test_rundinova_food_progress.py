from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from . import rundinova_food_progress as progress_controller
from .rundinova_food_progress import recalculate


class TestRundiNovaFoodProgress(UnitTestCase):
	def test_controller_adapts_frappe_snapshots_to_core_calculation(self):
		doc = frappe._dict({"budget": "BUDGET-1", "item": "Riz"})
		with (
			patch.object(progress_controller.frappe, "get_all") as get_all,
			patch.object(progress_controller.frappe.utils, "nowdate", return_value="2026-01-10"),
			patch.object(progress_controller.frappe.db, "get_value", return_value="2026-01-31"),
		):
			get_all.side_effect = [
			[frappe._dict({"quantity": 20, "unit": "kg", "monthly_amount": 100000})],
			[
				frappe._dict({"quantity": 5, "amount": 45000, "status": "Paid"}),
				frappe._dict({"quantity": 3, "amount": 25000, "status": "Submitted"}),
			],
			]
			recalculate(doc)

		self.assertEqual(doc.consumed_quantity, 8)
		self.assertEqual(doc.consumed_amount, 70000)
		self.assertEqual(doc.remaining_amount, 30000)
		self.assertEqual(doc.consumed_percent, 70)
		self.assertEqual(doc.status, "OK")
		self.assertEqual(doc.remaining_days, 21)
		self.assertEqual(get_all.call_count, 2)

	def test_incomplete_progress_does_not_query_frappe(self):
		with patch.object(progress_controller.frappe, "get_all") as get_all:
			recalculate(frappe._dict({"budget": "", "item": ""}))
		get_all.assert_not_called()
