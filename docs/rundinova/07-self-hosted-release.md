---
title: Self-hosted releases and controlled upstream updates
---

# Self-hosted releases and controlled upstream updates

RundiNova is delivered as one self-hosted stack: this repository, its custom
Frappe app, ERPNext, HRMS, CRM, database, Redis, and the locally built image.
The operator owns the running release. Starting the stack must not silently
replace that image with a newer registry image.

## Update policy

1. Keep the production environment file private and set `CUSTOM_IMAGE`,
   `CUSTOM_TAG`, and `PULL_POLICY=never`. Compose defaults to `never` when the
   variable is absent. Do not use a moving tag such as `latest` for a release.
2. Choose an update window. Record the current Git commit, image digest,
   Frappe/ERPNext/HRMS/CRM revisions, and database backup location.
3. Review upstream release notes and choose explicit app revisions. Update
   `apps-rundinova.json` to those approved refs; do not change it as part of an
   unattended deployment. Pin the base build images by immutable digest for a
   production build and record those digests with the release.
4. Build a uniquely tagged candidate image. Keep the previous image available
   locally or in the private registry. Never overwrite a release tag.
5. Restore a recent backup into a staging site and migrate that copy first.
   Review the desk navigation, role access, dashboards, workflows, and the
   business processes changed by the upgrade.
6. Back up production, deploy the exact tested image, and run the approved
   migration. Keep the previous image and pre-upgrade backup until acceptance.
7. Record the outcome and the new image digest in the release log.

When the deployment includes `overrides/compose.migrator.yaml`, migrations
are disabled by default. Run the one-off migration deliberately after the
pre-release backup, using the same Compose files as the live stack:

```bash
docker compose \
  --project-name rundinova \
  --env-file ~/gitops/rundinova.env \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.nginxproxy-ssl.yaml \
  -f overrides/compose.migrator.yaml \
  run --rm -e MIGRATE_SITES=true migrator
```

Use the actual proxy files for the deployment. Do not leave
`MIGRATE_SITES=true` in the normal runtime environment; migration belongs to
the deliberate release step.

Changing `apps-rundinova.json` alone does not update a running stack. A new
image must be deliberately built and selected in the private environment file.
The app list is sent to BuildKit as a secret and should not be copied into a
published image layer.

## RundiNova app-only release

For a RundiNova code correction, use the local overlay builder. It requires
the base image to already exist locally, refuses to overwrite an existing
release tag, disables Docker base pulls, and leaves the running stack alone.
It copies the current RundiNova app into the approved image without selecting
new Frappe, ERPNext, HRMS, or CRM revisions.

Run the framework-independent business-rule and release-provenance checks
before building a candidate:

```bash
PYTHONPATH=apps/rundinova_tech python3 -m unittest discover \
  -s apps/rundinova_tech/rundinova_tech/tests -p 'test_*.py'
python3 -m unittest discover -s images/rundinova/tests -p 'test_*.py'
```

```bash
bash images/rundinova/build-overlay.sh \
  rundinova/erpnext:16.37.7-rn.66-food-progress-link-core \
  16.37.7-rn.67-next-change
```

Use the exact approved local base tag or digest from the deployment record.
The second argument must be a new tag; never retag an existing release. The
builder embeds the resolved base image ID in release metadata and prints both
base and candidate image IDs for the release record. A
candidate does not become active until `CUSTOM_TAG` is deliberately changed in
the private environment file and the normal backup, staging, migration, and
acceptance steps are completed.

## GitHub Actions candidate releases

`.github/workflows/rundinova-release-candidate.yml` provides a manual candidate
build from `main`. It runs the reusable business, provenance, and Compose
checks first, then accepts only the private RundiNova GHCR package pinned by an
immutable SHA-256 digest. It refuses a reused release tag, builds only the
RundiNova overlay, smoke-checks its Desk assets and embedded metadata, and
publishes the candidate. It does not change the production environment or
deploy anything.

