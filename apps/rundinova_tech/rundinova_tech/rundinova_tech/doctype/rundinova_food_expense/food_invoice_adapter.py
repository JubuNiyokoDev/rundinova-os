"""Frappe persistence adapter for the independent food-invoice use case."""

import frappe
from frappe import _
from rundinova_core.application.food_invoice import FoodInvoiceCommand, FoodInvoiceLine


class FrappeFoodInvoicePort:
    """Keep invoice document access and permission bypasses inside Frappe."""

    def find_expense(self, invoice, invoice_line):
        return frappe.db.get_value(
            "RundiNova Food Expense",
            {"purchase_invoice": invoice, "purchase_invoice_item": invoice_line},
            "name",
        )

    def get_item_category(self, item):
        return frappe.db.get_value("Item", item, "item_group")

    def create_expense(self, values):
        doc = frappe.get_doc({"doctype": "RundiNova Food Expense", **values})
        doc.insert(ignore_permissions=True)

    def update_expense(self, name, values):
        doc = frappe.get_doc("RundiNova Food Expense", name)
        doc.update(values)
        doc.save(ignore_permissions=True)

    def list_invoice_expenses(self, invoice):
        return [
            (row.name, row.budget)
            for row in frappe.get_all(
                "RundiNova Food Expense",
                filters={"purchase_invoice": invoice},
                fields=["name", "budget"],
            )
        ]

    def cancel_expense(self, name):
        doc = frappe.get_doc("RundiNova Food Expense", name)
        doc.status = "Cancelled"
        doc.save(ignore_permissions=True)

    def refresh_budget(self, budget):
        if not frappe.db.exists("RundiNova Food Budget", budget):
            return
        from rundinova_tech.rundinova_tech.doctype.rundinova_food_budget.rundinova_food_budget import (
            refresh_budget_totals,
        )

        refresh_budget_totals(budget)


def food_invoice_command(doc):
    """Convert an ERPNext invoice document into a plain application command."""
    get = doc.get
    name = get("name")
    return FoodInvoiceCommand(
        name=name,
        budget=get("rundinova_food_budget"),
        posting_date=get("posting_date"),
        supplier=get("supplier"),
        source_note=_("Created from Purchase Invoice {0}").format(name),
        items=tuple(
            FoodInvoiceLine(
                name=row.get("name"),
                item=row.get("item_code"),
                quantity=row.get("qty"),
                unit=row.get("uom"),
                amount=row.get("amount"),
            )
            for row in (get("items") or [])
        ),
    )
