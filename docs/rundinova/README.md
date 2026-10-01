---
title: RundiNova Tech ERP
---

# RundiNova Tech ERP

This directory contains the deployment and business implementation contract
for the RundiNova Tech management platform. It does not contain the public
static website and it does not store production secrets.

## Documents

- [Architecture](01-architecture.md)
- [Business model](02-business-model.md)
- [Rollout plan](03-rollout.md)

## First deployment profile

The first deployment is one ERP site with one Gitega office. The data model is
multi-office from the beginning: offices are branches and cost centers, while
the hostname remains independent from the public website. Additional offices
can be added without redesigning the accounting or reporting model.

## Build the application image

Use Docker BuildKit and keep the application manifest outside the image layers:

```bash
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --secret=id=apps_json,src=apps-rundinova.json \
  --tag=rundinova/erpnext:16.36.1 \
  --file=images/rundinova/Containerfile .
```

The actual production image should be pushed to a private registry and the
tag should be pinned in the private environment file.

## Configuration and hostname

Copy `rundinova.env.example` to a private file such as
`~/gitops/rundinova.env`, replace the database password and email, and set the
real hostname. The DNS record for the ERP hostname must point to the server;
the static website can continue to use its own hosting and DNS records.

Render the production Compose file with MariaDB, Redis and the HTTPS proxy:

```bash
docker compose --project-name rundinova \
  --env-file ~/gitops/rundinova.env \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.nginxproxy.yaml \
  -f overrides/compose.nginxproxy-ssl.yaml config \
  > ~/gitops/compose.rundinova.yaml
```

Start it only after reviewing the rendered file:

```bash
docker compose --project-name rundinova \
  -f ~/gitops/compose.rundinova.yaml up -d
```

## Site creation

Choose the final hostname before running this command. The site hostname is
an internal ERP identity and can be different from the public website domain.

```bash
docker compose --project-name rundinova \
  -f ~/gitops/compose.rundinova.yaml exec backend \
  bench new-site \
  --mariadb-user-host-login-scope=% \
  --db-root-password "REPLACE_WITH_THE_DB_PASSWORD_FROM_rundinova.env" \
  --admin-password "REPLACE_WITH_A_UNIQUE_ADMIN_PASSWORD" \
  --install-app erpnext \
  erp.rundinova.com
```

Install the additional apps after the site exists:

```bash
docker compose --project-name rundinova \
  -f ~/gitops/compose.rundinova.yaml exec backend \
  bench --site erp.rundinova.com install-app hrms

docker compose --project-name rundinova \
  -f ~/gitops/compose.rundinova.yaml exec backend \
  bench --site erp.rundinova.com install-app crm

docker compose --project-name rundinova \
  -f ~/gitops/compose.rundinova.yaml exec backend \
  bench --site erp.rundinova.com install-app rundinova_tech
```

Do not use the demo password from `pwd.yml` in production. Before creating
real employees or financial records, change the administrator credentials,
enable two-factor authentication, configure backups and complete the Stage 1
acceptance checks in [the rollout plan](03-rollout.md).
