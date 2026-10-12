import frappe

from .workspace_layout import OPERATION_SECTIONS, _workspace_content

UNUSED_WORKSPACES = [
    # ERPNext core modules not needed by a dev hub
    "Assets",
    "Build",
    "Buying",
    "Expenses",
    "Financial Reports",
    "Integrations",
    "Invoicing",
    "Manufacturing",
    "Projects",
    "Quality",
    "Selling",
    "Stock",
    "Subcontracting",
    "Support",
    "Website",
    # HRMS modules (no formal HR processes for 5 co-founders)
    "HR Setup",
    "Leaves",
    "Payroll",
    "Performance",
    "Recruitment",
    "Shift & Attendance",
    "Tax & Benefits",
    "Tenure",
    # Misc
    "Home",
    "Welcome Workspace",
    # Generic ERP setup / module entry points are replaced by role-aware
    # RundiNova operations and setup workspaces.
    "Organization",
    "Accounting",
    "Accounts Setup",
    "Budget",
    "Subscription",
]

VISIBLE_DESKTOP_ICONS = {
    "RundiNova Tech",
    "RundiNova Team",
    "RundiNova Developer",
    "RundiNova Finance",
    "RundiNova Operations",
    "RundiNova Delivery",
    "RundiNova Ecosystem",
    "RundiNova Growth",
    "RundiNova Community",
    "RundiNova Communications",
    "RundiNova People",
    "Frappe CRM",
}

DEFAULT_WORKSPACE_BY_ROLE = (
    ("RundiNova Director", "RundiNova Tech"),
    ("RundiNova Developer", "RundiNova Developer"),
    ("RundiNova Finance Manager", "RundiNova Finance"),
    ("RundiNova Operations", "RundiNova Operations"),
    ("RundiNova Project Lead", "RundiNova Delivery"),
    ("RundiNova Ecosystem Lead", "RundiNova Ecosystem"),
    ("RundiNova Growth Lead", "RundiNova Growth"),
    ("RundiNova Community Relations", "RundiNova Community"),
    ("RundiNova Communications", "RundiNova Communications"),
    ("RundiNova People & Culture", "RundiNova People"),
    ("RundiNova Team Member", "RundiNova Team"),
)


def _sync_workspace(
    name,
    title,
    module,
    app,
    sequence,
    icon,
    links,
    block_prefix,
    roles,
    charts=(),
    number_cards=(),
    hidden=False,
    public=1,
):
    workspace = (
        frappe.get_doc("Workspace", name)
        if frappe.db.exists("Workspace", name)
        else frappe.new_doc("Workspace")
    )
    if not workspace.name:
        workspace.name = name
        workspace.flags.name_set = True
    workspace.update(
        {
            "label": title,
            "title": title,
            "module": module,
            "app": app,
            "type": "Workspace",
            "sequence_id": sequence,
            "icon": icon,
            "public": public,
            "is_hidden": int(hidden),
        }
    )
    workspace.roles = []
    for role in roles:
        workspace.append("roles", {"role": role})
    # These app-owned links are the source of truth. Removing obsolete rows
    # avoids accumulating stale entries as the navigation evolves.
    workspace.shortcuts = []
    for shortcut_type, target, label, shortcut_icon in links:
        shortcut = {
            "type": shortcut_type,
            "label": label,
            "icon": shortcut_icon,
        }
        shortcut["url" if shortcut_type == "URL" else "link_to"] = target
        workspace.append("shortcuts", shortcut)
    workspace.charts = []
    for chart, label in charts:
        workspace.append("charts", {"chart_name": chart, "label": label})
    workspace.number_cards = []
    for card, label in number_cards:
        workspace.append("number_cards", {"number_card_name": card, "label": label})
    workspace.save(ignore_permissions=True)
    workspace.reload()
    workspace.content = _workspace_content(
        title,
        workspace.shortcuts,
        block_prefix,
        workspace.charts,
        workspace.number_cards,
    )
    workspace.save(ignore_permissions=True)
    return workspace


