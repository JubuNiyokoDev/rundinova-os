"""Frappe persistence adapter for the framework-independent purchase use case."""

import frappe
from rundinova_core.application.food_purchase import (
    FoodBudget,
    FoodBudgetLine,
    FoodItemMetadata,
    FoodProgressRecord,
    FoodPurchaseResult,
)


class FrappeFoodPurchasePort:
    """Translate the purchase port into permission-aware Frappe operations."""

    def get_readable_budget(self, budget):
        doc = frappe.get_doc("RundiNova Food Budget", budget)
        doc.check_permission("read")
        return FoodBudget(
            name=doc.name,
            items=tuple(
                FoodBudgetLine(item=row.item, unit=row.unit)
                for row in (doc.items or [])
            ),
        )

    def get_readable_progress(self, progress):
        doc = frappe.get_doc("RundiNova Food Progress", progress)
        doc.check_permission("read")
        return FoodProgressRecord(name=doc.name, budget=doc.budget, item=doc.item)

    def find_readable_progress(self, budget, item):
        name = frappe.db.get_value(
            "RundiNova Food Progress", {"budget": budget, "item": item}, "name"
        )
        return self.get_readable_progress(name) if name else None

    def create_progress(self, budget, item):
        from rundinova_tech.rundinova_tech.doctype.rundinova_food_progress.rundinova_food_progress import (
            set_progress_title,
        )

        doc = frappe.get_doc(
            {"doctype": "RundiNova Food Progress", "budget": budget, "item": item}
        )
        set_progress_title(doc)
        doc.insert(ignore_permissions=True)
        return FoodProgressRecord(name=doc.name, budget=doc.budget, item=doc.item)

    def get_item_metadata(self, item):
        return FoodItemMetadata(
            category=frappe.db.get_value("Item", item, "item_group"),
            stock_unit=frappe.db.get_value("Item", item, "stock_uom"),
        )

    def insert_food_expense(self, values):
        doc = frappe.get_doc({"doctype": "RundiNova Food Expense", **values})
        doc.insert()
        return FoodPurchaseResult(
            name=doc.name,
            title=doc.expense_title,
            progress=doc.food_progress,
        )
