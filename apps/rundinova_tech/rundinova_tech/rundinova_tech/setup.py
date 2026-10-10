"""Stable Frappe hook entry points for RundiNova provisioning.

Implementation is split by responsibility under the provisioning package.
Keep these re-exports so installed hooks and integrations retain their paths.
"""

from .provisioning.branding import sync_branding
from .provisioning.dashboards import sync_dashboards
from .provisioning.fields import (
    backfill_budget_titles,
    ensure_project_repository_field,
    ensure_purchase_invoice_budget_field,
    ensure_task_repository_field,
    fix_company_currency,
)
from .provisioning.form_layouts import sync_form_layouts
from .provisioning.permissions import ensure_rundinova_permissions
from .provisioning.roles import ensure_rundinova_roles
from .provisioning.workspaces import hide_unused_desktop_icons, hide_unused_workspaces


def seed():
    """Provision configuration only; never create fictitious business data."""
    roles = ensure_rundinova_roles()
    permissions = ensure_rundinova_permissions()
    sync_dashboards()
    branding = sync_branding()
    form_layouts = sync_form_layouts()
    hidden_workspaces = hide_unused_workspaces()
    hide_unused_desktop_icons()
    fix_company_currency()
    return {
        "configured": True,
        "business_data_created": False,
        "roles": roles,
        "permissions": list(permissions),
        "branding": branding,
        "form_layouts": form_layouts,
        "hidden_workspaces": hidden_workspaces,
        "currency_symbol": "FBU",
    }