def _sync_workspace_sidebar(title, icon, items):
    """Keep the persistent Frappe sidebar aligned with the workspace links."""
    sidebar = (
        frappe.get_doc("Workspace Sidebar", title)
        if frappe.db.exists("Workspace Sidebar", title)
        else frappe.new_doc("Workspace Sidebar")
    )
    sidebar.title = title
    sidebar.app = "rundinova_tech"
    sidebar.module = "RundiNova Tech"
    sidebar.header_icon = icon
    sidebar.for_user = None
    sidebar.items = []
    for item in items:
        sidebar.append("items", item)
    sidebar.save(ignore_permissions=True)


def _ensure_workspace_desktop_icon(title, icon, roles, visible=True, label=None):
    label = label or title
    desktop_icon = (
        frappe.get_doc("Desktop Icon", label)
        if frappe.db.exists("Desktop Icon", label)
        else frappe.new_doc("Desktop Icon")
    )
    desktop_icon.update(
        {
            "label": label,
            "icon_type": "Link",
            "link_type": "Workspace Sidebar",
            "link_to": label,
            "icon": icon,
            "bg_color": {
                "RundiNova Tech": "blue",
                "RundiNova Team": "gray",
                "RundiNova Setup": "blue",
            }.get(title, "gray"),
            "hidden": 0 if visible else 1,
            "idx": 0,
        }
    )
    # Desktop Icons are global by default. Keep role-scoped workspaces from
    # leaking through the app launcher to users who cannot see the workspace.
    desktop_icon.roles = []
    for role in roles:
        desktop_icon.append("roles", {"role": role})
    desktop_icon.save(ignore_permissions=True)


