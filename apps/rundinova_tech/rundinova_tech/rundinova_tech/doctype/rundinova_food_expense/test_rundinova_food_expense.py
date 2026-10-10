"""Frappe adapter checks for supplier-invoice food-expense synchronization."""

from unittest.mock import MagicMock, Mock, patch

import frappe
from frappe.tests import UnitTestCase

from . import food_expense_policy_adapter
from . import rundinova_food_expense as food_expense_controller
from .food_expense_policy_adapter import FrappeFoodExpensePolicyPort
from .food_invoice_adapter import FrappeFoodInvoicePort, food_invoice_command
from .food_progress_link_adapter import FrappeFoodProgressLinkPort


class TestFoodInvoiceAdapter(UnitTestCase):
    def test_policy_adapter_loads_budget_and_active_expense_totals(self):
        with (
            patch.object(
                food_expense_policy_adapter.frappe.db,
                "get_value",
                return_value=("2026-01-01", "2026-01-31", 1150000),
            ),
            patch.object(
                food_expense_policy_adapter.frappe.db,
                "sql",
                side_effect=[[(125750,)], [(45750,)], [(90000,)]],
            ) as sql,
            patch.object(
                food_expense_policy_adapter.frappe.utils,
                "flt",
                side_effect=lambda value: float(value or 0),
            ),
        ):
            policy = FrappeFoodExpensePolicyPort().get_food_expense_policy(
                "BUDGET-1", "Riz", "FOOD-1", include_limits=True
            )

        self.assertEqual(policy.period_start, frappe.utils.getdate("2026-01-01"))
        self.assertEqual(policy.period_end, frappe.utils.getdate("2026-01-31"))
        self.assertEqual(policy.approved_ceiling, 1150000)
        self.assertEqual(policy.budget_committed, 125750)
        self.assertEqual(policy.item_committed, 45750)
        self.assertEqual(policy.item_planned, 90000)
        self.assertEqual(sql.call_count, 3)

    def test_policy_adapter_skips_aggregate_queries_when_limits_do_not_apply(self):
        with (
            patch.object(
                food_expense_policy_adapter.frappe.db,
                "get_value",
                return_value=("2026-01-01", "2026-01-31", 1150000),
            ),
            patch.object(food_expense_policy_adapter.frappe.db, "sql") as sql,
        ):
            policy = FrappeFoodExpensePolicyPort().get_food_expense_policy(
                "BUDGET-1", "Riz", "FOOD-1", include_limits=False
            )

        self.assertEqual(policy.budget_committed, 0)
        self.assertEqual(policy.item_committed, 0)
        self.assertEqual(policy.item_planned, 0)
        sql.assert_not_called()

    @patch(
        "rundinova_tech.rundinova_tech.doctype.rundinova_food_expense.food_invoice_adapter.frappe.get_doc"
    )
    def test_create_expense_keeps_the_existing_controlled_permission_bypass(
        self, get_doc
    ):
        expense = MagicMock()
        get_doc.return_value = expense
        values = {"budget": "BUDGET-1", "purchase_invoice": "PINV-1"}

        FrappeFoodInvoicePort().create_expense(values)

        get_doc.assert_called_once_with({"doctype": "RundiNova Food Expense", **values})
        expense.insert.assert_called_once_with(ignore_permissions=True)

    @patch(
        "rundinova_tech.rundinova_tech.doctype.rundinova_food_expense.food_invoice_adapter.frappe.get_doc"
    )
    def test_update_expense_preserves_privileged_save_path(self, get_doc):
        expense = MagicMock()
        get_doc.return_value = expense
        values = {"status": "Submitted", "amount": 12000}

        FrappeFoodInvoicePort().update_expense("FOOD-1", values)

        get_doc.assert_called_once_with("RundiNova Food Expense", "FOOD-1")
        expense.update.assert_called_once_with(values)
        expense.save.assert_called_once_with(ignore_permissions=True)

    @patch(
        "rundinova_tech.rundinova_tech.doctype.rundinova_food_expense.food_invoice_adapter.frappe.get_doc"
    )
    def test_cancel_expense_uses_the_standard_controller_save(self, get_doc):
        expense = MagicMock()
        get_doc.return_value = expense

        FrappeFoodInvoicePort().cancel_expense("FOOD-1")

        self.assertEqual(expense.status, "Cancelled")
        expense.save.assert_called_once_with(ignore_permissions=True)

    def test_invoice_document_is_adapted_to_plain_application_values(self):
        invoice = frappe._dict(
            {
                "name": "PINV-1",
                "rundinova_food_budget": "BUDGET-1",
                "posting_date": "2026-10-08",
                "supplier": "SUPPLIER-1",
                "items": [
                    frappe._dict(
                        {
                            "name": "row-1",
                            "item_code": "Riz",
                            "qty": 5,
                            "uom": "Kg",
                            "amount": 45000,
                        }
                    )
                ],
            }
        )

        command = food_invoice_command(invoice)

        self.assertEqual(command.name, "PINV-1")
        self.assertEqual(command.budget, "BUDGET-1")
        self.assertEqual(command.items[0].item, "Riz")
        self.assertEqual(command.items[0].quantity, 5)
        self.assertEqual(command.items[0].amount, 45000)
        self.assertIn("PINV-1", command.source_note)


