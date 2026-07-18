#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"

project="sc-production-blocker-matrix"
compose_file="docker-compose.migration-safety.yml"
image="${BLOCKER_RUNTIME_IMAGE:-sce-blocker-runtime:test}"
database="${BLOCKER_FRESH_DATABASE:-sc_blocker_formal_empty}"
rollback_database="${BLOCKER_ROLLBACK_DATABASE:-sc_daily_history_upgrade}"
artifacts="${BLOCKER_FRESH_ARTIFACTS:-artifacts/production-blocker/fresh-and-rollback}"
modules="smart_core,smart_construction_core,smart_construction_portal,smart_construction_custom,smart_construction_seed"
compose=(docker compose -p "$project" -f "$compose_file")
export BLOCKER_RUNTIME_IMAGE="$image"
mkdir -p "$artifacts"

"${compose[@]}" up -d --wait db
"${compose[@]}" run --rm --no-deps --user root --entrypoint sh odoo -c \
  'mkdir -p /var/lib/odoo/filestore; chown -R odoo:odoo /var/lib/odoo'
"${compose[@]}" exec -T db dropdb -U odoo --if-exists "$database"
"${compose[@]}" exec -T db createdb -U odoo "$database"

run_odoo() {
  local mode="$1"
  "${compose[@]}" run --rm --no-deps --entrypoint odoo odoo \
    --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo \
    --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux \
    --data-dir=/var/lib/odoo -d "$database" --no-http --workers=0 --max-cron-threads=0 \
    "$mode" "$modules" --without-demo=all --stop-after-init
}

install_started="$(date +%s)"
run_odoo -i 2>&1 | tee "$artifacts/fresh-install.log"
install_finished="$(date +%s)"
upgrade_started="$(date +%s)"
run_odoo -u 2>&1 | tee "$artifacts/fresh-upgrade.log"
upgrade_finished="$(date +%s)"

"${compose[@]}" exec -T db psql -U odoo -d "$database" -AtF '|' <<'SQL' > "$artifacts/fresh-module-status.txt"
SELECT name,state,COALESCE(latest_version,'') FROM ir_module_module
WHERE name IN ('smart_core','smart_construction_core','smart_construction_portal','smart_construction_custom','smart_construction_seed','smart_construction_demo')
ORDER BY name;
SELECT 'pending',count(*),'' FROM ir_module_module WHERE state IN ('to install','to upgrade','to remove');
SQL

# Register a test-only installed version in an isolated history clone. The
# deliberately failing 1.1 migration writes a marker and raises; both the
# marker and module-version transition must roll back.
"${compose[@]}" exec -T db psql -U odoo -d "$rollback_database" <<'SQL'
INSERT INTO ir_module_module
  (name, state, latest_version, application, demo, license, create_uid, write_uid, create_date, write_date)
VALUES
  ('sc_migration_failure_fixture', 'installed', '17.0.0.1.0', false, false, 'LGPL-3', 1, 1, now(), now())
ON CONFLICT (name) DO UPDATE
SET state='installed', latest_version='17.0.0.1.0', write_uid=1, write_date=now();
DELETE FROM ir_config_parameter WHERE key='sc.migration_failure_fixture.marker';
SQL
python3 scripts/verify/migration_safety_fingerprint.py \
  --project "$project" --compose-file "$compose_file" --database "$rollback_database" \
  --output "$artifacts/rollback-pre.json"

set +e
"${compose[@]}" run --rm --no-deps \
  -v "$root/scripts/verify/fixtures:/mnt/failure-addons:ro" --entrypoint odoo odoo \
  --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux,/mnt/failure-addons \
  --data-dir=/var/lib/odoo -d "$rollback_database" --no-http --workers=0 --max-cron-threads=0 \
  -u sc_migration_failure_fixture --without-demo=all --stop-after-init \
  > "$artifacts/intentional-failure.log" 2>&1
failure_status="$?"
set -e
[[ "$failure_status" -ne 0 ]]

python3 scripts/verify/migration_safety_fingerprint.py \
  --project "$project" --compose-file "$compose_file" --database "$rollback_database" \
  --output "$artifacts/rollback-post.json"
rollback_state="$("${compose[@]}" exec -T db psql -U odoo -d "$rollback_database" -AtF '|' -c \
  "SELECT latest_version, (SELECT count(*) FROM ir_config_parameter WHERE key='sc.migration_failure_fixture.marker') FROM ir_module_module WHERE name='sc_migration_failure_fixture'")"

INSTALL_STARTED="$install_started" INSTALL_FINISHED="$install_finished" \
UPGRADE_STARTED="$upgrade_started" UPGRADE_FINISHED="$upgrade_finished" \
FAILURE_STATUS="$failure_status" ROLLBACK_STATE="$rollback_state" ARTIFACTS="$artifacts" \
python3 - <<'PY'
import json
import os
from pathlib import Path

root = Path(os.environ["ARTIFACTS"])
rows = [line.split("|") for line in (root / "fresh-module-status.txt").read_text().splitlines()]
pending = next(int(row[1]) for row in rows if row[0] == "pending")
modules = {row[0]: {"state": row[1], "version": row[2]} for row in rows if row[0] != "pending"}
pre = json.loads((root / "rollback-pre.json").read_text())
post = json.loads((root / "rollback-post.json").read_text())
version, marker_count = os.environ["ROLLBACK_STATE"].split("|", 1)
payload = {
    "schema_version": 1,
    "fresh_install_seconds": int(os.environ["INSTALL_FINISHED"]) - int(os.environ["INSTALL_STARTED"]),
    "fresh_upgrade_seconds": int(os.environ["UPGRADE_FINISHED"]) - int(os.environ["UPGRADE_STARTED"]),
    "pending_modules": pending,
    "modules": modules,
    "intentional_failure_exit_code": int(os.environ["FAILURE_STATUS"]),
    "rollback": {
        "protected_fingerprint_unchanged": pre["protected_fingerprint_sha256"] == post["protected_fingerprint_sha256"],
        "module_version": version,
        "marker_count": int(marker_count),
    },
}
(root / "summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print("[production-blocker-fresh-and-rollback] " + json.dumps(payload, sort_keys=True))
formal = ("smart_core", "smart_construction_core", "smart_construction_portal", "smart_construction_custom", "smart_construction_seed")
if pending != 0 or any(modules[name]["state"] != "installed" for name in formal):
    raise SystemExit(1)
if modules["smart_construction_demo"]["state"] != "uninstalled":
    raise SystemExit(1)
if not payload["rollback"]["protected_fingerprint_unchanged"] or version != "17.0.0.1.0" or int(marker_count) != 0:
    raise SystemExit(1)
PY