def sync_workspaces(overview_charts=(), overview_number_cards=()):
    """Provision the role-aware RundiNova Desk navigation."""
    # Frappe's stock `workspace` home_page is not a Page DocType in this
    # version, so boot falls back to the generic module launcher. This app-owned
    # Page redirects to each user's default RundiNova workspace instead.
    frappe.db.set_default("desktop:home_page", "rundinova-home")

    operations_links = [
        (
            "Dashboard",
            "RundiNova Executive Dashboard",
            "Pilotage exécutif",
            "dashboard",
        ),
        ("Dashboard", "RundiNova Finance Dashboard", "Finance & budgets", "accounting"),
        ("Dashboard", "RundiNova People Dashboard", "Équipe & RH", "users"),
        ("Dashboard", "RundiNova Delivery Dashboard", "Projets & livraison", "project"),
        (
            "Dashboard",
            "RundiNova Ecosystem Dashboard",
            "Écosystème & croissance",
            "crm",
        ),
        ("Page", "rundinova-onboarding", "Préparation au démarrage", "tool"),
        ("DocType", "RundiNova Office", "Hub & organisation", "building"),
        ("DocType", "Project", "Projets", "project"),
        ("DocType", "Task", "Tâches", "tasks"),
        ("URL", "/crm", "CRM & communications", "crm"),
        ("DocType", "RundiNova Growth Opportunity", "Opportunités", "star"),
        ("DocType", "RundiNova Partnership", "Partenariats", "handshake"),
        ("DocType", "RundiNova Community Impact", "Activités communautaires", "heart"),
        ("DocType", "RundiNova Food Budget", "Budget alimentaire", "food"),
        ("DocType", "RundiNova Food Expense", "Achats alimentaires", "shopping-cart"),
        ("DocType", "RundiNova Cash Movement", "Mouvements de trésorerie", "money"),
        ("DocType", "RundiNova Cash Account", "Comptes de trésorerie", "bank"),
        ("DocType", "RundiNova Food Progress", "Progression Food", "chart"),
        ("DocType", "RundiNova Budget Review", "Revues de budget", "check-circle"),
        ("DocType", "RundiNova Repository", "Dépôts GitHub", "github"),
        ("DocType", "RundiNova Expense", "Dépenses générales", "expense"),
        ("DocType", "RundiNova Asset", "Biens & équipements", "asset"),
        ("DocType", "RundiNova Decision", "Décisions & réunions", "note"),
        ("DocType", "RundiNova Document", "Documents & fichiers", "file"),
        ("DocType", "RundiNova KPI Definition", "Définitions KPI", "target"),
        ("DocType", "RundiNova KPI Snapshot", "Mesures KPI", "analytics"),
        ("DocType", "RundiNova Goal", "Objectifs & KPI", "target"),
        ("URL", "/desk/rundinova-setup", "Configuration RundiNova", "settings"),
    ]
    team_links = [
        ("DocType", "RundiNova Office", "Hub & organisation", "building"),
        ("DocType", "RundiNova Food Expense", "Achats alimentaires", "shopping-cart"),
        ("DocType", "RundiNova Expense", "Dépenses générales", "expense"),
        ("DocType", "RundiNova Food Progress", "Progression Food", "chart"),
        ("DocType", "RundiNova Decision", "Décisions & réunions", "note"),
        ("DocType", "RundiNova Document", "Documents & fichiers", "file"),
        ("DocType", "RundiNova KPI Snapshot", "Mesures KPI", "analytics"),
    ]
    dashboard_links = [
        (
            "Dashboard",
            "RundiNova Executive Dashboard",
            "Pilotage exécutif",
            "dashboard",
        ),
        ("Dashboard", "RundiNova Finance Dashboard", "Finance & budgets", "accounting"),
        ("Dashboard", "RundiNova People Dashboard", "Équipe & RH", "users"),
        ("Dashboard", "RundiNova Delivery Dashboard", "Projets & livraison", "project"),
        (
            "Dashboard",
            "RundiNova Ecosystem Dashboard",
            "Écosystème & croissance",
            "crm",
        ),
    ]
    finance_links = [
        ("DocType", "RundiNova Food Budget", "Budgets alimentaires", "food"),
        ("DocType", "RundiNova Food Expense", "Achats alimentaires", "shopping-cart"),
        ("DocType", "RundiNova Budget Review", "Revues de budget", "check-circle"),
        ("DocType", "RundiNova Expense", "Dépenses générales", "expense"),
        ("DocType", "RundiNova Cash Account", "Comptes de trésorerie", "bank"),
        ("DocType", "RundiNova Cash Movement", "Mouvements de trésorerie", "money"),
        (
            "Dashboard",
            "RundiNova Finance Dashboard",
            "Tableau de bord Finance",
            "accounting",
        ),
    ]
    finance_workspace_roles = (
        "RundiNova Director",
        "RundiNova Finance Manager",
        "RundiNova Operations",
    )
    dashboard_workspace_roles = ("RundiNova Director",)
    product_workspace_roles = ("RundiNova Director",)
    _sync_workspace(
        "RundiNova Tech",
        "RundiNova Tech",
        "RundiNova Tech",
        "rundinova_tech",
        0,
        "briefcase",
        operations_links,
        "rundinova-home",
        ("RundiNova Director",),
        charts=overview_charts,
        number_cards=overview_number_cards,
        public=1,
    )
    _sync_workspace_sidebar(
        "RundiNova Tech",
        "briefcase",
        [
            {
                "type": "Link",
                "label": "Accueil RundiNova",
                "link_type": "Workspace",
                "link_to": "RundiNova Tech",
                "icon": "home",
            },
            {"type": "Section Break", "label": "Tableaux de bord", "collapsible": 0},
            *[
                {
                    "type": "Link",
                    "label": label,
                    "link_type": link_type,
                    "url" if link_type == "URL" else "link_to": target,
                    "icon": icon,
                }
                for link_type, target, label, icon in dashboard_links
            ],
            *[
                item
                for section, targets in OPERATION_SECTIONS
                for item in (
                    [{"type": "Section Break", "label": section, "collapsible": 0}]
                    + [
                        {
                            "type": "Link",
                            "label": label,
                            "link_type": link_type,
                            "link_to": target if link_type != "URL" else None,
                            "url": target if link_type == "URL" else None,
                            "icon": item_icon,
                        }
                        for link_type, target, label, item_icon in operations_links
                        if target in targets
                    ]
                )
            ],
        ],
    )
    _sync_workspace(
        "RundiNova Team",
        # Workspace routes are derived from the title. Keep this ASCII so the
        # Desk route is stable across browsers and Frappe's slug handling.
        "RundiNova Team",
        "RundiNova Tech",
        "rundinova_tech",
        0.25,
        "users",
        team_links,
        "rundinova-team",
        ("RundiNova Team Member",),
        hidden=False,
        public=1,
    )
    _sync_workspace_sidebar(
        "RundiNova Team",
        "users",
        [
            {
                "type": "Link",
                "label": "Accueil équipe",
                "link_type": "Workspace",
                "link_to": "RundiNova Team",
                "icon": "home",
            },
            {"type": "Section Break", "label": "Travail quotidien", "collapsible": 0},
            *[
                {
                    "type": "Link",
                    "label": label,
                    "link_type": link_type,
                    "link_to": target,
                    "icon": icon,
                }
                for link_type, target, label, icon in team_links
            ],
        ],
    )
    _sync_workspace(
        "RundiNova Finance",
        "Finance & trésorerie",
        "RundiNova Tech",
        "rundinova_tech",
        0.5,
        "bank",
        finance_links,
        "rundinova-finance",
        finance_workspace_roles,
        hidden=False,
        public=1,
    )

    role_workspaces = [
        (
            "RundiNova Developer",
            "Développement & livraison",
            "code",
            ("RundiNova Developer",),
            [
                ("DocType", "Project", "Projets", "project"),
                ("DocType", "Task", "Tâches assignées", "tasks"),
                ("DocType", "RundiNova Repository", "Dépôts GitHub", "github"),
            ],
        ),
        (
            "RundiNova Operations",
            "Opérations & budget",
            "briefcase",
            ("RundiNova Director", "RundiNova Operations"),
            [
                *finance_links,
                ("DocType", "RundiNova Office", "Bureaux", "building"),
                ("DocType", "Project", "Projets", "project"),
                ("DocType", "Task", "Tâches", "tasks"),
                ("DocType", "RundiNova Document", "Documents", "file"),
            ],
        ),
        (
            "RundiNova Delivery",
            "Projets & livraison",
            "project",
            ("RundiNova Director", "RundiNova Project Lead"),
            [
                (
                    "Dashboard",
                    "RundiNova Delivery Dashboard",
                    "Tableau de bord Livraison",
                    "project",
                ),
                ("DocType", "Project", "Projets", "project"),
                ("DocType", "Task", "Tâches", "tasks"),
                ("DocType", "RundiNova Repository", "Dépôts GitHub", "github"),
                ("DocType", "RundiNova Risk", "Risques projet", "alert-triangle"),
            ],
        ),
        (
            "RundiNova Ecosystem",
            "Écosystème & partenariats",
            "handshake",
            ("RundiNova Director", "RundiNova Ecosystem Lead"),
            [
                (
                    "Dashboard",
                    "RundiNova Ecosystem Dashboard",
                    "Tableau de bord Écosystème",
                    "crm",
                ),
                ("DocType", "RundiNova Partnership", "Partenariats", "handshake"),
                ("DocType", "RundiNova Growth Opportunity", "Opportunités", "star"),
                ("DocType", "RundiNova Decision", "Décisions", "note"),
                ("DocType", "RundiNova Document", "Documents", "file"),
            ],
        ),
        (
            "RundiNova Growth",
            "Croissance & prospection",
            "growth",
            ("RundiNova Director", "RundiNova Growth Lead"),
            [
                (
                    "Dashboard",
                    "RundiNova Ecosystem Dashboard",
                    "Tableau de bord Croissance",
                    "crm",
                ),
                ("DocType", "RundiNova Growth Opportunity", "Opportunités", "star"),
                ("DocType", "CRM Lead", "Prospects", "crm"),
                ("DocType", "CRM Deal", "Affaires", "deal"),
                ("DocType", "Task", "Tâches", "tasks"),
            ],
        ),
        (
            "RundiNova Community",
            "Communauté & impact",
            "heart",
            ("RundiNova Director", "RundiNova Community Relations"),
            [
                (
                    "Dashboard",
                    "RundiNova Ecosystem Dashboard",
                    "Tableau de bord Impact",
                    "crm",
                ),
                (
                    "DocType",
                    "RundiNova Community Impact",
                    "Activités communautaires",
                    "heart",
                ),
                ("DocType", "RundiNova Decision", "Décisions", "note"),
                ("DocType", "RundiNova Document", "Documents", "file"),
                ("DocType", "RundiNova KPI Snapshot", "Mesures KPI", "analytics"),
            ],
        ),
        (
            "RundiNova Communications",
            "Communication & CRM",
            "chat",
            ("RundiNova Director", "RundiNova Communications"),
            [
                ("URL", "/crm", "CRM & communications", "crm"),
                ("DocType", "CRM Lead", "Contacts et prospects", "crm"),
                ("DocType", "CRM Call Log", "Journal de communication", "phone"),
                ("DocType", "Task", "Tâches", "tasks"),
                ("DocType", "RundiNova Document", "Documents", "file"),
            ],
        ),
        (
            "RundiNova People",
            "Équipe & personnes",
            "users",
            ("RundiNova Director", "RundiNova People & Culture"),
            [
                (
                    "Dashboard",
                    "RundiNova People Dashboard",
                    "Tableau de bord Équipe",
                    "users",
                ),
                ("DocType", "Employee", "Équipe", "users"),
                ("DocType", "HR Settings", "Paramètres RH", "settings"),
                ("DocType", "RundiNova Office", "Bureaux", "building"),
                ("DocType", "RundiNova KPI Snapshot", "Mesures KPI", "analytics"),
            ],
        ),
    ]
    for index, (name, title, icon, roles, links) in enumerate(role_workspaces, start=2):
        _sync_workspace(
            name,
            title,
            "RundiNova Tech",
            "rundinova_tech",
            index,
            icon,
            links,
            name.lower().replace(" ", "-"),
            roles,
            hidden=False,
            public=1,
        )
        sidebar_items = [
            {
                "type": "Link",
                "label": "Accueil " + title,
                "link_type": "Workspace",
                "link_to": name,
                "icon": "home",
            },
            {"type": "Section Break", "label": title, "collapsible": 0},
        ]
        sidebar_items.extend(
            {
                "type": "Link",
                "label": label,
                "link_type": link_type,
                "link_to": target if link_type != "URL" else None,
                "url": target if link_type == "URL" else None,
                "icon": link_icon,
            }
            for link_type, target, label, link_icon in links
        )
        _sync_workspace_sidebar(name, icon, sidebar_items)
        _ensure_workspace_desktop_icon(name, icon, roles, True, name)

    _sync_workspace(
        "RundiNova Dashboards",
        "RundiNova Dashboards",
        "RundiNova Tech",
        "rundinova_tech",
        1,
        "chart",
        dashboard_links,
        "rundinova-dashboards",
        dashboard_workspace_roles,
        hidden=True,
        public=0,
    )
    _sync_workspace_sidebar(
        "RundiNova Finance",
        "bank",
        [
            {
                "type": "Link",
                "label": "Accueil Finance",
                "link_type": "Workspace",
                "link_to": "RundiNova Finance",
                "icon": "home",
            },
            {"type": "Section Break", "label": "Trésorerie", "collapsible": 0},
            {
                "type": "Link",
                "label": "Comptes de trésorerie",
                "link_type": "DocType",
                "link_to": "RundiNova Cash Account",
                "icon": "bank",
            },
            {
                "type": "Link",
                "label": "Mouvements de trésorerie",
                "link_type": "DocType",
                "link_to": "RundiNova Cash Movement",
                "icon": "money",
            },
            {
                "type": "Link",
                "label": "Budgets alimentaires",
                "link_type": "DocType",
                "link_to": "RundiNova Food Budget",
                "icon": "food",
            },
            {
                "type": "Link",
                "label": "Achats alimentaires",
                "link_type": "DocType",
                "link_to": "RundiNova Food Expense",
                "icon": "shopping-cart",
            },
            {
                "type": "Link",
                "label": "Dépenses générales",
                "link_type": "DocType",
                "link_to": "RundiNova Expense",
                "icon": "expense",
            },
            {
                "type": "Link",
                "label": "Fournisseurs",
                "link_type": "DocType",
                "link_to": "Supplier",
                "icon": "truck",
            },
            {"type": "Section Break", "label": "Indicateurs", "collapsible": 0},
            {
                "type": "Link",
                "label": "Tableau de bord Finance",
                "link_type": "Dashboard",
                "link_to": "RundiNova Finance Dashboard",
                "icon": "accounting",
            },
        ],
    )
    _sync_workspace_sidebar(
        "RundiNova Dashboards",
        "chart",
        [
            {
                "type": "Link",
                "label": "Accueil Dashboards",
                "link_type": "Workspace",
                "link_to": "RundiNova Dashboards",
                "icon": "home",
            },
            {"type": "Section Break", "label": "Pilotage", "collapsible": 0},
            *[
                {
                    "type": "Link",
                    "label": label,
                    "link_type": link_type,
                    "url" if link_type == "URL" else "link_to": target,
                    "icon": icon,
                }
                for link_type, target, label, icon in dashboard_links
            ],
        ],
    )
    for title, icon, roles, visible, label in [
        (
            "RundiNova Tech",
            "briefcase",
            product_workspace_roles,
            True,
            "RundiNova Tech",
        ),
        (
            "RundiNova Team",
            "users",
            ("RundiNova Team Member",),
            True,
            "RundiNova Team",
        ),
        # Finance and dashboard destinations already live in the main app
        # sidebar. Keep their workspaces addressable, but avoid duplicate
        # tiles on the main launcher.
        (
            "RundiNova Finance",
            "bank",
            finance_workspace_roles,
            True,
            "RundiNova Finance",
        ),
        (
            "RundiNova Dashboards",
            "chart",
            dashboard_workspace_roles,
            False,
            "RundiNova Dashboards",
        ),
    ]:
        _ensure_workspace_desktop_icon(title, icon, roles, visible, label)

    # Put every RundiNova user on an intentional home instead of Frappe's
    # generic Welcome Workspace fallback.
    for user in frappe.get_all(
        "User", filters={"user_type": "System User"}, pluck="name"
    ):
        user_roles = set(frappe.get_roles(user))
        default_workspace = next(
            (
                workspace
                for role, workspace in DEFAULT_WORKSPACE_BY_ROLE
                if role in user_roles
            ),
            None,
        )
        current_default = frappe.db.get_value("User", user, "default_workspace")
        if default_workspace and current_default != default_workspace:
            frappe.db.set_value("User", user, "default_workspace", default_workspace)