class TestFoodExpenseCashLinkAdapter(UnitTestCase):
    @patch.object(food_expense_controller, "_", side_effect=lambda message: message)
    @patch.object(food_expense_controller.frappe, "throw")
    @patch.object(
        food_expense_controller.frappe, "get_all", return_value=[{"name": "CASH-1"}]
    )
    def test_delete_requires_cancelled_cash_movement(self, get_all, throw, translate):
        doc = frappe._dict({"name": "FOOD-1"})

        food_expense_controller.ensure_cash_link_not_stale(doc, deleting=True)

        get_all.assert_called_once()
        throw.assert_called_once_with(
            "Cancel the linked cash movement before deleting this food purchase."
        )

    @patch.object(food_expense_controller, "_", side_effect=lambda message: message)
    @patch.object(food_expense_controller.frappe, "throw")
    @patch.object(
        food_expense_controller.frappe, "get_all", return_value=[{"name": "CASH-1"}]
    )
    def test_only_changes_to_cash_source_fields_require_cancellation(
        self, get_all, throw, translate
    ):
        previous = frappe._dict({"amount": 45000, "status": "Paid", "notes": "old"})
        unchanged_source = frappe._dict(
            {"name": "FOOD-1", "amount": 45000, "status": "Paid", "notes": "new"}
        )
        unchanged_source.get_doc_before_save = Mock(return_value=previous)
        changed_source = frappe._dict(
            {"name": "FOOD-1", "amount": 46000, "status": "Paid", "notes": "old"}
        )
        changed_source.get_doc_before_save = Mock(return_value=previous)

        food_expense_controller.ensure_cash_link_not_stale(unchanged_source)
        throw.assert_not_called()
        food_expense_controller.ensure_cash_link_not_stale(changed_source)
        self.assertEqual(get_all.call_count, 2)
        throw.assert_called_once_with(
            "Cancel the linked cash movement before changing this food purchase."
        )


class TestFoodExpenseValidationRoleCheck(UnitTestCase):
    def _validate_with_roles(self, roles):
        doc = frappe._dict(
            {
                "name": "FOOD-ROLE-TEST",
                "item": None,
                "category": None,
                "unit": None,
                "budget": None,
                "expense_date": "2026-10-09",
                "amount": 1000,
                "status": "Draft",
                "notes": "",
            }
        )
        with (
            patch.object(food_expense_controller, "ensure_cash_link_not_stale"),
            patch.object(food_expense_controller, "auto_link_food_progress"),
            patch.object(food_expense_controller, "set_expense_title"),
            patch.object(
                food_expense_controller,
                "validate_food_expense",
                return_value=None,
            ) as validate_policy,
            patch.object(
                food_expense_controller.frappe, "get_roles", return_value=roles
            ),
            patch.dict(
                food_expense_controller.frappe.session,
                {"user": "joffre.niyondiko@rundinova.com"},
            ),
        ):
            food_expense_controller.validate_expense(doc)
        return validate_policy.call_args.args[0].can_exceed_item_plan

    def test_director_role_is_checked_with_supported_frappe_api(self):
        self.assertTrue(self._validate_with_roles(["RundiNova Director"]))

    def test_non_director_role_cannot_exceed_item_plan(self):
        self.assertFalse(self._validate_with_roles(["RundiNova Team Member"]))


class TestFoodProgressLinkAdapter(UnitTestCase):
    @patch.object(
        food_expense_controller, "ensure_food_progress_link", return_value="PROGRESS-1"
    )
    @patch.object(food_expense_controller, "FrappeFoodProgressLinkPort")
    def test_expense_controller_delegates_association_policy_to_core(
        self, port, ensure_link
    ):
        doc = frappe._dict(
            {"budget": "BUDGET-1", "item": "RICE", "food_progress": None}
        )

        food_expense_controller.auto_link_food_progress(doc)

        ensure_link.assert_called_once_with("BUDGET-1", "RICE", None, port.return_value)
        self.assertEqual(doc.food_progress, "PROGRESS-1")

    @patch(
        "rundinova_tech.rundinova_tech.doctype.rundinova_food_expense.food_progress_link_adapter.frappe.get_all"
    )
    def test_finds_existing_progress_for_the_expense_budget_item(self, get_all):
        get_all.return_value = [frappe._dict({"name": "PROGRESS-1"})]

        progress = FrappeFoodProgressLinkPort().find_progress("BUDGET-1", "RICE")

        self.assertEqual(progress, "PROGRESS-1")
        get_all.assert_called_once_with(
            "RundiNova Food Progress",
            filters={"budget": "BUDGET-1", "item": "RICE"},
            fields=["name"],
        )

    @patch(
        "rundinova_tech.rundinova_tech.doctype.rundinova_food_expense.food_progress_link_adapter.frappe.get_doc"
    )
    def test_creates_missing_progress_with_the_existing_controlled_bypass(
        self, get_doc
    ):
        progress = MagicMock(name="progress-object")
        progress.name = "PROGRESS-NEW"
        get_doc.return_value = progress

        result = FrappeFoodProgressLinkPort().create_progress("BUDGET-1", "RICE")

        self.assertEqual(result, "PROGRESS-NEW")
        get_doc.assert_called_once_with(
            {"doctype": "RundiNova Food Progress", "budget": "BUDGET-1", "item": "RICE"}
        )
        progress.insert.assert_called_once_with(ignore_permissions=True)
