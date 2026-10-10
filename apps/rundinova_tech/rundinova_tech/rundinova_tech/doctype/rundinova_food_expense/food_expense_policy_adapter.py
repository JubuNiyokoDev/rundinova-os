"""Frappe reads for the independent food-expense policy use case."""

import frappe
from rundinova_core.application.food_expense import FoodExpensePolicy
from rundinova_core.food import ACTIVE_EXPENSE_STATUSES


class FrappeFoodExpensePolicyPort:
    """Build a policy snapshot from the current site's budget and expenses."""

    def get_food_expense_policy(self, budget, item, exclude_expense, include_limits):
        period_start, period_end, approved_ceiling = frappe.db.get_value(
            "RundiNova Food Budget",
            budget,
            ["period_start", "period_end", "approved_ceiling"],
        )
        budget_committed = item_committed = item_planned = 0
        if include_limits:
            statuses = tuple(ACTIVE_EXPENSE_STATUSES)
            status_slots = ", ".join("%s" for _ in statuses)
            budget_committed = frappe.db.sql(
                """select coalesce(sum(amount), 0) from `tabRundiNova Food Expense`
				   where budget=%s and status in (""" + status_slots + ") and name != %s",
                (budget, *statuses, exclude_expense or ""),
            )[0][0]
        item_committed = 0
        if include_limits and item:
            item_committed = frappe.db.sql(
                """select coalesce(sum(amount), 0) from `tabRundiNova Food Expense`
				   where budget=%s and item=%s and status in ("""
                + status_slots
                + ") and name != %s",
                (budget, item, *statuses, exclude_expense or ""),
            )[0][0]
            item_planned = frappe.db.sql(
                """select coalesce(sum(monthly_amount), 0) from `tabRundiNova Food Budget Item`
				   where parent=%s and item=%s""",
                (budget, item),
            )[0][0]
        return FoodExpensePolicy(
            period_start=frappe.utils.getdate(period_start),
            period_end=frappe.utils.getdate(period_end),
            approved_ceiling=frappe.utils.flt(approved_ceiling),
            budget_committed=frappe.utils.flt(budget_committed),
            item_committed=frappe.utils.flt(item_committed),
            item_planned=frappe.utils.flt(item_planned),
        )