def hide_unused_desktop_icons():
    """Show only the RundiNova workspaces and the CRM entry on the launcher."""
    for label in frappe.get_all("Desktop Icon", filters={"hidden": 0}, pluck="label"):
        if label not in VISIBLE_DESKTOP_ICONS:
            frappe.db.set_value("Desktop Icon", label, "hidden", 1)
    for user in frappe.get_all(
        "User", filters={"user_type": "System User"}, pluck="name"
    ):
        frappe.cache.hdel("desktop_icons", user)
        frappe.cache.hdel("bootinfo", user)

    # Older setup aliases are retired; role-specific workspaces remain visible.
    for label in ("RundiNova Setup", "RundiNova Dashboards"):
        if frappe.db.exists("Desktop Icon", label):
            frappe.db.set_value(
                "Desktop Icon", label, "hidden", 1, update_modified=False
            )


def hide_unused_workspaces():
    """Hide unused module workspaces while keeping their DocTypes installed."""
    newly_hidden = []
    for name in UNUSED_WORKSPACES:
        if not frappe.db.exists("Workspace", name):
            continue
        if not frappe.db.get_value("Workspace", name, "is_hidden"):
            frappe.db.set_value("Workspace", name, "is_hidden", 1)
            newly_hidden.append(name)
    frappe.db.commit()
    return newly_hidden or "already-hidden"
