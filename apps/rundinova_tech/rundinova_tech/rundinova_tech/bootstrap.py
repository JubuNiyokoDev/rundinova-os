"""Stable Frappe bootstrap entry points for the RundiNova site.

Implementation lives in focused site_bootstrap and provisioning modules;
these re-exports preserve existing bench commands and hook paths.
"""

import frappe
from rundinova_tech.rundinova_tech.setup import seed

from .provisioning.workspaces import (
    UNUSED_WORKSPACES,
    hide_unused_desktop_icons,
    hide_unused_workspaces,
)
from .site_bootstrap.company import (
    COMPANY_ABBR,
    COMPANY_NAME,
    ensure_company,
    ensure_transit_warehouse_type,
)
from .site_bootstrap.diagnostics import (
    check_page_access,
    check_sidebar,
    current_state,
    permission_report,
)
from .site_bootstrap.team import TEAM_USERS, ensure_team_users


def run():
    """Bootstrap entry point; returns a small status report."""
    report = {}
    report["warehouse_type"] = ensure_transit_warehouse_type()
    report["company"] = ensure_company()
    report["seed"] = run_seed()
    report["team_users"] = ensure_team_users()
    report["hidden_workspaces"] = hide_unused_workspaces()
    hide_unused_desktop_icons()
    frappe.db.commit()
    report["checks"] = current_state()
    return report


def run_seed():
    result = seed()
    frappe.db.commit()
    return result
