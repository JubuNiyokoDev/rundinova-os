import unittest

from rundinova_core.application.food_invoice import (
    FoodInvoiceCommand,
    FoodInvoiceLine,
    cancel_food_invoice,
    sync_food_invoice,
)


class FakeFoodInvoicePort:
    def __init__(self, existing=None, linked=None):
        self.existing = existing or {}
        self.linked = linked or []
        self.created = []
        self.updated = []
        self.cancelled = []
        self.refreshed = []

    def find_expense(self, invoice, invoice_line):
        return self.existing.get((invoice, invoice_line))

    def get_item_category(self, item):
        return f"{item} category"

    def create_expense(self, values):
        self.created.append(values)

    def update_expense(self, name, values):
        self.updated.append((name, values))

    def list_invoice_expenses(self, invoice):
        return self.linked

    def cancel_expense(self, name):
        self.cancelled.append(name)

    def refresh_budget(self, budget):
        self.refreshed.append(budget)


def command(budget="food-budget", items=None):
    return FoodInvoiceCommand(
        name="PINV-2026-0001",
        budget=budget,
        posting_date="2026-10-08",
        supplier="SUPPLIER-1",
        source_note="Created from invoice",
        items=tuple(items or ()),
    )


class TestFoodInvoiceUseCase(unittest.TestCase):
    def test_sync_creates_missing_expenses_updates_existing_and_skips_non_items(self):
        port = FakeFoodInvoicePort(existing={("PINV-2026-0001", "row-2"): "FOOD-2"})
        result = sync_food_invoice(
            command(
                items=[
                    FoodInvoiceLine("row-1", "Riz", 5, "kg", 45000),
                    FoodInvoiceLine("row-2", "Pain", 2, "unit", 12000),
                    FoodInvoiceLine("row-tax", None, 1, None, 0),
                ]
            ),
            port,
        )

        self.assertEqual((result.created, result.updated), (1, 1))
        self.assertEqual(port.created[0]["purchase_invoice_item"], "row-1")
        self.assertEqual(port.created[0]["category"], "Riz category")
        self.assertEqual(port.created[0]["status"], "Submitted")
        self.assertEqual(port.updated[0][0], "FOOD-2")
        self.assertEqual(port.refreshed, ["food-budget"])

    def test_sync_without_budget_has_no_side_effects(self):
        port = FakeFoodInvoicePort()
        result = sync_food_invoice(command(budget=None), port)

        self.assertEqual((result.created, result.updated), (0, 0))
        self.assertEqual(port.created, [])
        self.assertEqual(port.refreshed, [])

    def test_cancel_cancels_all_linked_expenses_and_refreshes_each_budget_once(self):
        port = FakeFoodInvoicePort(
            linked=[
                ("FOOD-1", "budget-A"),
                ("FOOD-2", "budget-A"),
                ("FOOD-3", "budget-B"),
            ]
        )
        result = cancel_food_invoice(command(), port)

        self.assertEqual(result.cancelled, 3)
        self.assertEqual(port.cancelled, ["FOOD-1", "FOOD-2", "FOOD-3"])
        self.assertEqual(port.refreshed, ["budget-A", "budget-B"])

    def test_cancel_without_linked_expenses_does_not_refresh_budgets(self):
        port = FakeFoodInvoicePort()
        result = cancel_food_invoice(command(), port)

        self.assertEqual(result.cancelled, 0)
        self.assertEqual(port.refreshed, [])


if __name__ == "__main__":
    unittest.main()
