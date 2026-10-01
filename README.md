# RundiNova OS

RundiNova OS is an open-source operations, finance, impact, and governance
platform for organizations that need one reliable system for people, programs,
budgets, partnerships, and reporting.

It is built on [Frappe](https://github.com/frappe/frappe),
[ERPNext](https://github.com/frappe/erpnext), HRMS, and CRM. This repository
contains the RundiNova application, its Docker image definition, and the
deployment infrastructure required to run it.

## What RundiNova provides

- operational and office management;
- budgets, food-program expenses, and financial controls;
- partnerships, opportunities, risks, and community impact;
- KPI definitions and snapshots for management reporting;
- role-based workflows, auditability, and multi-office reporting;
- a production-ready Docker deployment profile.

## Repository map

```text
apps/rundinova_tech/  RundiNova business application and DocTypes
docs/rundinova/       Product architecture, business model, and rollout plan
images/rundinova/     Custom ERPNext image definition
apps-rundinova.json   Frappe/ERPNext/HRMS/CRM application manifest
compose.yaml          Base production Compose configuration
overrides/            Database, Redis, proxy, TLS, and deployment options
rundinova.env.example Safe configuration template (no production secrets)
```

The Docker and Compose files are the platform layer; RundiNova is the product
and business layer. Keeping both in one repository makes a deployment
reproducible while keeping company-specific logic in the `rundinova_tech` app.

## Quick start for development

Prerequisites: Docker, Docker Compose v2, Git, and access to the required
Frappe/ERPNext images.

```bash
git clone git@github.com:JubuNiyokoDev/rundinova-os.git
cd rundinova-os
cp rundinova.env.example rundinova.env
# Edit rundinova.env and set a unique DB_PASSWORD.
docker compose --env-file rundinova.env -f compose.yaml config
```

For a complete deployment, including MariaDB, Redis, HTTPS, site creation,
and installation of the RundiNova app, follow
[`docs/rundinova/README.md`](docs/rundinova/README.md).

## Production principles

- Never commit `rundinova.env`, database dumps, or credentials.
- Pin image and app versions before a production rollout.
- Use HTTPS, two-factor authentication, role-based access, and encrypted
  backups.
- Review the rendered Compose file before starting a production stack.
- Keep the public website separate from the ERP hostname and data store.

## Technology

RundiNova OS uses Frappe as its application framework, ERPNext for core
business processes, HRMS and CRM for people and pipeline management, and
Docker Compose for repeatable deployment. Frappe is the foundation; RundiNova
is the custom product built on top of it.

## Documentation

- [Product and deployment guide](docs/rundinova/README.md)
- [Architecture](docs/rundinova/01-architecture.md)
- [Business model](docs/rundinova/02-business-model.md)
- [Rollout plan](docs/rundinova/03-rollout.md)
- [Contributing](CONTRIBUTING.md)

## License

The RundiNova application and this deployment configuration are released under
the MIT License. See [LICENSE](LICENSE). Frappe, ERPNext, HRMS, and CRM remain
under their respective upstream licenses.

## Maintainer

RundiNova Tech — <https://github.com/JubuNiyokoDev>