The GHCR package is private and currently separate from the source repository.
Before the first Actions run, open the
[package settings](https://github.com/users/JubuNiyokoDev/packages/container/package/rundinova-erpnext/settings),
choose **Manage Actions access**, add `JubuNiyokoDev/rundinova-os`, and grant
**Write** so the workflow can pull the approved base and publish candidates.
The workflow uses the short-lived `GITHUB_TOKEN`; no personal token is stored
as a repository secret. Run **RundiNova release candidate** from the Actions
tab on `main`, keep the approved base digest, and choose a new tag such as
`16.37.7-rn.78-next-change`. The job summary records the candidate digest and
source commit for staging and review.

The active local stack uses the release documented at the end of this file.
Previous release records are retained as history.

New framework-base images and app-only overlays also contain
`/home/frappe/frappe-bench/release-metadata.json`. It records installed app
versions and Git revisions when available, the requested upstream refs, the
build/runtime image references, the app-manifest hash, and a SHA-256 digest of
the RundiNova app source. The manifest contents and credentials are not copied
into the image. App-only builds update the RundiNova source digest while
preserving the upstream revision records from their base image. If that base
predates this metadata, the overlay records the base image and installed app
versions and marks the upstream revisions unavailable. Images built before
this metadata change do not contain that file. The active image contains
schema version 1 metadata, including the base image ID, application
versions, and RundiNova source digest; its upstream Git revisions are marked
unavailable.

Inspect the record in a running release with:

```bash
docker compose --project-name rundinova --env-file rundinova.env \
  -f compose.yaml -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml -f overrides/compose.noproxy.yaml \
  exec backend cat /home/frappe/frappe-bench/release-metadata.json
```

## Local candidate build

Use this only when intentionally promoting a new framework/app baseline. Set
`FRAPPE_BRANCH` to the approved immutable Frappe commit, set the build and
runtime images to approved digests, and pin each app in `apps-rundinova.json`
to its approved immutable ref before building. The values below are explicit
placeholders; do not build a release from the moving `version-16` branch tag.
The framework `Containerfile` has no branch or image defaults, so an upstream
candidate cannot silently select the current version-16 images.

```bash
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=<approved-frappe-commit> \
  --build-arg=FRAPPE_BUILD_IMAGE=frappe/build@sha256:<approved-digest> \
  --build-arg=FRAPPE_RUNTIME_IMAGE=frappe/base@sha256:<approved-digest> \
  --secret=id=apps_json,src=apps-rundinova.json \
  --tag=rundinova/erpnext:<new-unique-release-tag> \
  --file=images/rundinova/Containerfile .
```

This is the only documented path that resolves new upstream inputs. It is an
operator-run release action; the running stack does not follow upstream
changes. Keep a release record alongside deployment operations, not in
`rundinova.env`:

```text
Release tag:
Git commit:
Image digest:
Frappe / ERPNext / HRMS / CRM refs:
Base build / runtime image digests:
Backup identifier:
Migration result:
Acceptance owner and date:
Rollback image digest:
```

## Backup and recovery

Use the project’s backup schedule and retain encrypted copies outside the
Docker host. A release is not recoverable until a backup has been restored
successfully to a separate site. Include the database, private files, public
files, site configuration, and the matching image/release record. Protect
encryption keys and site secrets separately from the backup files.

The optional `overrides/compose.backup-cron.yaml` creates Frappe backups with
files and stores them in the shared `sites` volume. This protects against
application mistakes only while that Docker host and volume remain available;
it is not an off-host backup. The backup job uses the same approved RundiNova
image, so no additional scheduler image or Docker socket access is needed. Set
`BACKUP_INTERVAL_SECONDS` in the private environment file, then include the
override when starting the stack:

```bash
docker compose \
  --project-name rundinova \
  --env-file ~/gitops/rundinova.env \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.nginxproxy-ssl.yaml \
  -f overrides/compose.backup-cron.yaml \
  up -d
```

Review `docker compose logs backup` for failed cycles and monitor free disk
space: this local service does not prune old backups or copy them off-host.
Production still needs encrypted off-host retention and a restore rehearsal.

If a release fails before schema migration, select the previous image and
restart the stack. If migration has run, restore the pre-upgrade backup and
select its matching previous image; do not assume a database schema can be
downgraded by changing only the image tag.

## Operations ownership

- The RundiNova operator approves upstream revisions and production releases.
- Builds and migrations are explicit release activities, not side effects of
  routine container restarts.
- Keep app-specific changes in this repository; keep secrets, live data, and
  environment files outside Git.
- Run a staging migration and restore rehearsal before a major release.
- Track upstream changes as reviewed commits and merge them deliberately so
  the RundiNova customizations and existing business data remain under local
  control.

## Superseded candidate record — 2026-10-07

- Image: `rundinova/erpnext:16.37.7-rn.16-navigation`
- Image ID: `sha256:adb4ee978674e5da09ccbb7c24032ed7461b1784b06fe8a4c67aa517a660f6f1`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.15-navigation`
- Base image ID: `sha256:8ebbbc861aa54382811007860fc172ee8452983e8c2498a8ad62793ab6c8de0a`
- RundiNova source digest: `4d1465f0195829f3685d021cf1fe3817b44f44785eeaf484ac980ef1769fad41`
- Release type: app-only overlay; upstream application revisions were not changed.
- Verification: app unit suite, release metadata suite, workspace navigation tests,
  and `git diff --check` passed. The workspace configuration was synchronized to
  the local site and verified through Frappe's workspace API.
- Status: candidate only. The running stack remains on `rn.15`; this candidate
  has not completed staging migration, business acceptance, or restore rehearsal.

## Superseded candidate record — rn.17 — 2026-10-07

- Image: `rundinova/erpnext:16.37.7-rn.17-controller-tests`
- Image ID: `sha256:ff8f940b570fbc1814d07505b77fd59da4df9500474f23fd040020df3ceb1260`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.16-navigation`
- Base image ID: `sha256:adb4ee978674e5da09ccbb7c24032ed7461b1784b06fe8a4c67aa517a660f6f1`
- RundiNova source digest: `84dfd480872cdf35f30cd6a3f9fe075e64c6de8ea7aa935eb414fc870b3eb017`
- Release type: app-only overlay; no upstream apps or revisions were changed.
- Verification: the candidate itself installed Frappe, ERPNext, HRMS, CRM, and
  RundiNova on an isolated temporary site. All four `bench run-tests` suites
  executed and passed (9 controller tests total). The candidate's app suite
  (43 tests) and release metadata suite also passed; `git diff --check` and the
  test harness shell syntax check passed. The temporary Compose project,
  containers, and volumes were removed after the run.
- Status: candidate only. The active stack remains on `rn.15`. Staging business
  acceptance and restore rehearsal remain outstanding before promotion.

## Superseded candidate record — rn.18 — 2026-10-07

- Image: `rundinova/erpnext:16.37.7-rn.18-navigation-smoke`
- Image ID: `sha256:a5ccf182313734d99a99d0d8e0501dcb1fc7a7098a4536da6a42d5aebc325ddb`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.17-controller-tests`
- Base image ID: `sha256:ff8f940b570fbc1814d07505b77fd59da4df9500474f23fd040020df3ceb1260`
- RundiNova source digest: `3f0ca8592781c3fdd947370cadafc750e311a4d1072c483787b564effd381681`
- Release type: app-only overlay; no Frappe, ERPNext, HRMS, or CRM revision was changed.
- Verification: the candidate installed all apps on an isolated site and completed
  `bench migrate`; database-backed checks confirmed all five dashboards, the
  Finance/Projects/Tasks workspace links, sidebar entries, and separate setup
  workspace. All four controller suites passed (9 tests), workspace acceptance
  checks passed (3 tests), the standalone suite passed (43 tests), and release
  metadata checks passed (6 tests). Temporary containers and volumes were removed.
- Status: candidate only. The active stack remains on `rn.15`. Migration of a
  restored copy of the live business site, the pre-upgrade backup, and user
  acceptance remain outstanding before promotion. The restore rehearsal remains
  deferred as requested.

## Historical local release record — rn.21 — 2026-10-07

- Image: `rundinova/erpnext:16.37.7-rn.21-food-cash-link`
- Image ID: `sha256:1dcc5871eff0a800b597c6830bf2657cb0fc8145ba10936f7d1a1b0a5251dbd7`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.20-food-cash-link-tests`
- Base image ID: `sha256:e0ca52b721889efa7990a9fc6c8e9e4e8e55d7cd41b6d8cd4f6543045af49dbf`
- Release type: app-only overlay; Frappe, ERPNext, HRMS, and CRM revisions are unchanged.
- Verification: candidate migration completed on an isolated site. The three
  cash movement controller tests and three workspace navigation acceptance
  tests passed there. The current host suite passed (51 tests), including
  workspace layout and release metadata checks; `git diff --check` passed.
- Navigation provisioned in this candidate: all five RundiNova dashboards at
  the top of **RundiNova Tech**, Projects and Tasks, Finance and food purchase
  links, matching sidebar destinations, and a separate setup workspace. The
  Desk launcher hides unrelated ERPNext module icons while retaining installed
  DocTypes.
- Deployment: active local self-hosted stack now runs `rn.21`; all application
  containers were recreated from this image. MariaDB and Redis remained on
  their existing images and volumes.
- Data protection: immediately before migration, `bench backup --with-files`
  created database and public/private file backups dated `20261007_162429` in
  the site's private backup directory. The database gzip and both tar archives
  passed integrity/listing checks. No restore rehearsal or off-machine backup
  was performed, as deferred by the operator.
- Runtime verification: `bench migrate` completed successfully; the live
  database contains all five dashboard links, Finance, Projects and Tasks in
  both RundiNova Tech and its sidebar, and the separate setup workspace. Joffre
  defaults to RundiNova Tech. The launcher now exposes RundiNova Tech, Team,
  Setup and Frappe CRM; standard module icons are hidden. `/api/method/ping`
  returned HTTP 200 and `/app/rundinova-tech` redirected to `/desk/rundinova-tech`.
- Permission check: with a temporary assignment inside a rolled-back
  transaction, Housekeeping could see that budget and create a food expense,
  but still could not read cash movements. The temporary assignment was
  verified absent after rollback.
- Business data snapshot (2026-10-07): one food budget exists, for January
  2026, in Draft; three food expenses are Submitted. There are no RundiNova
  cash accounts or cash movements, and no Projects, Tasks, or GitHub
  repositories. The purchase-to-cash and project delivery workflows therefore
  still need operator-provided business data and have not been accepted
  end-to-end. Team Members only see budgets assigned to them; the current
  budget has no assignments.
- Status: superseded by rn.25. Visual acceptance in Joffre's browser remains
  for the operator to confirm; this record does not claim that user-session
  page rendering was captured automatically.

## Superseded local release record — rn.25 — 2026-10-07

- Image: `rundinova/erpnext:16.37.7-rn.25-navigation-assets`
- Image ID: `sha256:ceb9918eb1fcd9c067cecaaaadd7a46ef5a1acfb20e625663d47bbadbdb89dd6`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.24-navigation-sidebar`
- Release type: app-only overlay; Frappe, ERPNext, HRMS, and CRM revisions are unchanged.
- Change: include app public assets in the built image and load a small Desk
  route compatibility script so `/desk/rundinova-tech` selects the matching
  RundiNova sidebar. The workspace presents five dashboards, daily links for
  food, finance, projects and tasks, with setup in a separate administration
  section and a direct sidebar link.
- Verification: isolated Frappe installation, migration and all four
  controller suites passed, including three workspace navigation checks. The
  image build asserts that the JS and logo assets exist. On the active stack,
  `bench migrate` and `clear-cache` completed; the JS URL returns HTTP 200,
  `/api/method/ping` returns `pong`, and the database confirms all five
  dashboard links, Projects, Tasks, food operations, Setup and Joffre's default
  workspace.
- Data protection: backup `20261007_181002` includes database, public/private
  files and site configuration; gzip and tar integrity checks passed.
- Deployment: active on the local `rundinova` Compose stack. Services use rn.25;
  database and Redis images and volumes are unchanged.
- Limitation: no automated browser session was available to capture the final
  signed-in page. The operator should log out/in or hard-refresh once to confirm
  the visual sidebar and home page in Joffre's browser.

## Superseded local release record — rn.28 — 2026-10-07

- Image: `rundinova/erpnext:16.37.7-rn.28-navigation-ux`
- Image ID: `sha256:0795afce304582a4f0d8e82b65b1a3763a906ed4d17c799ca39e43c0f30ec96a`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.25-navigation-assets`
- Base image ID: `sha256:ceb9918eb1fcd9c067cecaaaadd7a46ef5a1acfb20e625663d47bbadbdb89dd6`
- RundiNova source digest: `d286640873d8df2a0d887f8f5280e3bfbfee2e364ab4401d0b782db39ee5f594`
- Release type: app-only overlay; Frappe, ERPNext, HRMS, and CRM revisions are unchanged.
- Change: launcher labels and routes for Setup and Team now resolve to ASCII workspace
  titles, the launcher tiles are visually distinct, app title/logo/favicon are
  branded, business links show human titles, and custom list views hide opaque IDs.
  Food Progress records now show item and budget names. Each progress form has a
  short “Enregistrer un achat” flow that records quantity, amount, date and payment
  as a submitted food purchase and refreshes the budget/progress totals.
- Verification: isolated fresh installation and migration passed. The Frappe
  controller suites passed (12 tests) and workspace acceptance tests passed
  (5 tests). Active site migration completed. `/api/method/ping`, the three Desk
  routes, logo, favicon and sidebar asset returned HTTP 200. The route probes
  redirected to login because no browser session was attached; signed-in visual
  acceptance remains with the operator.
- Data protection: `bench backup --with-files` completed at `20261007_194358`
  before migration; it includes database, public/private files and site config.
  No restore rehearsal or off-machine encrypted copy was performed, as deferred.
- Deployment: active on the local self-hosted Compose stack; `rundinova.env` pins
  `CUSTOM_TAG=16.37.7-rn.28-navigation-ux`. Database and Redis images/volumes were
  not changed.

## Superseded local release record — rn.29 — 2026-10-07

- Image: `rundinova/erpnext:16.37.7-rn.29-navigation-ux`
- Image ID: `sha256:edfd58e602619f1e9716970681923f0e2305fb11487223ac11ff7f1fdfa7af90`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.28-navigation-ux`
- Base image ID: `sha256:0795afce304582a4f0d8e82b65b1a3763a906ed4d17c799ca39e43c0f30ec96a`
- RundiNova source digest: `88ec7fc753d0431ccbace05e1121fb17b2772289fe7ed816cabb19973b9cce88`
- Release type: app-only overlay; Frappe, ERPNext, HRMS, and CRM revisions are unchanged.
- Change: hide internal document keys from detail sidebars, use a 298-byte SVG
  favicon, and keep the short purchase action focused on fields team members can
  fill without supplier-master permissions.
- Verification: isolated installation and migration passed; 12 controller tests
  and 6 workspace/branding tests passed. The active migration completed. Ping,
  the three Desk routes, SVG favicon, CSS, purchase JS and list-view JS returned
  HTTP 200. Routes correctly send signed-out requests to login. The rendered
  authenticated page and purchase submission still need the operator's browser
  confirmation; this run did not claim a browser-session test.
- Data protection: `bench backup --with-files` completed at `20261007_201100`
  immediately before migration; it includes database, public/private files and
  site configuration. Restore rehearsal and off-host encrypted retention remain
  deferred, as requested.
- Deployment at this release: local self-hosted Compose stack; `rundinova.env` pinned
  `CUSTOM_TAG=16.37.7-rn.29-navigation-ux`. Database and Redis images/volumes
  were not changed.

## Historical local release record — rn.30 — 2026-10-07

- Image: `rundinova/erpnext:16.37.7-rn.30-navigation-branding`
- Image ID: `sha256:5cf46da0d5bc35302dd8a4f983fcebd56b82be03511f3b65e39ce6238e4c721c`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.29-navigation-ux`
- Base image ID: `sha256:edfd58e602619f1e9716970681923f0e2305fb11487223ac11ff7f1fdfa7af90`
- RundiNova source digest: `08fac1409228e60060e665a78953ac9df6a34fc3b0b8a0dfe4a91c47095010b3`
- Release type: app-only overlay; no Frappe, ERPNext, HRMS or CRM update was selected.
- Change: the login browser title now uses `RundiNova Tech · Connexion` while the
  website metadata, logo and compact SVG favicon stay RundiNova branded.
- Verification: isolated fresh installation and migration passed; 12 controller
  tests and 6 workspace/branding tests passed. The active migration completed,
  followed by a healthy backend restart. Chromium rendered `/login` and the final
  document title was `RundiNova Tech · Connexion`; it loaded the RundiNova SVG
  favicon. `/api/method/ping`, the Team/Setup/Tech Desk routes and custom CSS/JS
  assets returned HTTP 200. Signed-out Desk routes correctly redirect to login.
- Data protection: `bench backup --with-files` completed at `20261007_202750`
  before migration and includes the database, public/private files and site
  configuration. No restore rehearsal or encrypted off-host copy was performed,
  as deferred by the operator.
- Deployment: active local self-hosted Compose stack; `rundinova.env` pins
  `CUSTOM_TAG=16.37.7-rn.30-navigation-branding`. MariaDB and Redis images and
  volumes were not changed.

## Historical local release record — rn.34 — 2026-10-07

- Image: `rundinova/erpnext:16.37.7-rn.34-dashboard-ux`
- Image ID: `sha256:b7fb925d730ce8694644d4160e7c0c63ab321489080f6bde2a282760e7dc8214`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.30-navigation-branding`
- Base image ID: `sha256:5cf46da0d5bc35302dd8a4f983fcebd56b82be03511f3b65e39ce6238e4c721c`
- RundiNova source digest: `25bdf2dd3cc8eea97e55ffddb5e30f71b033e1a564346d6328c947d747a3b6a8`
- Release type: app-only overlay; no Frappe, ERPNext, HRMS or CRM update was selected.
- Change: refocused the executive dashboard on company health, reduced Finance
  from 16 charts/8 cards to 9/6 and Delivery from 10/10 to 6/5, corrected
  category-based sum/average charts, and set monetary cards/charts to BIF.
- Verification: on candidate `.33`, the isolated fresh-install migration passed,
  along with 2 document-controller tests and all 10 workspace/dashboard tests.
  A `.33` migration against the existing database exposed Frappe's immutable
  chart-type guard; that candidate was not retained. The provisioning code now
  updates that app-owned configuration field explicitly. The `.34` migration
  completed against the existing site, the backend reports healthy, and all
  application services are running. Read-only checks confirmed dashboard
  layouts (Executive 7/6, Finance 9/6, People 6/4, Delivery 6/5, Ecosystem 6/3),
  BIF currency, and food-progress values for Pain, Viande and Riz. The ping
  endpoint returned HTTP 200; signed-out Desk routes redirect to login. No
  authenticated browser session was available for a visual acceptance check.
- Data protection: `bench backup --with-files` completed at `20261007_214839`
  before the final migration and includes database, public/private files and
  site configuration. Restore rehearsal and encrypted off-host copy remain
  deferred, as requested.
- Deployment: active local self-hosted Compose stack; `rundinova.env` pins
  `CUSTOM_TAG=16.37.7-rn.34-dashboard-ux`. MariaDB and Redis images and volumes
  were not changed.

## Historical local release record — rn.39 — 2026-10-08

- Image: `rundinova/erpnext:16.37.7-rn.39-desk-home`
- Image ID: `sha256:671e7ce8c03dfea6a54699d5b1de5f3b813b78edf1da33214c0dc4c252b6215f`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.38-desk-home`
- Base image ID: `sha256:b74e16351f8494215a9960595786b84b7ccda7108aec60a52a46a01e92417d76`
- RundiNova source digest: `61153fb4034c70d57fd3ddeaf2692920af7e1572f857b8170763e885c333b6b6`
- Release type: app-only overlay; no Frappe, ERPNext, HRMS or CRM update was selected.
- Change: add the RundiNova Desk home route and load its redirect through
  Frappe's `page_js` hook, sending each user to their assigned workspace.
- Verification: the isolated `.39` install/migrate passed 2 document-controller
  tests and all 11 workspace/dashboard tests, including verification that
  `desk_page.get()` returns the actual redirect script. The live migration
  completed; backend and database are healthy and all application services are
  running. On the live site, `add_home_page()` returned `rundinova-home` for
  both Joffre and housekeeping; their assigned workspaces were respectively
  `RundiNova Tech` and `RundiNova Team`, and Frappe returned the redirect script
  for both users. `/api/method/ping` and the built home JS asset returned HTTP 200. An authenticated browser-session visual test was not performed.
- Data protection: `bench backup --with-files` completed at `20261008_074240`
  before migration and includes the database, public/private files and site
  configuration. Restore rehearsal and encrypted off-host copy remain deferred,
  as requested.
- Deployment: active local self-hosted Compose stack; `rundinova.env` pins
  `CUSTOM_TAG=16.37.7-rn.39-desk-home`. MariaDB and Redis images/volumes were
  not changed.

## Historical local release record — rn.45 — 2026-10-08

- Image: `rundinova/erpnext:16.37.7-rn.45-detail-forms`
- Image ID: `sha256:b4d8ae66c9d171cfc91e03536312c1e09810cde8c0af7637b9cee48733c3e367`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.44-navigation-trim`
- Base image ID: `sha256:4f7ac1dcd040e028d9248e6071bcc0ac81905d5a0968913b8b1371aa7face755`
- RundiNova source digest: `93263abecc3bd08772f981a6ef567b4cf6daaa265fb8c3e00408aa9f87f0a9fc`
- Release type: app-only overlay; Frappe, ERPNext, HRMS and CRM versions were
  unchanged.
- Change: add durable French section groupings and readable field labels to 15
  RundiNova business forms, preserving their fieldnames and workflow values.
  This builds on the prior navigation aliases, one primary Tech workspace,
  branded logo/favicon/title, human-readable record links, dashboard layout,
  and server-validated quick food-purchase flow.
- Verification: candidate fresh-install migration passed, along with 2 document
  controller tests and all 15 workspace, navigation, dashboard, branding and
  form metadata tests. Live migration completed successfully. Backend and
  database are healthy; all app services are running from `.45`. The ping,
  branding JS and RundiNova favicon returned HTTP 200. No authenticated browser
  session visual acceptance test was performed.
- Data protection: `bench backup --with-files` completed at `20261008_082941`
  before migration; database gzip, public/private files archives and site
  configuration integrity checks passed. Restore rehearsal and encrypted
  off-host retention remain deferred, as requested.
- Deployment: active local self-hosted Compose stack; `rundinova.env` pins
  `CUSTOM_TAG=16.37.7-rn.45-detail-forms`. MariaDB and Redis images and volumes
  were not changed.

## Historical local release record — rn.47 — 2026-10-08

- Image: `rundinova/erpnext:16.37.7-rn.47-clean-overlay`
- Image ID: `sha256:bbd2433dabbeabf427a45304c2e1fe8d6dca889f27fa1c1fb1679effc5ac3201`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.46-core-package`
- Base image ID: `sha256:ccb5fc65a0cd8a7974130c2b09da32a81b0dcb58c54f371680c8fa74f0c60609`
- RundiNova source digest: `dc40e2f3345f075f056e9bbfcbcfd66c50abc23647e7df8bd2368e7375bd6860`
- Release type: app-only overlay; Frappe, ERPNext, HRMS and CRM versions were
  unchanged.
- Change: make the overlay replace the complete RundiNova app directory so
  deleted source and test files from older images do not remain visible in the
  final filesystem. The app's pure business rules are packaged as
  `rundinova-core`, independently installable and testable without Frappe,
  while existing Frappe imports remain compatible.
- Verification: fresh isolated install and migration passed; 30 core tests, 12
  controller tests, and 15 navigation/dashboard/form tests passed. The image
  check confirmed that five moved domain test files are absent from the old
  location. On the active image, the backend and database are healthy, 30 core
  tests and 16 app/compatibility tests pass, and only the three current tests
  remain in the app test folder. `/api/method/ping`, branding JS and favicon
  return HTTP 200.
- Data protection: `bench backup --with-files` completed at `20261008_091545`
  before migration; the database gzip, public/private file archives and site
  configuration passed integrity checks. Restore rehearsal and encrypted
  off-host retention remain deferred, as requested.
- Deployment: active local self-hosted Compose stack; `rundinova.env` pins
  `CUSTOM_TAG=16.37.7-rn.47-clean-overlay`. MariaDB and Redis images and
  volumes were not changed.

## Historical local release record — rn.48 — 2026-10-08

- Image: `rundinova/erpnext:16.37.7-rn.48-workspace-purchase-ux`
- Image ID: `sha256:81013381bd40efba60e5e424db38d395f1c1df772c8ad8c6bf4820a8971a3240`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.47-clean-overlay`
- Base image ID: `sha256:bbd2433dabbeabf427a45304c2e1fe8d6dca889f27fa1c1fb1679effc5ac3201`
- RundiNova source digest: `f2e4fca8ccf078150de239ca4bc18611939a973cdc34552bf28649092a1647df`
- Release type: app-only overlay; Frappe, ERPNext, HRMS and CRM were unchanged.
- Change: extract food-purchase orchestration into framework-independent
  `rundinova-core` behind a permission-aware Frappe adapter; add a purchase
  chooser to the expense list; restore the workspace sidebar on dashboard
  views; send `/desk` to the assigned workspace; and refresh historical food
  progress/expense titles during migration.
- Verification: fresh isolated installation and migration passed; 35 core
  tests, 12 controller tests, and 16 workspace/dashboard tests passed. The
  active site was backed up at `20261008_093230`; database gzip, public/private
  file archives, and site configuration passed integrity checks. Ping, logo,
  favicon, branding script and the setup asset returned HTTP 200.
- Deployment: was active briefly on the local self-hosted stack, then superseded
  by `.50` after the next navigation acceptance exposed duplicate workspaces.

## Historical local release record — rn.50 — 2026-10-08

- Image: `rundinova/erpnext:16.37.7-rn.50-single-entry`
- Image ID: `sha256:b9a7bfb3c1ed6882fe5bad4fa2c7783ab28d46d87efc0aeba7781dab2d861a5e`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.48-workspace-purchase-ux`
- Base image ID: `sha256:81013381bd40efba60e5e424db38d395f1c1df772c8ad8c6bf4820a8971a3240`
- RundiNova source digest: `07af5b945a086e5ebf3ba0f14be3451ec1db21601e1ef0ebe2bb453d324c3bbd`
- Release type: app-only overlay; Frappe, ERPNext, HRMS and CRM were unchanged.
- Change: use one visible RundiNova Tech workspace for all RundiNova roles,
  provide a separate setup Page at `/desk/rundinova-setup`, redirect old team
  aliases to the canonical home, keep the persistent sidebar on dashboards,
  and offer a short food-purchase dialog from the list or item progress.
- Verification: candidate install and migration passed; 35 core tests, 12
  controller tests, and 17 workspace/navigation/dashboard tests passed. On the
  active site, Joffre's workspace list now contains only `RundiNova Tech`; the
  setup Page exists, and old routes now reach login rather than returning a
  missing-Page response. Existing progress and purchase records display
  readable item/budget/date titles. Ping, logo, favicon, branding script and
  setup-page JavaScript returned HTTP 200. An authenticated browser session was
  not available for visual acceptance.
- Data protection: backup completed at `20261008_094605` before migration;
  database gzip, both file archives, and site configuration passed integrity
  checks. No business data was deleted or replaced.
- Deployment: active local self-hosted Compose stack; `rundinova.env` pins
  `CUSTOM_TAG=16.37.7-rn.50-single-entry`. Database and Redis images/volumes
  were not changed. Superseded by `.54` after the food-invoice bridge was
  extracted behind the independent application layer.

## Historical local release record — rn.54 — 2026-10-08

- Image: `rundinova/erpnext:16.37.7-rn.54-food-invoice-core`
- Image ID: `sha256:eb7dee361b2bfc8ce9ccb4bb6966ed14328301eacaac3f20911ff197457f0690`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.50-single-entry`
- Base image ID: `sha256:b9a7bfb3c1ed6882fe5bad4fa2c7783ab28d46d87efc0aeba7781dab2d861a5e`
- RundiNova source digest: `3d5d03b35b1fba4996f2e64d8ed7d1cb439ff3514f87c5bd433fa452ce29834e`
- Release type: app-only overlay; Frappe, ERPNext, HRMS and CRM revisions were
  not changed.
- Change: move Purchase Invoice to food-expense synchronization and cancellation
  into framework-independent `rundinova-core` use cases, with a Frappe
  persistence adapter preserving existing hooks and controlled permission
  bypasses. The `.50` navigation, dashboard, branding, readable labels, and
  quick food-purchase UX are retained.
- Verification: candidate fresh install/migration passed; 39 core tests, 14
  controller tests, and 18 workspace/navigation/dashboard tests passed. The
  active Frappe migration completed successfully; backend and database were
  healthy. Superseded by `.56` to add multi-item market purchases.
- Data protection: `bench backup --with-files` completed at `20261008_101654`;
  database gzip, public/private file archives, and site configuration passed
  integrity checks. No business data was deleted or replaced. Restore rehearsal
  and encrypted off-host retention remain deferred as requested.
- Deployment: active briefly on the local self-hosted stack;
  `rundinova.env` then advanced to `.56`. Database and Redis images/volumes were
  not changed. Authenticated browser visual acceptance was not performed.

## Historical local release record — rn.56 — 2026-10-08

- Image: `rundinova/erpnext:16.37.7-rn.56-market-basket`
- Image ID: `sha256:99442707db7539d280504eb27f387fbb5cbbe5f4168890005c263ae21899bf4b`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.54-food-invoice-core`
- Base image ID: `sha256:eb7dee361b2bfc8ce9ccb4bb6966ed14328301eacaac3f20911ff197457f0690`
- RundiNova source digest: `ff0964414af41fdeda52ca5480600154f12bf2bb2ba29d52cf99b0a5ffb7582c`
- Release type: app-only overlay; Frappe, ERPNext, HRMS and CRM revisions were
  not changed.
- Change: let a buyer record several food items from one market visit in one
  dialog, with per-item quantity and total and shared date, payment method,
  receipt and notes. Each line uses the existing server-validated budget and
  progress workflow; progress-specific purchase actions remain one-item.
- Verification: candidate fresh install/migration passed; 41 core tests, 14
  controller tests, and 18 workspace/navigation/dashboard tests passed. The
  active migration completed successfully. Ping and the purchase script,
  RundiNova logo and favicon returned HTTP 200; workspace destinations redirect
  to login rather than returning missing-page responses. Backend and database
  are healthy; all app services are running on `.56`. Authenticated browser
  visual and end-to-end purchase acceptance were not performed.
- Data protection: `bench backup --with-files` completed at `20261008_103022`;
  database gzip, public/private file archives, and site configuration passed
  integrity checks. No business data was deleted or replaced. Restore rehearsal
  and encrypted off-host retention remain deferred as requested.
- Deployment: active local self-hosted Compose stack until `.58`; database and
  Redis images/volumes were not changed.

## Historical local release record — rn.58 — 2026-10-08

- Image: `rundinova/erpnext:16.37.7-rn.58-food-progress-core`
- Image ID: `sha256:e3f7aff401c55b53bab497950e14e4aead4e41eb2dd3c15df4569ce9d5aaf7d6`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.56-market-basket`
- Base image ID: `sha256:99442707db7539d280504eb27f387fbb5cbbe5f4168890005c263ae21899bf4b`
- RundiNova source digest: `2a9adaec7a1bd167bc3a916afd256a05be56afb671671bba4a1bee491a013a0b`
- Release type: app-only overlay; Frappe, ERPNext, HRMS and CRM revisions were
  not changed.
- Change: move food-item progress aggregation into framework-independent
  `rundinova-core`; Frappe now loads the budget line, expense snapshots and
  dates, then applies the returned calculations to the DocType. Existing field
  values, status names, active expense statuses and persisted records remain
  compatible.
- Verification: candidate fresh install/migration passed; 44 core tests, 18
  controller tests and 19 workspace/navigation/dashboard tests passed. Active
  migration completed; backend and database are healthy, and all Compose app
  services are running. Ping and the food-purchase JS return HTTP 200; workspace
  routes redirect to login instead of missing-page responses. No authenticated
  browser visual acceptance was performed.
- Data protection: `bench backup --with-files` completed at `20261008_105038`;
  database gzip, public/private file archives and site configuration passed
  integrity checks. No business data was deleted or replaced. Restore rehearsal
  and encrypted off-host retention remain deferred as requested.
- Deployment: active local self-hosted Compose stack until `.60`; database and
  Redis images/volumes were not changed.

## Historical local release record — rn.60 — 2026-10-08

- Image: `rundinova/erpnext:16.37.7-rn.60-food-expense-core`
- Image ID: `sha256:47170acd3475e3ae60fa66f6656a88358a84067864d173da54d5dd6ca5bb8846`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.58-food-progress-core`
- Base image ID: `sha256:e3f7aff401c55b53bab497950e14e4aead4e41eb2dd3c15df4569ce9d5aaf7d6`
- RundiNova source digest: `44b7f5d347a08cc45ebc26a65a2e832545ca01c53811ddbb6d0bb18459cf5675`
- Release type: app-only overlay; Frappe, ERPNext, HRMS and CRM revisions were
  not changed.
- Change: move food-expense policy orchestration into framework-independent
  `rundinova-core`. The Frappe adapter provides budget periods and committed
  totals from SQL, and role context; core applies period, per-item, justification
  and approved-ceiling rules in their existing order. Non-active expenses still
  skip aggregate queries. Existing DocTypes, statuses and records are unchanged.
- Verification: candidate fresh install/migration passed; 49 core tests, 20
  controller tests and 20 workspace/navigation/dashboard tests passed. Active
  migration completed; backend and database are healthy, and every Compose app
  service is running. Ping, food-purchase JS and favicon return HTTP 200; the
  workspace route redirects to login instead of a missing-page response. No
  authenticated browser visual acceptance was performed.
- Data protection: `bench backup --with-files` completed at `20261008_111608`;
  database gzip, public/private file archives and site configuration passed
  integrity checks. No business data was deleted or replaced. Restore rehearsal
  and encrypted off-host retention remain deferred as requested.
- Deployment: active local self-hosted Compose stack until `.64`; database and
  Redis images/volumes were not changed.

## Historical local release record — rn.64 — 2026-10-08

- Image: `rundinova/erpnext:16.37.7-rn.64-cash-link-policy-core`
- Image ID: `sha256:39ebaa3210d87ac43f1f58c1b3b285cbdfa0e4ffe267372f3f03c3456b81d3ec`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.60-food-expense-core`
- Base image ID: `sha256:47170acd3475e3ae60fa66f6656a88358a84067864d173da54d5dd6ca5bb8846`
- RundiNova source digest: `9003a44e892aaae7042c56e1c0a1a9df93ce430af45185fc7d7e44cebd7d1186`
- Release type: app-only overlay; Frappe, ERPNext, HRMS and CRM revisions were
  not changed.
- Change: move the rule that protects cash-linked food purchases into
  `rundinova-core`. The Frappe controller still looks up an active cash movement
  and adapts the saved/current expense fields; core decides whether a protected
  edit or deletion requires cancellation first. The existing hook function,
  protected fields, user-facing errors, DocTypes and records are preserved.
- Verification: candidate fresh install/migration passed; 51 core tests, 22
  controller tests and 21 workspace/navigation/dashboard tests passed. Active
  migration completed; backend and database are healthy and all Compose
  services run. Ping, purchase JavaScript and favicon return HTTP 200; the
  workspace route redirects to login instead of a missing-page response. No
  authenticated browser visual acceptance was performed.
- Data protection: `bench backup --with-files` completed at `20261008_192827`;
  database gzip, public/private file archives and site configuration passed
  integrity checks. No business data was deleted or replaced. Restore rehearsal
  and encrypted off-host retention remain deferred as requested.
- Deployment: active local self-hosted Compose stack; `rundinova.env` pins
  `CUSTOM_TAG=16.37.7-rn.64-cash-link-policy-core` until `.65`. Database and
  Redis images/volumes were not changed.

## Historical local release record — rn.65 — 2026-10-08

- Image: `rundinova/erpnext:16.37.7-rn.65-desk-purchase-ux`
- Image ID: `sha256:69a1e3a655b4ca297c7d37f67dbd3f468a9d848428f4c0315eea5a878d9c5525`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.64-cash-link-policy-core`
- Base image ID: `sha256:39ebaa3210d87ac43f1f58c1b3b285cbdfa0e4ffe267372f3f03c3456b81d3ec`
- RundiNova source digest: `b9a994efa36e1d6ecd362e798ab951539e3583836b8508e0fae34acd70aa1596`
- Release type: app-only overlay; Frappe, ERPNext, HRMS and CRM revisions were
  not changed.
- Change: legacy Setup and Team routes now redirect at the browser route boundary;
  obsolete Setup, Team, Finance and Dashboards launcher tiles are hidden so the
  launcher has one RundiNova destination. Budget, Food Progress and Food Expense
  explicitly use human-readable titles. Food Progress budget/item references are
  read-only derived values. The Item list now offers “Acheter”: select an item,
  choose its food budget, enter quantity and total, then record the purchase
  through the existing server-validated expense workflow.
- Verification: fresh candidate install/migration passed; 51 core tests, 22
  controller tests and 21 workspace/navigation/dashboard tests passed. The active
  migration completed. Database inspection confirms only `RundiNova Tech` and
  `Frappe CRM` are visible workspaces; legacy RundiNova tiles are hidden and the
  three food DocTypes use their human title fields. Ping, workspace route, food
  purchase JavaScript, logo and favicon returned HTTP 200 (the workspace route
  redirects to login without a browser session). No authenticated browser visual
  or live market-purchase acceptance was performed.
- Data protection: `bench backup --with-files` completed at `20261008_201302`;
  database gzip, site configuration JSON, public and private file archives passed
  integrity checks. No business data was deleted or replaced. Restore rehearsal
  and encrypted off-host retention remain deferred as requested.
- Deployment: active local self-hosted Compose stack; `rundinova.env` pins
  `CUSTOM_TAG=16.37.7-rn.65-desk-purchase-ux` until `.66`. Database and Redis
  images/volumes were not changed. Rollback images `.64` and `.65` remain local.

## Active local release record — rn.66 — 2026-10-08

- Image: `rundinova/erpnext:16.37.7-rn.66-food-progress-link-core`
- Image ID: `sha256:8acdbc2f9a8315c6d95b93fc8d3e59894e5b22143252a8094dc773e60c2d8d56`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.65-desk-purchase-ux`
- Base image ID: `sha256:69a1e3a655b4ca297c7d37f67dbd3f468a9d848428f4c0315eea5a878d9c5525`
- RundiNova source digest: `0b2477e3a91740c8b5341f7679fa1c9989fd7744b9b95905660d8611b365ae08`
- Release type: app-only overlay; Frappe, ERPNext, HRMS and CRM revisions were
  not changed.
- Change: move the expense-to-food-progress association decision into
  `rundinova-core`. Core preserves an explicitly linked progress record, looks
  up the existing budget/item match, or requests creation through a narrow
  adapter. The adapter retains the prior Frappe query and controlled insert
  behavior. No DocTypes, fields, statuses, or persisted records changed.
- Verification: fresh candidate installation and migration passed; 55 core
  tests, 25 controller tests, and 22 workspace/navigation/dashboard tests passed.
  Active migration completed and all Compose services are running, with backend
  and database healthy. Ping, workspace route, purchase JavaScript, logo, and
  favicon returned HTTP 200 (workspace redirects to login without a session).
- Data protection: `bench backup --with-files` completed at `20261008_210955`;
  database gzip, site configuration JSON, and public/private file archives
  passed integrity checks. No business data was deleted or replaced. Restore
  rehearsal and encrypted off-host retention remain deferred as requested.
- Deployment: active local self-hosted Compose stack; `rundinova.env` pins
  `CUSTOM_TAG=16.37.7-rn.66-food-progress-link-core`. Database and Redis images
  and volumes were not changed. Rollback images `.64` and `.65` remain local.

## Active local release record — rn.67 — 2026-10-08

- Image: `rundinova/erpnext:16.37.7-rn.67-navigation-purchase-ux`
- Image ID: `sha256:c905ea181e8f3851901996692790d6c72545bdafd4c73b368b5b9fff539aff56`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.66-food-progress-link-core`
- Base image ID: `sha256:8acdbc2f9a8315c6d95b93fc8d3e59894e5b22143252a8094dc773e60c2d8d56`
- RundiNova source digest: `3939f0bfc60a530fac444ad0d3d666370802239425db9bd36f6dc153b00ca001`
- Release type: app-only overlay; Frappe, ERPNext, HRMS and CRM revisions were
  not changed.
- Change: legacy Setup and Team Page routes now load their redirect script
  directly. The food-purchase dialog is loaded from both the food-expense form
  and list, offers a multi-item market purchase, and is available from each
  Item row. Food expense technical identifiers are hidden in its list; custom
  DocType links use their human title fields. Existing global RundiNova logo,
  favicon and tab-title branding remain included.
- Verification: 16 app-level and 9 release tests passed; all 21 custom DocType
  JSON files parsed and `git diff --check` passed. Live migration exited 0.
  Database checks confirm legacy Pages have their redirect hooks, only the
  RundiNova Tech launcher icon is visible, and the Food Budget, Food Progress
  and Food Expense links use human titles. The purchase JavaScript and favicon
  return HTTP 200, and all application containers are running with a healthy
  backend. No authenticated browser session was available for visual or
  market-purchase acceptance.
- Data protection: `bench backup --with-files` completed at `20261008_212532`;
  database, site config, public and private files were included. No business
  data was removed or replaced. Restore rehearsal and encrypted off-host
  retention remain deferred as requested.
- Deployment: active local self-hosted Compose stack; `rundinova.env` pins
  `CUSTOM_TAG=16.37.7-rn.67-navigation-purchase-ux`. Database and Redis images
  and volumes were not changed. Rollback image `.66` remains local.

## Historical local release record — rn.68 — 2026-10-09

- Image: `rundinova/erpnext:16.37.7-rn.68-brand-fbu-crm`
- Image ID: `sha256:31ac3f4bcf8839abb1604276e572a7c413aac32fc2a89eaa528bd2e571a076cc`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.67-navigation-purchase-ux`
- RundiNova source digest: `5f196498998e14b1b17cdfe6c4aa3f7186df510d1a66fd58e26cdf49d9b5ba6f`
- Release type: app-only overlay; Frappe, ERPNext, HRMS and CRM revisions were
  not changed.
- Change: correct the missing food-progress import; persist `FBu` on the BIF
  currency record; grant read-only HR Settings access to RundiNova Director and
  People & Culture; use the existing RundiNova logo source with a wide crop and
  the existing brand PNG favicon; add CRM, growth opportunities, partnerships
  and community impact to the operational workspace.
- Verification: app and release checks passed; the active migration completed.
  Food purchase and workspace Frappe test modules exited successfully. Live
  checks confirmed `FBu`, Joffre's HR Settings read access, the logo/favicon
  settings, ping, and both brand assets (HTTP 200). The `.68` image was active
  briefly before the CRM role follow-up in `.69`.
- Data protection: `bench backup --with-files` completed at `20261009_081610`;
  database, site configuration, public and private files were included.
- Deployment: local self-hosted Compose stack; the release was superseded by
  `.69`. The `.67` image remains available for rollback.

## Active local release record — rn.69 — 2026-10-09

- Image: `rundinova/erpnext:16.37.7-rn.69-crm-access`
- Image ID: `sha256:826a91e3f62b2f43adb9c3b1d14a3e816e155d68ff1a8e871ec3e65318d3d616`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.68-brand-fbu-crm`
- Base image ID: `sha256:31ac3f4bcf8839abb1604276e572a7c413aac32fc2a89eaa528bd2e571a076cc`
- RundiNova source digest: `5308f525a93e863eab72095093ac9e15c74553d5649e26fa6b53d477d5d0ae65`
- Release type: app-only overlay; Frappe, ERPNext, HRMS and CRM revisions were
  not changed.
- Change: grant RundiNova Director and Communications roles create/read/update
  access to operational CRM records; Operations and Project Lead receive
  read-only access. CRM configuration records remain outside the RundiNova
  grants.
- Verification: app and release suites and `git diff --check` passed. Food
  expense and workspace Frappe test modules exited successfully on the active
  site. Live permission checks confirmed Joffre can create CRM leads, Elvis can
  create CRM leads, and Elvis cannot read FCRM Settings. BIF displays `FBu`;
  ping and the logo/favicon assets return HTTP 200. Backend and database are
  healthy. An authenticated browser session was not available for visual CRM or
  purchase acceptance.
- Data protection: `bench backup --with-files` completed at `20261009_082409`;
  database, site configuration, public and private files were included. No
  business records were deleted or replaced. Encrypted off-machine retention
  and restore rehearsal remain deferred as requested.
- Deployment: active local self-hosted Compose stack; `rundinova.env` pins
  `CUSTOM_TAG=16.37.7-rn.69-crm-access`. Database and Redis images and volumes
  were not changed. Rollback images `.67` and `.68` remain local.

## Superseded candidate — rn.70 — 2026-10-09

- Image: `rundinova/erpnext:16.37.7-rn.70-profile-crm-purchase`
- Image ID: `sha256:1ef775dd061195a7e90f67060b84a7ee4450cf094f5cb4fa9875ac7851beb1f4`
- This image was not activated. Its migration stopped in an `after_migrate`
  hook because CRM role assignment saved users before recreating their default
  workspace. No application containers were restarted. The ordering was fixed
  in `.71`; the failed attempt and the later successful attempt each have a
  complete local `backup --with-files` copy (`20261009_084704` and
  `20261009_085049`).

## Active local release record — rn.71 — 2026-10-09

- Image: `rundinova/erpnext:16.37.7-rn.71-crm-bootstrap-order`
- Image ID: `sha256:840aecaf5bd33a324f952f11671e97e820ba63e5b64210e216fe2ddd0cef91b6`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.70-profile-crm-purchase`
- Base image ID: `sha256:1ef775dd061195a7e90f67060b84a7ee4450cf094f5cb4fa9875ac7851beb1f4`
- RundiNova source digest: `24843eb00e6076ba5d1e2f5f45a8bd5f38e45a3050ab2614ba9ad025b13268d7`
- Release type: app-only overlay; Frappe, ERPNext, HRMS and CRM revisions were
  not changed.
- Change: use the supported `frappe.get_roles` API during food expense
  validation; grant the built-in CRM entry role only to RundiNova Directors and
  Communications users after workspace synchronization; use a cache-distinct
  favicon derived from the actual RundiNova logo. The user profile continues to
  use Frappe's own self-service User form and image field.
- Verification: app and release suites passed; active-site food-expense and
  workspace Frappe test modules exited successfully. The workspace test
  confirmed that Joffre and Elvis pass Frappe CRM's own application-entry
  permission check. Live roles include `Sales User` for those users and keep
  CRM setup access excluded for Communications. BIF symbol is `FBu`; ping, new
  logo, favicon, and cache-distinct branding script return HTTP 200. All
  Compose services are running, with backend and database healthy.
- Data protection: `bench backup --with-files` completed at `20261009_085049`;
  database, site configuration, public and private files were included. No
  restore rehearsal or off-machine encrypted backup was performed, as deferred.
- Deployment: active local self-hosted Compose stack; `rundinova.env` pins
  `CUSTOM_TAG=16.37.7-rn.71-crm-bootstrap-order`. Database and Redis images and
  volumes were not changed. Rollback candidates `.69`, `.70`, and `.71` remain
  local.

## VPS deployment candidate — rn.72 — 2026-10-09

### VPS image delivery

Existing VPS applications use GHCR images with release-specific tags. RundiNova
uses the same delivery path: publish the already-built, locally verified image
to `ghcr.io/jubuniyokodev/rundinova-erpnext`, then let the VPS pull that tag.
The first publication seeds the complete Frappe image once; future app-only
overlays add only their changed layers. Never rebuild this release from moving
Frappe, ERPNext, HRMS, or CRM branches.

Publish with a new tag for every release:

```bash
bash images/rundinova/publish-image.sh \
  rundinova/erpnext:16.37.7-rn.72-production-no-default-password \
  ghcr.io/jubuniyokodev/rundinova-erpnext:16.37.7-rn.72-production-no-default-password
```

The script uses the authenticated GitHub CLI token through standard input,
prints no credential, and refuses to replace a local tag. The account must
have `write:packages`. Record the published registry digest and configure the
VPS Compose project to pull the unique release tag before starting services.

- Image: `rundinova/erpnext:16.37.7-rn.72-production-no-default-password`
- Image ID: `sha256:f8fcdab9fe75770e1f89de7d99fec16e9cfc8a9e4a2ec5b190d192e5c50f3314`
- Pinned local base: `rundinova/erpnext:16.37.7-rn.71-crm-bootstrap-order`
- Base image ID: `sha256:840aecaf5bd33a324f952f11671e97e820ba63e5b64210e216fe2ddd0cef91b6`
- Release type: app-only overlay; no upstream Frappe, ERPNext, HRMS, or CRM
  revisions were selected.
- Change: remove the shared `RundiNova@2026` fallback from founding-user
  provisioning. A password is set only when an operator explicitly supplies
  one; new accounts no longer receive a known shared credential.
- Verification: source inspection confirmed the shared default is absent and
  the explicit-password branch remains. The immutable image build completed.
  No app test suite was run for this small change.
- Published image digest: `sha256:f8fcdab9fe75770e1f89de7d99fec16e9cfc8a9e4a2ec5b190d192e5c50f3314`.
- Production: deployed on `workspace.rundinova.com` on 2026-10-10 as an isolated
  Compose project under `/opt/rundinova-production`. The application listens
  only on `127.0.0.1:18081`; the host Nginx site has a separate TLS certificate
  and automatically renews it. The existing public website vhost was not changed.
- Initial production data: RundiNova Tech in BIF, six employee records, five
  enabled user accounts, one October 2026 food budget with 16 planned items,
  zero food expenses, and zero cash or bank transactions. The BIF display symbol
  is `FBU`.
- Credentials: generated separately per account and stored in the root-only
  VPS file `/root/rundinova-initial-credentials.txt`; no shared default password
  is used. Mail delivery is not configured, so credentials are not emailed.
- Registry access: the GHCR package is private. VPS Compose uses
  `PULL_POLICY=missing` so normal restarts reuse the installed immutable image
  without storing a GitHub token on the server. For releases, authenticate
  temporarily, pull the new immutable tag, then start with `--pull never`.
- Smoke verification: production services reported healthy; HTTPS
  `/api/method/ping` returned `200 pong`; Joffre's supplied login returned
  `Logged In`; the food-progress module imports successfully; the budget's
  committed and actual amounts remain zero.
- Deferred: off-machine encrypted backups and a restoration rehearsal remain
  postponed by explicit user decision. Full business workflow acceptance is
  still to be performed by the RundiNova team in the browser.

## Superseded VPS release — rn.73 — 2026-10-10

- Image: `ghcr.io/jubuniyokodev/rundinova-erpnext:16.37.7-rn.73-install-provisioning-fbu`
- Image ID and registry digest:
  `sha256:ed0ea47107141e7e5ef272ffc4902855d58303b01832abad980afe25fccd4a31`
- RundiNova source SHA-256:
  `1ab038f5e24196f1ba0a96633a55db02278f5dcf593942de86c4617b173e023a`; it
  matches the app-source digest embedded in the production image metadata.
- Pinned app-only base: `16.37.7-rn.72-production-no-default-password`
- Change: first-install provisioning now applies RundiNova branding, form
  layouts, workspace and desktop visibility, and the `FBU` BIF display symbol.
  The currency migration also consistently writes `FBU`.
- Production migration: `bench --site workspace.rundinova.com migrate`
  completed successfully. A first attempt exposed a MariaDB account tied to the
  old backend container IP; the account was moved to `%` inside the private
  Compose network. MariaDB has no published host port.
- Verification: backend and database are healthy, frontend is running, HTTPS
  `/api/method/ping` returns `pong`, and the login page displays the RundiNova
  logo. Production records remain six employees, five enabled users, one food
  budget, and zero food expenses. The workspace is visible and BIF displays
  `FBU`.
- Pre-migration database/config backup:
  `20261010_132016-workspace_rundinova_com`; `bench backup` was run without
  files. Encrypted off-machine retention and restoration remain deferred.
- The previous rn.72 image remains available on the VPS for rollback. The
  production environment pins rn.73 and uses `PULL_POLICY=never`; release
  images are pulled explicitly with temporary GHCR authentication.

## Superseded VPS release — rn.76 — 2026-10-10

- Image: `ghcr.io/jubuniyokodev/rundinova-erpnext:16.37.7-rn.76-self-hosted-candidate`
- Image ID and registry digest:
  `sha256:67af1c8493c8a55b0137e8596e24bb93687550723f6469435a2064ab62aafde7`
- Source commit: `5c53e014de017ff828bc8c1e28b2c52e0f0e92ca` on
  `release/rn-76-self-hosted-candidate`.
- RundiNova source SHA-256:
  `ce08da1dc8fcbb5cfeedb81d17ff50863cf07d239c65320b121b801014f0baf0`;
  it matches the image metadata and source tree.
- Pinned base: rn.73 image ID
  `sha256:ed0ea47107141e7e5ef272ffc4902855d58303b01832abad980afe25fccd4a31`.
  Frappe, ERPNext, HRMS, and CRM versions were not upgraded.
- Change: decouple workspace/provisioning tests from production users, fix the
  Frappe v16 food-expense test session, and declare the app's `requests`
  dependency so the GitHub checks install the package correctly.
- Verification: GitHub workflow run
  [38053192054](https://github.com/JubuNiyokoDev/rundinova-os/actions/runs/38053192054)
  passed after the dependency fix. The isolated VPS harness passed 55 core
  tests and 52 Frappe controller/provisioning tests; its temporary services,
  networks, and volumes were removed. Production `bench migrate` exited 0,
  backend and database are healthy, and public HTTPS `/api/method/ping` returns
  `200 pong`.
- Preserved production records: six employees, five enabled team accounts, one
  food budget, and zero food expenses before and after migration.
- Pre-migration backup with database and files:
  `20261010_145123-workspace_rundinova_com`; gzip and both file archives were
  verified. Encrypted off-machine retention and restoration rehearsal remain
  deferred by operator decision.
- Production is pinned to rn.76 with `PULL_POLICY=never`. The prior production
  image is rn.73; the previous environment file is kept at
  `/etc/rundinova/production.env.before-rn76-self-hosted-candidate`.
- Status: deployed and verified; superseded by rn.77 below.

## Active VPS release — rn.77 — 2026-10-10

- Image: `ghcr.io/jubuniyokodev/rundinova-erpnext:16.37.7-rn.77-professional-ux`
- Image ID and published GHCR manifest digest (published and verified on
  2026-10-11):
  `sha256:2164d00b66f9cf2edb76d75e69088ac488fd971cc4967993365e5831f8877d15`.
  The image was built locally on the VPS, then pushed directly from that host
  to GHCR; its registry manifest digest matches the VPS image ID. Production
  remains pinned with `PULL_POLICY=never`. The GHCR package is private, so a
  separate host needs authorized package access before it can pull this image.
- Source: merged main commit `ae5e81451daee1e05ed07c9d529065578f1cfd9f`;
  the candidate source tree used for the build is identical to the merge tree.
- RundiNova source SHA-256:
  `838fd96027f12031f0516ed4540091ca2a67a55b7fe21904c719a05753a9b0fa`,
  verified in the image's release metadata.
- Pinned base: rn.76 image ID
  `sha256:67af1c8493c8a55b0137e8596e24bb93687550723f6469435a2064ab62aafde7`.
  Frappe 16.36.1, ERPNext 16.37.0, HRMS 16.20.1, and CRM 1.86.0 remain
  unchanged.
- Change: correct the image CI so it installs the standalone RundiNova core,
  excludes only Frappe-dependent app tests from the host-side test environment,
  and sets `PULL_POLICY=always` for the integration test that must pull the
  locally built images. The complete image builds and tests pass for v15/v16
  on amd64/arm64.
- Staging verification: restored the production backup into an isolated Compose
  project with separate database and site volumes, ran `bench migrate`, and
  verified 6 employees, 1 food budget, and 33 food expenses before and after.
  The RundiNova Tech workspace and Executive Dashboard exist after migration.
- Production migration: the deliberate migrator completed successfully after
  the final backup. All RundiNova containers are running; backend and database
  report healthy. Public HTTPS `/api/method/ping` returns `pong`.
- Preserved records after deployment: 6 employees, 1 food budget, and 33 food
  expenses.
- Pre-migration backup with database and files:
  `20261010_232412-workspace_rundinova_com`; archives were created on the VPS.
  Encrypted off-machine retention and restoration rehearsal remain postponed
  by explicit user decision.
- Rollback image: rn.76 remains on the VPS. Previous environment file:
  `/etc/rundinova/production.env.before-rn77-professional-ux`.
- A private staging stack remains on the VPS, bound to localhost port 28181
  with separate volumes. It must not be exposed publicly.
- Status: deployed and health-checked; RundiNova team acceptance of daily
  browser workflows remains pending.

## Local verification candidate — rn.76 — 2026-10-10

- Image: `rundinova/erpnext:16.37.7-rn.76-test-fixture-independence`
- Image ID: `sha256:ec374a3ad9755fadd68552220440f96bf5036d809f1360820d1863fcd3d3db64`
- Base: rn.73 image ID
  `sha256:ed0ea47107141e7e5ef272ffc4902855d58303b01832abad980afe25fccd4a31`.
- Source SHA-256:
  `c76aeeab2e06f8162a056472ff7dba41410e4ddd55a0fde4a6739f05043994b6`; it
  matches both the local app tree and the image's release metadata.
- Change: make CRM provisioning tests independent of real production users and
  exercise the actual role-grant function; make the food-expense authorization
  tests compatible with Frappe v16's dict-backed session and return a successful
  policy result from their mock.
- Verification: the disposable Frappe harness completed against this exact
  image. All 55 framework-independent core tests passed; all 52 Frappe
  controller and workspace tests passed, including 13 food-expense tests and
  25 workspace/provisioning tests. The harness removed its temporary Compose
  containers, networks, and volumes. `git diff --check` and
  `git diff --cached --check` passed.
- Status: superseded by the active VPS release below. It was a local test
  candidate; its framework and app versions were unchanged.

## Active VPS release — rn.82 — 2026-10-11

- Image: `ghcr.io/jubuniyokodev/rundinova-erpnext:16.37.7-rn.82-team-accounts`
- Published GHCR manifest digest:
  `sha256:ac69af5d6e97756907bd9e2a6cc38e009143f718c958c868ba19c1a716b3a7a5`.
- Source: main commit `e4fc1a8e93241a34f4d5d910cbf320f93e4dedff`; the build
  used the merged role, migration-order, and team-account corrections.
- Base: rn.81 digest
  `sha256:7dfba025adfa8c1f7becd4a1e4731d09dd5729e62164fdf14de93fc5a0b4b750`.
  Frappe 16.36.1, ERPNext 16.37.0, HRMS 16.20.1, and CRM 1.86.0 remain
  unchanged.
- Changes: create RundiNova custom roles before workspace fixtures are synced;
  attach Janvier's Employee record to the confirmed
  `ndabubahajanvier@gmail.com` login and disable the superseded
  `1.ndabubahajanvier@gmail.com` account. Preserve self-only Employee access for
  team members while allowing the Director to read the full directory.
- Staging: candidate migration and user sync passed on the isolated `rn77-staging`
  Compose project. Application-level `get_list` checks returned 6 Employee
  records for Joffre and 1 for Housekeeping. All six intended accounts are
  enabled, linked to their correct Employee record, and carry the intended
  business role. The superseded Janvier account is disabled.
- Production: deployed on `workspace.rundinova.com`; pinned with
  `PULL_POLICY=never`. The production `.env` rollback copy is
  `/etc/rundinova/production.env.before-rn82-team-accounts`. The complete
  pre-migration backup is
  `20261011_163124-workspace_rundinova_com` and includes the database, site
  config, public files, and private files.
- Verification: migration and team synchronization exited successfully;
  backend and database report healthy; public HTTPS
  `/api/method/ping` returned `200 pong`; application permission checks returned
  6 Employee records for Joffre and 1 for Housekeeping. Production retains six
  employees, one food budget, zero food expenses, and zero cash movements.
- Rollback: prior production image rn.79 remains available locally, and the
  previous production env is saved at the path above. Restore the environment
  file before recreating the production Compose stack if rollback is required.
- Deferred: the RundiNova team still needs to run the browser acceptance
  checklist in `PRODUCTION_ACCEPTANCE_TESTS.md`. SMTP and outbound email remain
  unconfigured; GitHub repository synchronization remains a separate
  operator-authorized setup.
