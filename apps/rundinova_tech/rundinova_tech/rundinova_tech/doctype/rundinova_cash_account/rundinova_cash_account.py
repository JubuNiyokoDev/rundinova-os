import frappe
from frappe import _
from frappe.model.document import Document

from rundinova_core.cash import (
    BALANCE_STATUSES,
    calculate_cash_account_balance,
    cash_account_opening_balance_violation,
)


class RundiNovaCashAccount(Document):
    def validate(self):
        if cash_account_opening_balance_violation(frappe.utils.flt(self.opening_balance)):
            frappe.throw(_("Opening balance cannot be negative."))
        if not self.currency:
            self.currency = "BIF"

    def on_update(self):
        refresh_account_balance(self.name)


def refresh_account_balance(account_name):
    if not account_name or not frappe.db.exists("RundiNova Cash Account", account_name):
        return
    account = frappe.get_doc("RundiNova Cash Account", account_name)
    rows = frappe.get_all(
        "RundiNova Cash Movement",
        filters={"status": ["in", list(BALANCE_STATUSES)], "docstatus": ["<", 2]},
        fields=["movement_type", "account", "destination_account", "amount"],
    )
    balance = calculate_cash_account_balance(
        frappe.utils.flt(account.opening_balance),
        account_name,
        [
            (
                row.movement_type,
                row.account,
                row.destination_account,
                frappe.utils.flt(row.amount),
            )
            for row in rows
        ],
    )
    frappe.db.set_value("RundiNova Cash Account", account_name, "current_balance", balance, update_modified=False)
