# Repository architecture and contributor map

This repository is the complete, locally controlled RundiNova deployment. It
contains both the Docker platform configuration and the RundiNova Frappe app.
The framework is still Frappe; upstream changes enter only through an
intentional release update.

## Two code layers

| Layer | Owns | Main locations |
| --- | --- | --- |
| Self-hosted platform | Images, services, databases, Redis, proxy and deployment profiles | `compose.yaml`, `overrides/`, `images/` |
| RundiNova product | Business records, workflows, permissions, workspace and dashboards | `apps/rundinova_tech/` |

The platform starts the app. The app does not own infrastructure lifecycle, and
the platform does not define RundiNova business rules. Keep changes in the
layer that owns the behavior.

## Directory map

```text
apps/rundinova_tech/                 Installable RundiNova Frappe app
  pyproject.toml                     App packaging and Python metadata
  rundinova_tech/                    Python package
    hooks.py                         Frappe lifecycle and permission hook registry
    api.py                           App API endpoints
    config/                          Desk module and app configuration
    public/                          Browser assets shipped with the app
    rundinova_tech/                  RundiNova business module
      domain/                        Framework-independent business calculations and rules
      doctype/                       Frappe DocType definitions and controllers
      page/                          Custom Desk pages
      setup.py                       Stable Frappe setup-hook compatibility entry points
      provisioning/                   Idempotent setup operations by responsibility
        roles.py                      RundiNova role creation
        permissions.py                Role permission policy persistence
        fields.py                     Cross-app custom fields and data backfills
        dashboards.py                 Dashboard cards, charts and dashboard composition
        workspaces.py                 Role-aware Desk workspaces and shortcuts
      site_bootstrap/                 First-site setup by responsibility (company, team, diagnostics)
      bootstrap.py                   Stable Frappe bootstrap command and hook facade
      access_control.py              Record-level query and document access rules
compose.yaml                         Base service topology
overrides/                           Optional deployment profiles and adapters
images/rundinova/                    RundiNova image overlay and build inputs
docs/rundinova/                      Product, architecture, release and user guidance
docs/                                Docker/Frappe platform reference documentation
tests/                               Compose and platform integration checks
development/                         Examples and local developer tooling
.github/                             CI, release and repository automation
```

## How the app is organized

Each Frappe DocType keeps its schema JSON and Python controller together in its
own directory. This is a framework convention: the JSON defines fields and
metadata; the controller defines server behavior. Keep the pair together and
add a focused test when changing business behavior.

`hooks.py` is the framework registration point. Keep behavior in the owning
module and register its callable in the hook map. `setup.py` preserves the
stable hook paths used by existing sites and delegates to `provisioning/`.
Provisioning operations must remain idempotent because install and migration
hooks can run repeatedly. Access checks belong in `access_control.py` and must
cover both list queries and direct document reads where applicable.

Use the Frappe business module as the boundary for related DocTypes, then keep
cross-cutting UI assets under `public/` and desk configuration under `config/`.
Avoid creating a second app or copying framework code into the RundiNova app.

New business calculations and decision rules belong in `domain/` when they
can run on plain Python values. DocType controllers remain Frappe adapters:
they load records, enforce permissions, translate domain rule codes into user
messages, and persist results. Domain modules must not import Frappe or access
the database. This boundary is being introduced workflow by workflow so the
current DocTypes, IDs, and stored business data stay stable.

Run the framework-independent business-rule suite from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=apps/rundinova_tech \
  python3 -m unittest discover \
  -s apps/rundinova_tech/rundinova_tech/tests -p 'test_*.py' -v
python3 -m unittest discover \
  -s images/rundinova/tests -p 'test_*.py' -v
python3 .github/scripts/validate_compose.py
```

The business-rule and release-provenance tests run without a Frappe site or
database. Compose validation checks every supported profile without starting
containers. Controller, permission, and workflow integration still requires
the installed Frappe environment.

## Deployment source of truth

- `apps-rundinova.json` records the app set used by the bench image.
- `images/rundinova/Overlay.Containerfile` adds the RundiNova app to an
  explicitly selected, already approved base image.
- `compose.yaml` and one selected set of overrides describe the running site.
- `rundinova.env.example` documents supported configuration without secrets.
- `docs/rundinova/07-self-hosted-release.md` is the operator release procedure.

The override files are deployment profiles, not duplicate service definitions:
they support different database, proxy, TLS, and local-development choices.
Do not delete or merge one until its use and documentation references have
been checked. The active local instance uses `overrides/compose.mariadb.yaml`,
`overrides/compose.redis.yaml`, and `overrides/compose.noproxy.yaml`.

## Local state and generated files

`sites/` contains live site data and is intentionally ignored by Git. Python
bytecode, pytest cache, and `.claude/worktrees/` are reproducible local
artifacts; they are not application source. Keep credentials, database dumps,
and generated site files out of commits. Tool-specific local state such as
`.codebuddy/` and `.claude/` is developer tooling, not part of the deployed app.

## Contributor workflow

1. Read this map and the relevant product or release guide before changing a
   business workflow or deployment profile.
2. Make the change in its owning layer and preserve the established Frappe
   directory conventions.
3. Review the Compose profile or app release procedure that will ship it.
4. Record user-visible behavior and operator steps in `docs/rundinova/`.
5. Keep upstream framework revisions pinned; promote them in a separate,
   deliberate update after reviewing compatibility.
