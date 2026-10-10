"""Frappe controller integration tests for document governance."""

import frappe
from frappe.tests import UnitTestCase


class TestRundiNovaDocument(UnitTestCase):
    def test_restricted_document_needs_an_owner(self):
        doc = frappe.new_doc("RundiNova Document")
        doc.document_date = "2026-01-01"
        doc.review_date = "2026-01-02"
        doc.confidentiality = "Restricted"

        with self.assertRaises(frappe.ValidationError):
            doc.validate()

    def test_valid_restricted_document_passes(self):
        doc = frappe.new_doc("RundiNova Document")
        doc.document_date = "2026-01-01"
        doc.review_date = "2026-01-02"
        doc.confidentiality = "Restricted"
        doc.document_owner = frappe.session.user

        doc.validate()
