"""Food-budget and purchase rules with no Frappe or database dependencies."""

from collections.abc import Iterable


ACTIVE_EXPENSE_STATUSES = frozenset(("Submitted", "Approved", "Paid"))


def validate_food_budget_plan(
    total_planned,
    approved_ceiling,
    covered_people,
    has_branch,
    has_cost_center,
):
    """Return the first budget-plan rule code, preserving validation order."""
    if total_planned > approved_ceiling:
        return "planned_total_exceeds_ceiling"
    if covered_people and covered_people < 1:
        return "covered_people_must_be_positive"
    if has_branch and not has_cost_center:
        return "branch_requires_cost_center"
    return None


def calculate_food_budget_plan(monthly_amounts: Iterable[float], covered_people):
    """Calculate the monthly, annual, daily, and per-person food plan."""
    total = sum(monthly_amounts)
    daily = total / 30
    return {
        "total_planned_amount": total,
        "annual_planned_amount": total * 12,
        "daily_planned_amount": daily,
        "per_person_daily_amount": daily / covered_people if covered_people else 0,
    }


def calculate_food_budget_usage(approved_ceiling, expenses):
    """Aggregate committed, paid, remaining, and consumed amounts."""
    active = [
        (amount, status)
        for amount, status in expenses
        if status in ACTIVE_EXPENSE_STATUSES
    ]
    committed = sum(amount for amount, _status in active)
    actual = sum(amount for amount, status in active if status == "Paid")
    return {
        "committed_amount": committed,
        "actual_amount": actual,
        "balance_amount": approved_ceiling - committed,
        "consumed_percent": committed / approved_ceiling * 100 if approved_ceiling else 0,
    }


def calculate_food_progress(
    *, planned_quantity, unit, planned_amount, expenses, today=None, period_end=None
):
    """Return food-item progress fields from a plan and expense snapshots."""
    active = [
        (quantity, amount)
        for quantity, amount, status in expenses
        if status in ACTIVE_EXPENSE_STATUSES
    ]
    consumed_quantity = sum(quantity for quantity, _amount in active)
    consumed_amount = sum(amount for _quantity, amount in active)
    consumed_percent = (
        min(100.0, consumed_amount / planned_amount * 100) if planned_amount else 0
    )
    if consumed_amount > planned_amount:
        status = "Over"
    elif consumed_percent >= 90:
        status = "Warning"
    else:
        status = "OK"
    remaining_days = max(0, (period_end - today).days) if today and period_end else 0
    return {
        "unit": unit,
        "planned_quantity": planned_quantity,
        "planned_amount": planned_amount,
        "consumed_quantity": consumed_quantity,
        "consumed_amount": consumed_amount,
        "remaining_amount": planned_amount - consumed_amount,
        "consumed_percent": consumed_percent,
        "status": status,
        "remaining_days": remaining_days,
    }


def food_expense_amount_violation(amount):
    if amount <= 0:
        return "amount_must_be_positive"
    return None


def food_expense_period_violation(purchase_date, period_start, period_end):
    if purchase_date < period_start or purchase_date > period_end:
        return "purchase_date_outside_budget_period"
    return None


def food_expense_limit_violation(
    *,
    status,
    amount,
    budget_committed,
    approved_ceiling,
    item_committed,
    item_planned,
    can_exceed_item_plan,
    has_justification,
):
    """Return the first active-expense limit violation in policy order."""
    if status not in ACTIVE_EXPENSE_STATUSES:
        return None
    if item_committed + amount > item_planned:
        if not can_exceed_item_plan:
            return "item_plan_exceeded_without_authority"
        if not has_justification:
            return "item_plan_exceeded_without_justification"
    if budget_committed + amount > approved_ceiling:
        return "approved_ceiling_exceeded"
    return None
