import frappe
from frappe import _
from frappe.model.document import Document


class RundiNovaCashAccount(Document):
    def validate(self):
        if frappe.utils.flt(self.opening_balance) < 0:
            frappe.throw(_("Opening balance cannot be negative."))
        if not self.currency:
            self.currency = "BIF"

    def on_update(self):
        refresh_account_balance(self.name)


def refresh_account_balance(account_name):
    if not account_name or not frappe.db.exists("RundiNova Cash Account", account_name):
        return
    account = frappe.get_doc("RundiNova Cash Account", account_name)
    rows = frappe.get_all("RundiNova Cash Movement", filters={"status": ["in", ["Approved", "Reconciled"]]}, fields=["movement_type", "account", "destination_account", "amount"])
    balance = frappe.utils.flt(account.opening_balance)
    for row in rows:
        amount = frappe.utils.flt(row.amount)
        if row.account == account_name:
            balance += amount if row.movement_type == "Income" else -amount
        if row.movement_type == "Transfer" and row.destination_account == account_name:
            balance += amount
    frappe.db.set_value("RundiNova Cash Account", account_name, "current_balance", balance, update_modified=False)
