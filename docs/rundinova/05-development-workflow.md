# RundiNova development workflow

Use the development override while editing the custom app. It mounts the
working tree into the Frappe services, so normal Python, JSON and template
changes do not require a Docker image rebuild.

```bash
docker compose --env-file rundinova.env \
  -f compose.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.rundinova-dev.yaml up -d
```

After Python/DocType changes, run migrations and restart the workers:

```bash
docker compose --env-file rundinova.env -f compose.yaml \
  -f overrides/compose.redis.yaml -f overrides/compose.mariadb.yaml \
  -f overrides/compose.rundinova-dev.yaml exec backend \
  bench --site erp.rundinova.local migrate
docker compose --env-file rundinova.env -f compose.yaml \
  -f overrides/compose.redis.yaml -f overrides/compose.mariadb.yaml \
  -f overrides/compose.rundinova-dev.yaml restart backend queue-short queue-long scheduler websocket
```

For JavaScript/CSS or changed public assets, rebuild only the app assets:

```bash
docker compose --env-file rundinova.env -f compose.yaml \
  -f overrides/compose.redis.yaml -f overrides/compose.mariadb.yaml \
  -f overrides/compose.rundinova-dev.yaml exec backend \
  bench build --app rundinova_tech
```

Build a new Docker image only for a release or production deployment. The
production image remains versioned and immutable.
