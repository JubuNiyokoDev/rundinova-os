"""Currency semantics for business metrics rendered in RundiNova dashboards."""

BUSINESS_CURRENCY = "BIF"

MONETARY_FIELDS = frozenset(
    {
        "amount",
        "actual_amount",
        "balance_amount",
        "business_value",
        "current_balance",
        "current_value",
        "expected_value",
        "total_planned_amount",
    }
)


def currency_for_field(field_name):
    """Return the currency for monetary fields, or None for counts and ratios."""
    return BUSINESS_CURRENCY if field_name in MONETARY_FIELDS else None
