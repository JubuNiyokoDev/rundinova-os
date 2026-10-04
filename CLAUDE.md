# CLAUDE.md

## Projet

RundiNova OS combine l’infrastructure de déploiement de `frappe_docker` avec
l’application Frappe `apps/rundinova_tech`. C’est une plateforme open source
d’opérations, finance, impact et gouvernance, construite sur Frappe, ERPNext,
HRMS et CRM.

- `apps/rundinova_tech/` : DocTypes, pages, règles métier et bootstrap RundiNova.
- `images/rundinova/Containerfile` : image Frappe personnalisée.
- `compose.yaml` et `overrides/` : services et profils de déploiement.
- `docs/rundinova/` : architecture, déploiement et workflow produit.

## Stack technique

- Docker Engine/BuildKit et Docker Compose v2.
- Frappe Framework v16, ERPNext v16, HRMS v16 et CRM (`main`).
- Python >= 3.10, Bench et paquet Python `setuptools`.
- Nginx, Gunicorn, Socket.IO, workers RQ et scheduler.
- MariaDB et Redis (cache, files d’attente et pub/sub).
- Documentation VitePress avec pnpm.

## Commandes courantes

### Développement RundiNova

```bash
docker compose --env-file rundinova.env \
  -f compose.yaml -f overrides/compose.redis.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.rundinova-dev.yaml up -d

docker compose --env-file rundinova.env -f compose.yaml \
  -f overrides/compose.redis.yaml -f overrides/compose.mariadb.yaml \
  -f overrides/compose.rundinova-dev.yaml exec backend \
  bench --site erp.rundinova.local migrate

docker compose --env-file rundinova.env -f compose.yaml \
  -f overrides/compose.redis.yaml -f overrides/compose.mariadb.yaml \
  -f overrides/compose.rundinova-dev.yaml exec backend \
  bench build --app rundinova_tech
```

Après une migration, redémarrer `backend queue-short queue-long scheduler websocket`.
Pour initialiser les données de configuration :
`bench --site <site> execute rundinova_tech.rundinova_tech.bootstrap.run`.

### Image et déploiement

```bash
docker build --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --secret=id=apps_json,src=apps-rundinova.json \
  --tag=rundinova/erpnext:16.36.1 \
  --file=images/rundinova/Containerfile .

docker compose --env-file rundinova.env -f compose.yaml \
  -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml \
  -f overrides/compose.nginxproxy.yaml \
  -f overrides/compose.nginxproxy-ssl.yaml config
```

### Vérification et documentation

```bash
pre-commit run --all-files
pytest
(cd docs && pnpm docs:dev)
(cd docs && pnpm docs:build)
```

## Session Claude Code

Au début de chaque session, lire `.claude/COMMON_MISTAKES.md`, `.claude/QUICK_START.md`
et `.claude/ARCHITECTURE_MAP.md`. À la fin, créer
`.claude/completions/YYYY-MM-DD-task-name.md`; archiver le fichier de session
s’il a été créé. Ne pas charger automatiquement `.claude/completions/`,
`.claude/sessions/` ou `docs/archive/`.

**Dernière mise à jour** : 2026-10-03
