#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
test_image="${RN_TEST_IMAGE:-}"
project="rundinova-itest-${RANDOM}-${RANDOM}"
site="rundinova-itest-${RANDOM}-${RANDOM}.local"
test_doctypes="${RN_TEST_DOCTYPES:-RundiNova Document|RundiNova Decision|RundiNova Asset|RundiNova Goal|RundiNova Cash Movement|RundiNova Food Expense|RundiNova Food Progress}"

if [[ -z "$test_image" ]]; then
	echo "Set RN_TEST_IMAGE to an app image tag already present locally." >&2
	exit 2
fi

case "$test_image" in
	*:* ) ;;
	*) echo "RN_TEST_IMAGE must be an image tag already present locally." >&2; exit 2 ;;
esac

if [[ "$test_image" == *@* ]]; then
	echo "RN_TEST_IMAGE must use an immutable local tag for this test runner." >&2
	exit 2
fi

image_name="${test_image%:*}"
image_tag="${test_image##*:}"
image_id="$(docker image inspect --format '{{.Id}}' "$test_image")"
env_file="$(mktemp "${TMPDIR:-/tmp}/rundinova-integration.XXXXXX.env")"
chmod 600 "$env_file"
printf '%s\n' \
	"CUSTOM_IMAGE=$image_name" \
	"CUSTOM_TAG=$image_tag" \
	"ERPNEXT_VERSION=16.37.7" \
	"PULL_POLICY=never" \
	"DB_PASSWORD=rundinova-integration-only" \
	"DB_HOST=db" \
	"DB_PORT=3306" \
	"REDIS_CACHE=redis-cache:6379" \
	"REDIS_QUEUE=redis-queue:6379" \
	"SOCKETIO_PORT=9000" > "$env_file"

compose_cmd=(
	docker compose
	--project-name "$project"
	--env-file "$env_file"
	-f "$repo_root/compose.yaml"
	-f "$repo_root/overrides/compose.mariadb.yaml"
	-f "$repo_root/overrides/compose.redis.yaml"
)

run_backend() {
	"${compose_cmd[@]}" run --rm --no-deps backend "$@"
}

cleanup() {
	"${compose_cmd[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
	rm -f -- "$env_file"
}
trap cleanup EXIT

echo "Running isolated Frappe controller tests with $test_image ($image_id)"
echo "Compose project: $project; disposable site: $site"

# This unique Compose project owns its own DB, Redis, and sites volumes. No
# service or volume from the active RundiNova project is mounted or reused.
"${compose_cmd[@]}" up -d db redis-cache redis-queue configurator

run_backend bash -lc \
	"cd /home/frappe/frappe-bench && \
	test ! -e apps/rundinova_tech/rundinova_tech/tests/test_cash_domain.py && \
	test ! -e apps/rundinova_tech/rundinova_tech/tests/test_currency_domain.py && \
	test ! -e apps/rundinova_tech/rundinova_tech/tests/test_expense_domain.py && \
	test ! -e apps/rundinova_tech/rundinova_tech/tests/test_food_domain.py && \
	test ! -e apps/rundinova_tech/rundinova_tech/tests/test_governance_domain.py && \
	echo 'App source tree replacement check passed.'"

run_backend bash -lc \
	"cd /home/frappe/frappe-bench && \
	PYTHONPATH=/home/frappe/frappe-bench/apps/rundinova_tech \
	env/bin/python -m unittest discover \
	-s apps/rundinova_tech/rundinova_core/tests -p 'test_*.py'"

run_backend bash -lc \
	"bench new-site --no-mariadb-socket --db-host db --db-port 3306 \\
	--db-root-password=rundinova-integration-only \\
	--mariadb-user-host-login-scope=% \\
	--admin-password=rundinova-integration-only \\
	--install-app erpnext '$site'"

for app in hrms crm rundinova_tech; do
	run_backend bash -lc \
		"bench --site '$site' install-app '$app'"
done

# Exercise the normal post-migration provisioning hooks on this disposable
# site. This catches workspace/dashboard setup failures before a candidate is
# considered for a data-bearing staging copy.
run_backend bash -lc "bench --site '$site' migrate"

run_backend bash -lc \
	"bench --site '$site' set-config allow_tests true"

IFS='|' read -r -a controller_doctypes <<< "$test_doctypes"
for doctype in "${controller_doctypes[@]}"; do
	run_backend bash -lc \
		"output=\$(bench --site '$site' run-tests --doctype '$doctype' 2>&1); status=\$?; \\
		printf '%s\\n' \"\$output\"; \\
		if [ \$status -ne 0 ]; then exit \$status; fi; \\
		if ! printf '%s\\n' \"\$output\" | grep -Eq 'Ran [1-9][0-9]* tests?'; then \\
			echo 'Frappe did not report any executed tests.' >&2; exit 1; \\
		fi"
done

run_backend bash -lc \
	"output=\$(bench --site '$site' run-tests --module rundinova_tech.rundinova_tech.tests.test_workspace_provisioning 2>&1); status=\$?; \\
	printf '%s\\n' \"\$output\"; \\
	if [ \$status -ne 0 ]; then exit \$status; fi; \\
	if ! printf '%s\\n' \"\$output\" | grep -Eq 'Ran [1-9][0-9]* tests?'; then \\
		echo 'Frappe did not report any workspace tests executed.' >&2; exit 1; \\
	fi"

echo "All RundiNova Frappe controller suites passed."
