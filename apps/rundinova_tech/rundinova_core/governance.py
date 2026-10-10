"""Framework-independent rules for decisions, records, assets, and goals."""


def document_validation_actions(
    review_date, document_date, confidentiality, document_owner
):
    actions = []
    if review_date and document_date and review_date < document_date:
        actions.append("review_before_document_date")
    if confidentiality == "Restricted" and not document_owner:
        actions.append("restricted_document_requires_owner")
    return tuple(actions)


def decision_validation_actions(
    status, action_task, evidence, follow_up_date, decision_date
):
    actions = []
    if status == "Completed" and not action_task and not evidence:
        actions.append("completed_decision_requires_follow_up")
    if follow_up_date and decision_date and follow_up_date < decision_date:
        actions.append("follow_up_before_decision_date")
    return tuple(actions)


def asset_validation_actions(
    purchase_amount, current_value, status, assigned_to, location
):
    actions = []
    if purchase_amount < 0 or current_value < 0:
        actions.append("asset_value_negative")
    if status == "In Use" and not assigned_to and not location:
        actions.append("asset_in_use_requires_assignment_or_location")
    return tuple(actions)


def goal_validation_actions(period_start, period_end, target_value):
    if period_end < period_start:
        return ("goal_period_invalid",)
    if target_value <= 0:
        return ("goal_target_not_positive",)
    return ()


def goal_achievement(current_value, target_value):
    """Return the bounded achievement percentage and optional achieved status."""
    percent = min(100, max(0, current_value / target_value * 100))
    return percent, "Achieved" if percent >= 100 else None
