"""Role-policy checks for the real RundiNova team responsibilities."""

from unittest.mock import patch

from frappe import _dict
from frappe.tests import UnitTestCase

from rundinova_tech import hooks
from rundinova_tech.rundinova_tech.access_control import (
    get_custom_doctype_permissions,
    get_standard_doctype_permissions,
    has_permission,
    workspace_query,
)
from rundinova_tech.rundinova_tech.provisioning.workspaces import (
    DEFAULT_WORKSPACE_BY_ROLE,
)
from rundinova_tech.rundinova_tech.site_bootstrap.team import (
    LEGACY_TEAM_LOGIN_REPLACEMENTS,
    TEAM_USERS,
    _clear_orphaned_default_workspace,
)


class TestRolePolicy(UnitTestCase):
    def test_custom_roles_exist_before_migrate_syncs_workspace_fixtures(self):
        self.assertIn(
            "rundinova_tech.rundinova_tech.provisioning.roles.ensure_rundinova_roles",
            hooks.before_migrate,
        )

    def test_team_bootstrap_clears_workspace_links_removed_by_migration(self):
        user = _dict(default_workspace="RundiNova Ecosystem")
        with patch(
            "rundinova_tech.rundinova_tech.site_bootstrap.team.frappe.db.exists",
            return_value=False,
        ):
            self.assertTrue(_clear_orphaned_default_workspace(user))
        self.assertIsNone(user.default_workspace)

    def test_team_bootstrap_preserves_existing_workspace_links(self):
        user = _dict(default_workspace="RundiNova Tech")
        with patch(
            "rundinova_tech.rundinova_tech.site_bootstrap.team.frappe.db.exists",
            return_value=True,
        ):
            self.assertFalse(_clear_orphaned_default_workspace(user))
        self.assertEqual(user.default_workspace, "RundiNova Tech")

    def test_team_seed_uses_confirmed_login_addresses_and_business_roles(self):
        users = {row["email"]: set(row["roles"]) for row in TEAM_USERS}
        self.assertEqual(
            set(users),
            {
                "joffre.niyondiko@kit-hub.com",
                "ndabubahajanvier@gmail.com",
                "presira857@gmail.com",
                "maniranyibutsef@gmail.com",
                "mandela.fanuel.1@gmail.com",
                "vyamungucharif410@gmail.com",
            },
        )
        self.assertIn("RundiNova Director", users["joffre.niyondiko@kit-hub.com"])
        self.assertIn("Employee", users["ndabubahajanvier@gmail.com"])
        self.assertIn("RundiNova Ecosystem Lead", users["ndabubahajanvier@gmail.com"])
        self.assertIn("RundiNova Project Lead", users["maniranyibutsef@gmail.com"])
        self.assertIn("RundiNova Growth Lead", users["maniranyibutsef@gmail.com"])
        self.assertIn(
            "RundiNova Community Relations", users["mandela.fanuel.1@gmail.com"]
        )
        self.assertEqual(
            users["vyamungucharif410@gmail.com"],
            {"Employee", "RundiNova Team Member"},
        )
        for developer in (
            "ndabubahajanvier@gmail.com",
            "presira857@gmail.com",
            "maniranyibutsef@gmail.com",
            "mandela.fanuel.1@gmail.com",
        ):
            self.assertIn("RundiNova Developer", users[developer])
        self.assertEqual(
            LEGACY_TEAM_LOGIN_REPLACEMENTS,
            {
                "1.ndabubahajanvier@gmail.com": "ndabubahajanvier@gmail.com",
                "housekeeping@rundinova.com": "vyamungucharif410@gmail.com",
            },
        )

    def test_role_specific_home_takes_priority_over_shared_developer_workspace(self):
        role_order = [role for role, _workspace in DEFAULT_WORKSPACE_BY_ROLE]
        developer_index = role_order.index("RundiNova Developer")
        for role in (
            "RundiNova Project Lead",
            "RundiNova Ecosystem Lead",
            "RundiNova Growth Lead",
            "RundiNova Community Relations",
            "RundiNova Communications",
        ):
            self.assertLess(role_order.index(role), developer_index)

    def test_developer_and_project_lead_project_task_permissions_exclude_delete(self):
        policy = get_standard_doctype_permissions()
        developer_project = policy[("Project", "RundiNova Developer")]
        developer_task = policy[("Task", "RundiNova Developer")]
        project_lead_project = policy[("Project", "RundiNova Project Lead")]
        project_lead_task = policy[("Task", "RundiNova Project Lead")]

        self.assertEqual(developer_project["read"], 1)
        self.assertEqual(developer_project["write"], 0)
        self.assertEqual(developer_task["write"], 1)
        self.assertEqual(developer_task["create"], 1)
        for permission in (
            developer_project,
            developer_task,
            project_lead_project,
            project_lead_task,
        ):
            self.assertEqual(permission["delete"], 0)
        self.assertEqual(project_lead_project["write"], 1)
        self.assertEqual(project_lead_task["write"], 1)

    def test_only_non_director_team_accounts_lose_workspace_admin_bypass(self):
        self.assertIn(
            "rundinova_tech.rundinova_tech.bootstrap.ensure_team_users",
            hooks.after_migrate,
        )

    def test_stale_workspace_and_page_routes_are_denied_server_side(self):
        user = "developer@example.test"
        workspace = _dict(doctype="Workspace", is_hidden=1, roles=[])
        page = _dict(
            doctype="Page",
            name="build",
            roles=[_dict(role="System Manager")],
        )
        with patch(
            "rundinova_tech.rundinova_tech.access_control.frappe.get_roles",
            return_value=["RundiNova Developer"],
        ):
            self.assertFalse(has_permission(workspace, user=user, ptype="read"))
            self.assertFalse(has_permission(page, user=user, ptype="read"))

    def test_documents_are_available_to_rundinova_roles_but_not_unrelated_users(self):
        document = _dict(doctype="RundiNova Document")
        with patch(
            "rundinova_tech.rundinova_tech.access_control.frappe.get_roles",
            return_value=["RundiNova Developer", "RundiNova Team Member"],
        ):
            self.assertTrue(
                has_permission(document, user="developer@example.test", ptype="read")
            )
        with patch(
            "rundinova_tech.rundinova_tech.access_control.frappe.get_roles",
            return_value=["Employee"],
        ):
            self.assertFalse(
                has_permission(document, user="employee@example.test", ptype="read")
            )

    def test_workspace_list_filter_uses_role_rows_without_nonexistent_columns(self):
        with (
            patch(
                "rundinova_tech.rundinova_tech.access_control.frappe.get_roles",
                return_value=["RundiNova Developer"],
            ),
            patch(
                "rundinova_tech.rundinova_tech.access_control.frappe.db.escape",
                side_effect=lambda value: f"'{value}'",
            ),
        ):
            condition = workspace_query("developer@example.test")
        self.assertIn("tabHas Role", condition)
        self.assertIn("is_hidden = 0", condition)
        self.assertNotIn("tabWorkspace`.roles", condition)

    def test_growth_ecosystem_and_community_roles_are_separated(self):
        policy = get_custom_doctype_permissions()
        self.assertEqual(
            policy[("RundiNova Partnership", "RundiNova Ecosystem Lead")]["write"], 1
        )
        self.assertEqual(
            policy[("RundiNova Growth Opportunity", "RundiNova Growth Lead")]["write"],
            1,
        )
        self.assertEqual(
            policy[("RundiNova Community Impact", "RundiNova Community Relations")][
                "write"
            ],
            1,
        )
        self.assertNotIn(("RundiNova Cash Account", "RundiNova Growth Lead"), policy)
        self.assertEqual(
            policy[("RundiNova Food Budget", "RundiNova Community Relations")]["write"],
            0,
        )

    def test_director_reads_employee_directory_but_team_members_do_not(self):
        policy = get_standard_doctype_permissions()
        self.assertEqual(policy[("Employee", "RundiNova Director")]["read"], 1)
        self.assertNotIn(("Employee", "RundiNova Team Member"), policy)
