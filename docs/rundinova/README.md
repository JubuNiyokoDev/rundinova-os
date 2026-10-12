---
title: RundiNova Tech ERP
---

# RundiNova Tech ERP

This directory contains the deployment and business implementation contract
for the RundiNova Tech management platform. It does not contain the public
static website and it does not store production secrets.

## Documents

- [Repository architecture and contributor map](00-repository-guide.md)
- [Architecture](01-architecture.md)
- [Business model](02-business-model.md)
- [Rollout plan](03-rollout.md)
- [Approved V1 scope and acceptance checklist](04-v1-scope.md)
- [Roles and responsibilities](06-roles-and-responsibilities.md)
- [Production team acceptance tests](PRODUCTION_ACCEPTANCE_TESTS.md)
- [GitHub access and AI project reviews](08-github-and-ai.md)
- [Self-hosted releases and controlled upstream updates](07-self-hosted-release.md)

## First deployment profile

The first deployment is one ERP site with one Gitega office. The data model is
multi-office from the beginning: offices are branches and cost centers, while
the hostname remains independent from the public website. Additional offices
can be added without redesigning the accounting or reporting model.

## Build the application image

For the initial stack image or an intentional upstream framework update, use
the controlled candidate process in [the self-hosted release guide](07-self-hosted-release.md).
Pin the Frappe/ERPNext/HRMS/CRM inputs and build-image digests for that release;
do not treat a moving branch as an automatic update mechanism. For ordinary
RundiNova app changes, use the local overlay builder documented there. It
starts from an image already present on the host and does not change the
framework revisions.

The resulting image tag is selected explicitly in the private environment
file. Self-hosted deployments can keep that image on the local Docker host;
publishing to a private registry is optional.

## Configuration and hostname

Copy `rundinova.env.example` to a private file such as
`~/gitops/rundinova.env`, replace the database password and email, and set the
real hostname. The DNS record for the ERP hostname must point to the server;
the static website can continue to use its own hosting and DNS records.

Before starting the stack, replace `CUSTOM_TAG` with the exact release tag and
make that image available on the Docker host. Build it from an approved local
base, load a verified release archive, or pull it explicitly from the private
registry. `PULL_POLICY=never` prevents Compose from silently selecting or
downloading a different image. Confirm the rendered image and local image ID:

```bash
docker compose --project-name rundinova \
  --env-file ~/gitops/rundinova.env \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.nginxproxy.yaml \
  -f overrides/compose.nginxproxy-ssl.yaml config --images

docker image inspect rundinova/erpnext:<release-tag> \
  --format '{{.Id}} {{json .RepoDigests}}'
```

The environment example deliberately uses a placeholder tag so a new
installation cannot accidentally select an old local release.

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
