"""Framework-independent validation steps for general expenses."""

EVIDENCE_STATUSES = frozenset(("Submitted", "Approved", "Paid"))
APPROVAL_STATUSES = frozenset(("Approved", "Paid"))


def expense_validation_actions(
    *, amount, status, receipt_present, approved_by_present, payment_method
):
    """Return validation errors and workflow actions in the existing order."""
    if amount <= 0:
        return ("amount_must_be_positive",)
    if status in EVIDENCE_STATUSES and not receipt_present:
        return ("evidence_required",)

    actions = []
    if status in APPROVAL_STATUSES and not approved_by_present:
        actions.append("stamp_approver")
    if status == "Paid" and not payment_method:
        actions.append("payment_method_required")
    return tuple(actions)
