"""Role-policy checks for the real RundiNova team responsibilities."""

from frappe.tests import UnitTestCase
from rundinova_tech import hooks
from rundinova_tech.rundinova_tech.access_control import (
    get_custom_doctype_permissions,
    get_standard_doctype_permissions,
)
from rundinova_tech.rundinova_tech.site_bootstrap.team import (
    LEGACY_TEAM_LOGIN_REPLACEMENTS,
    TEAM_USERS,
)


class TestRolePolicy(UnitTestCase):
    def test_custom_roles_exist_before_migrate_syncs_workspace_fixtures(self):
        self.assertIn(
            "rundinova_tech.rundinova_tech.provisioning.roles.ensure_rundinova_roles",
            hooks.before_migrate,
        )

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
                "housekeeping@rundinova.com",
            },
        )
        self.assertIn("RundiNova Director", users["joffre.niyondiko@kit-hub.com"])
        self.assertIn("RundiNova Ecosystem Lead", users["ndabubahajanvier@gmail.com"])
        self.assertIn("RundiNova Growth Lead", users["maniranyibutsef@gmail.com"])
        self.assertIn(
            "RundiNova Community Relations", users["mandela.fanuel.1@gmail.com"]
        )
        self.assertEqual(
            users["housekeeping@rundinova.com"],
            {"Employee", "RundiNova Team Member"},
        )
        self.assertEqual(
            LEGACY_TEAM_LOGIN_REPLACEMENTS,
            {"1.ndabubahajanvier@gmail.com": "ndabubahajanvier@gmail.com"},
        )

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
