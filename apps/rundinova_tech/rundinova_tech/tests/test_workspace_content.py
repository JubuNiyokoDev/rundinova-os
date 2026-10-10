"""Tests for the RundiNova operations workspace layout."""

import json
import unittest
from types import SimpleNamespace

from rundinova_tech.rundinova_tech.provisioning.workspace_layout import (
    _workspace_content,
)


class TestWorkspaceContent(unittest.TestCase):
    def test_dashboard_links_and_operational_shortcuts_are_grouped(self):
        content = json.loads(
            _workspace_content(
                "RundiNova Tech",
                [
                    SimpleNamespace(type="DocType", label="Projets", link_to="Project"),
                    SimpleNamespace(
                        type="DocType",
                        label="Achats alimentaires",
                        link_to="RundiNova Food Expense",
                    ),
                    SimpleNamespace(type="Dashboard", label="Pilotage exécutif"),
                    SimpleNamespace(
                        type="URL",
                        label="Configuration RundiNova",
                        url="/desk/rundinova-setup",
                    ),
                ],
                "test-home",
                chart_rows=[],
                number_card_rows=[],
            )
        )

        widget_types = [block["type"] for block in content]
        self.assertLess(widget_types.index("header", 1), widget_types.index("shortcut"))
        self.assertEqual(
            [
                block["data"]["shortcut_name"]
                for block in content
                if block["type"] == "shortcut"
            ],
            [
                "Pilotage exécutif",
                "Achats alimentaires",
                "Projets",
                "Configuration RundiNova",
            ],
        )
        headers = [
            block["data"]["text"] for block in content if block["type"] == "header"
        ]
        self.assertIn("Tableaux de bord", headers)
        self.assertIn("Finance & achats", headers)
        self.assertIn("Projets & livraison", headers)
        self.assertIn("Administration", headers)
        self.assertLess(
            headers.index("Finance & achats"), headers.index("Projets & livraison")
        )
        self.assertEqual(
            [
                block["data"]["shortcut_name"]
                for block in content
                if block["type"] == "shortcut"
            ][-1],
            "Configuration RundiNova",
        )

    def test_overview_widgets_use_native_workspace_block_types(self):
        content = json.loads(
            _workspace_content(
                "RundiNova Tech",
                [],
                "test-home",
                chart_rows=[SimpleNamespace(label="Projets par statut")],
                number_card_rows=[SimpleNamespace(label="Projets actifs")],
            )
        )

        blocks = {block["type"]: block for block in content}
        self.assertEqual(
            blocks["number_card"]["data"]["number_card_name"], "Projets actifs"
        )
        self.assertEqual(blocks["chart"]["data"]["chart_name"], "Projets par statut")


if __name__ == "__main__":
    unittest.main()
