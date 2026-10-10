"""Pure serialization helpers for the RundiNova workspace home layout."""

import json

OPERATION_SECTIONS = (
    ("Démarrage & organisation", {"rundinova-onboarding", "RundiNova Office"}),
    (
        "Finance & achats",
        {
            "RundiNova Food Budget",
            "RundiNova Food Expense",
            "RundiNova Cash Movement",
            "RundiNova Cash Account",
            "RundiNova Expense",
            "RundiNova Budget Review",
        },
    ),
    ("Projets & livraison", {"Project", "Task", "RundiNova Repository"}),
    (
        "Communication & partenariats",
        {
            "/crm",
            "RundiNova Growth Opportunity",
            "RundiNova Partnership",
            "RundiNova Community Impact",
        },
    ),
    (
        "Équipe & gouvernance",
        {
            "RundiNova Food Progress",
            "RundiNova Asset",
            "RundiNova Decision",
            "RundiNova Document",
            "RundiNova KPI Definition",
            "RundiNova KPI Snapshot",
            "RundiNova Goal",
        },
    ),
    ("Administration", {"/desk/rundinova-setup"}),
)


def _workspace_content(
    title, shortcut_rows, block_prefix, chart_rows=(), number_card_rows=()
):
    """Serialize Workspace shortcuts, indicators, and charts into Desk blocks."""
    content = [
        {
            "id": f"{block_prefix}-title",
            "type": "header",
            "data": {"text": f"{title} · Centre de pilotage", "col": 12},
        }
    ]

    dashboards = [row for row in shortcut_rows if row.type == "Dashboard"]
    operational_shortcuts = [row for row in shortcut_rows if row.type != "Dashboard"]
    if dashboards:
        content.append(
            {
                "id": f"{block_prefix}-dashboards-title",
                "type": "header",
                "data": {"text": "Tableaux de bord", "col": 12},
            }
        )
    for idx, shortcut in enumerate(dashboards):
        content.append(
            {
                "id": f"{block_prefix}-shortcut-{idx}",
                "type": "shortcut",
                # Frappe resolves this against the child shortcut's label.
                "data": {"shortcut_name": shortcut.label, "col": 4},
            }
        )
    for idx, number_card in enumerate(number_card_rows):
        if idx == 0:
            content.append(
                {
                    "id": f"{block_prefix}-indicators-title",
                    "type": "header",
                    "data": {"text": "Indicateurs clés", "col": 12},
                }
            )
        content.append(
            {
                "id": f"{block_prefix}-number-card-{idx}",
                "type": "number_card",
                "data": {"number_card_name": number_card.label, "col": 3},
            }
        )
    for idx, chart in enumerate(chart_rows):
        content.append(
            {
                "id": f"{block_prefix}-chart-{idx}",
                "type": "chart",
                "data": {"chart_name": chart.label, "col": 6},
            }
        )

    grouped_shortcuts = {section: [] for section, _targets in OPERATION_SECTIONS}
    ungrouped_shortcuts = []
    for shortcut in operational_shortcuts:
        target = getattr(shortcut, "link_to", None) or getattr(shortcut, "url", None)
        section = next(
            (name for name, targets in OPERATION_SECTIONS if target in targets), None
        )
        (grouped_shortcuts[section] if section else ungrouped_shortcuts).append(
            shortcut
        )

    for section_index, (section, _targets) in enumerate(OPERATION_SECTIONS):
        shortcuts = grouped_shortcuts[section]
        if not shortcuts:
            continue
        content.append(
            {
                "id": f"{block_prefix}-operations-title-{section_index}",
                "type": "header",
                "data": {"text": section, "col": 12},
            }
        )
        for shortcut_index, shortcut in enumerate(shortcuts):
            content.append(
                {
                    "id": f"{block_prefix}-operation-{section_index}-{shortcut_index}",
                    "type": "shortcut",
                    "data": {"shortcut_name": shortcut.label, "col": 4},
                }
            )
    if ungrouped_shortcuts:
        content.append(
            {
                "id": f"{block_prefix}-operations-title-other",
                "type": "header",
                "data": {"text": "Autres opérations", "col": 12},
            }
        )
        for idx, shortcut in enumerate(ungrouped_shortcuts):
            content.append(
                {
                    "id": f"{block_prefix}-operation-other-{idx}",
                    "type": "shortcut",
                    "data": {"shortcut_name": shortcut.label, "col": 4},
                }
            )
    return json.dumps(content, ensure_ascii=False)
