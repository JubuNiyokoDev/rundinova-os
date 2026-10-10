import frappe
from frappe import _
from frappe.model.document import Document
from rundinova_core.cash import (
    cash_movement_violation,
    food_expense_cash_link_violation,
    food_expense_movement_fields,
)


class RundiNovaCashMovement(Document):
    def before_insert(self):
        set_movement_title(self)

    def validate(self):
        linked_expense = sync_food_expense_fields(self)
        if linked_expense:
            violation = food_expense_cash_link_violation(
                expense_status=linked_expense.status,
            )
            if violation == "food_expense_must_be_paid":
                frappe.throw(
                    _("Mark the food purchase as Paid before linking it to cash.")
                )
        set_movement_title(self)
        violation = cash_movement_violation(
            amount=frappe.utils.flt(self.amount),
            movement_type=self.movement_type,
            destination_account=self.destination_account,
            status=self.status,
            evidence_present=bool(self.evidence),
        )
        if violation == "amount_must_be_positive":
            frappe.throw(_("Movement amount must be greater than zero."))
        if violation == "transfer_requires_destination":
            frappe.throw(_("A transfer requires a destination account."))
        if violation == "destination_only_valid_for_transfer":
            frappe.throw(_("Destination account is only used for transfers."))
        if violation == "evidence_required":
            frappe.throw(_("Evidence is required before submitting a movement."))
        if linked_expense:
            duplicate = frappe.db.exists(
                "RundiNova Cash Movement",
                {
                    "food_expense": self.food_expense,
                    "status": ["!=", "Cancelled"],
                    "docstatus": ["<", 2],
                    "name": ["!=", self.name or ""],
                },
            )
            violation = food_expense_cash_link_violation(
                expense_status=linked_expense.status,
                duplicate_movement=bool(duplicate),
            )
            if violation == "food_expense_already_linked":
                frappe.throw(
                    _(
                        "This food purchase is already linked to another active cash movement."
                    )
                )
        if self.status in ("Approved", "Reconciled") and not self.approved_by:
            self.approved_by = frappe.session.user

    def on_update(self):
        refresh_accounts(self)

    def on_trash(self):
        refresh_accounts(self)

    def on_cancel(self):
        refresh_accounts(self)


def sync_food_expense_fields(doc):
    """Keep linked food purchases as the source of truth for cash details."""
    if not doc.food_expense:
        previous = doc.get_doc_before_save()
        if (
            previous
            and previous.food_expense
            and previous.status in ("Submitted", "Approved", "Reconciled")
        ):
            frappe.throw(
                _("Cancel this cash movement before removing its food purchase link.")
            )
        return None

    expense = frappe.get_doc("RundiNova Food Expense", doc.food_expense)
    values = food_expense_movement_fields(expense)
    receipt = values.pop("evidence")
    for fieldname, value in values.items():
        setattr(doc, fieldname, value)
    if not doc.evidence:
        doc.evidence = receipt
    return expense


def set_movement_title(doc):
    if doc.movement_date and doc.movement_type and doc.category:
        doc.movement_title = (
            f"{doc.movement_date} - {doc.movement_type} - {doc.category}"
        )


def refresh_accounts(doc):
    from ..rundinova_cash_account.rundinova_cash_account import refresh_account_balance

    for account in {doc.account, doc.destination_account}:
        refresh_account_balance(account)
