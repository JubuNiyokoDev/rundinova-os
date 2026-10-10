"""Frappe controller integration tests for asset controls."""

import frappe
from frappe.tests import UnitTestCase


class TestRundiNovaAsset(UnitTestCase):
    def test_negative_asset_values_are_rejected(self):
        doc = frappe.new_doc("RundiNova Asset")
        doc.purchase_amount = -1
        doc.current_value = 0

        with self.assertRaises(frappe.ValidationError):
            doc.validate()

    def test_asset_in_use_needs_a_person_or_location(self):
        doc = frappe.new_doc("RundiNova Asset")
        doc.purchase_amount = 0
        doc.current_value = 0
        doc.status = "In Use"

        with self.assertRaises(frappe.ValidationError):
            doc.validate()

    def test_asset_in_use_with_location_passes(self):
        doc = frappe.new_doc("RundiNova Asset")
        doc.purchase_amount = 0
        doc.current_value = 0
        doc.status = "In Use"
        doc.location = "Gitega HQ"

        doc.validate()
