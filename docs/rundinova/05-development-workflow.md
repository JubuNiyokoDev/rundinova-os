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

## Test levels

Run the framework-independent business and release tests before preparing a
candidate:

```bash
PYTHONPATH=apps/rundinova_tech python3 -m unittest discover \
  -s apps/rundinova_tech/rundinova_tech/tests -p 'test_*.py'
PYTHONPATH=apps/rundinova_tech python3 -m unittest discover \
  -s apps/rundinova_tech/rundinova_core/tests -p 'test_*.py'
python3 -m unittest discover \
  -s images/rundinova/tests -p 'test_*.py'
```

The pure business core can also be installed without Frappe, ERPNext or a
database. See [`rundinova-core`](../../apps/rundinova_tech/rundinova_core/README.md)
for the isolated installation check.

Frappe controller tests live beside their DocTypes and need an installed app.
They use Frappe's `UnitTestCase` because these controller validations do not
need database records. Run them through the disposable Frappe test harness
against a locally built candidate image:

```bash
RN_TEST_IMAGE=rundinova/erpnext:<candidate-tag> \
  bash tests/run-rundinova-frappe-tests.sh
```

The harness creates a unique Compose project with its own MariaDB, Redis, and
sites volumes, installs ERPNext, HRMS, CRM, and RundiNova, runs a full Frappe
migration to exercise post-migration provisioning, installs and tests the
standalone core package inside the image, then runs the controller suites with
`bench run-tests`. It removes only that temporary
project and its volumes. It tests the RundiNova source embedded in the chosen
image and never mounts or connects to the active business site. The runner
requires Frappe to report executed tests for every suite, so a disabled or
empty test run cannot pass silently.
