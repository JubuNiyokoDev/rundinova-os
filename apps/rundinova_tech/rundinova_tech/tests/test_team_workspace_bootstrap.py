"""Framework-neutral regression tests for migration-safe team setup."""

import runpy
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

TEAM_MODULE = (
    Path(__file__).resolve().parents[1]
    / "rundinova_tech"
    / "site_bootstrap"
    / "team.py"
)


def load_clear_orphaned_default_workspace(exists):
    frappe_stub = ModuleType("frappe")
    frappe_stub.db = SimpleNamespace(exists=exists)
    with patch.dict(sys.modules, {"frappe": frappe_stub}):
        namespace = runpy.run_path(str(TEAM_MODULE))
    return namespace["_clear_orphaned_default_workspace"]


class TestTeamWorkspaceBootstrap(TestCase):
    def test_clears_default_workspace_deleted_during_migration(self):
        exists = Mock(return_value=False)
        clear_default_workspace = load_clear_orphaned_default_workspace(exists)
        user = SimpleNamespace(default_workspace="RundiNova Ecosystem")

        self.assertTrue(clear_default_workspace(user))
        self.assertIsNone(user.default_workspace)
        exists.assert_called_once_with("Workspace", "RundiNova Ecosystem")

    def test_preserves_existing_default_workspace(self):
        exists = Mock(return_value=True)
        clear_default_workspace = load_clear_orphaned_default_workspace(exists)
        user = SimpleNamespace(default_workspace="RundiNova Tech")

        self.assertFalse(clear_default_workspace(user))
        self.assertEqual(user.default_workspace, "RundiNova Tech")
        exists.assert_called_once_with("Workspace", "RundiNova Tech")

    def test_leaves_empty_default_workspace_unset_until_provisioning(self):
        exists = Mock()
        clear_default_workspace = load_clear_orphaned_default_workspace(exists)
        user = SimpleNamespace(default_workspace=None)

        self.assertFalse(clear_default_workspace(user))
        self.assertIsNone(user.default_workspace)
        exists.assert_not_called()
