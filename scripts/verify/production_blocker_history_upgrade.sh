#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"

project="sc-production-blocker-matrix"
compose_file="docker-compose.migration-safety.yml"
database="${BLOCKER_HISTORY_UPGRADE_DATABASE:-sc_daily_history_upgrade}"
restore_database="${BLOCKER_HISTORY_RESTORE_DATABASE:-sc_history_restore_check}"
image="${BLOCKER_RUNTIME_IMAGE:-sce-blocker-runtime:test}"
artifacts="${BLOCKER_HISTORY_UPGRADE_ARTIFACTS:-artifacts/production-blocker/history-upgrade}"
backup_root="${BLOCKER_HISTORY_BACKUP_ROOT:-artifacts/production-blocker/source/daily-dev-history-source-backup}"
source_dump="$backup_root/database.dump"
source_filestore="$backup_root/filestore.tar.gz"
source_filestore_db="$(python3 - "$backup_root/manifest.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1]))["source"]["database"])
PY
)"
modules="smart_core,smart_construction_core,smart_construction_portal,smart_construction_custom"
compose=(docker compose -p "$project" -f "$compose_file")
export BLOCKER_RUNTIME_IMAGE="$image"
mkdir -p "$artifacts"

# Restore a clean clone of the daily-development server snapshot.  The demo
# ownership fixture belongs only to MIG-S01/S02 and must not influence the
# formal four-module historical upgrade fingerprint.
"${compose[@]}" up -d --wait db
"${compose[@]}" exec -T db dropdb -U odoo --if-exists "$database"
"${compose[@]}" exec -T db createdb -U odoo "$database"
"${compose[@]}" exec -T db pg_restore -U odoo -d "$database" --no-owner --no-privileges \
  < "$source_dump"
"${compose[@]}" run --rm --no-deps --user root --entrypoint bash odoo -lc \
  "rm -rf '/var/lib/odoo/filestore/$database' /tmp/history-upgrade-filestore; mkdir -p /tmp/history-upgrade-filestore /var/lib/odoo/filestore; tar -C /tmp/history-upgrade-filestore -xzf -; cp -a '/tmp/history-upgrade-filestore/$source_filestore_db' '/var/lib/odoo/filestore/$database'; rm -rf /tmp/history-upgrade-filestore" \
  < "$source_filestore"

python3 scripts/verify/migration_safety_fingerprint.py \
  --project "$project" --compose-file "$compose_file" --database "$database" \
  --output "$artifacts/pre.json"

upgrade_started="$(date +%s)"
set +e
"${compose[@]}" run --rm --no-deps --entrypoint odoo odoo \
  --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux \
  --data-dir=/var/lib/odoo -d "$database" --no-http --workers=0 --max-cron-threads=0 \
  -u "$modules" --without-demo=all --stop-after-init \
  2>&1 | tee "$artifacts/upgrade.log"
upgrade_status="${PIPESTATUS[0]}"
set -e
upgrade_finished="$(date +%s)"
[[ "$upgrade_status" -eq 0 ]]

python3 scripts/verify/migration_safety_fingerprint.py \
  --project "$project" --compose-file "$compose_file" --database "$database" \
  --output "$artifacts/post.json"

"${compose[@]}" exec -T db psql -U odoo -d "$database" -AtF '|' <<'SQL' > "$artifacts/module-status.txt"
SELECT name,state,COALESCE(latest_version,'')
FROM ir_module_module
WHERE name IN (
  'smart_core','smart_construction_core','smart_construction_portal',
  'smart_construction_custom','smart_construction_seed','smart_construction_demo'
)
ORDER BY name;
SELECT 'pending',count(*),''
FROM ir_module_module
WHERE state IN ('to install','to upgrade','to remove');
SQL

dump_started="$(date +%s)"
"${compose[@]}" exec -T db pg_dump -U odoo -d "$database" -Fc --no-owner --no-privileges \
  > "$artifacts/upgraded.dump"
"${compose[@]}" exec -T db pg_restore --list < "$artifacts/upgraded.dump" >/dev/null
dump_finished="$(date +%s)"

restore_started="$(date +%s)"
"${compose[@]}" exec -T db dropdb -U odoo --if-exists "$restore_database"
"${compose[@]}" exec -T db createdb -U odoo "$restore_database"
"${compose[@]}" exec -T db pg_restore -U odoo -d "$restore_database" --no-owner --no-privileges \
  < "$artifacts/upgraded.dump"
"${compose[@]}" run --rm --no-deps --user root --entrypoint bash odoo -lc \
  "rm -rf '/var/lib/odoo/filestore/$restore_database'; cp -a '/var/lib/odoo/filestore/$database' '/var/lib/odoo/filestore/$restore_database'"
python3 scripts/verify/migration_safety_fingerprint.py \
  --project "$project" --compose-file "$compose_file" --database "$restore_database" \
  --output "$artifacts/restored.json"
"${compose[@]}" exec -T db pg_dump -U odoo -d "$restore_database" -Fc --no-owner --no-privileges \
  > "$artifacts/restored-second.dump"
"${compose[@]}" exec -T db pg_restore --list < "$artifacts/restored-second.dump" >/dev/null
restore_finished="$(date +%s)"

UPGRADE_STARTED="$upgrade_started" UPGRADE_FINISHED="$upgrade_finished" \
DUMP_STARTED="$dump_started" DUMP_FINISHED="$dump_finished" \
RESTORE_STARTED="$restore_started" RESTORE_FINISHED="$restore_finished" \
ARTIFACTS="$artifacts" DATABASE="$database" RESTORE_DATABASE="$restore_database" \
python3 - <<'PY'
import hashlib
import json
import os
from pathlib import Path

root = Path(os.environ["ARTIFACTS"])
pre = json.loads((root / "pre.json").read_text())
post = json.loads((root / "post.json").read_text())
restored = json.loads((root / "restored.json").read_text())
module_rows = [line.split("|") for line in (root / "module-status.txt").read_text().splitlines()]
pending = next(int(row[1]) for row in module_rows if row[0] == "pending")
modules = {row[0]: {"state": row[1], "version": row[2]} for row in module_rows if row[0] != "pending"}

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

protected_unchanged = pre["protected_fingerprint_sha256"] == post["protected_fingerprint_sha256"]
restore_matches = post["protected_fingerprint_sha256"] == restored["protected_fingerprint_sha256"]
payload = {
    "schema_version": 1,
    "database": os.environ["DATABASE"],
    "restore_database": os.environ["RESTORE_DATABASE"],
    "upgrade_seconds": int(os.environ["UPGRADE_FINISHED"]) - int(os.environ["UPGRADE_STARTED"]),
    "dump_seconds": int(os.environ["DUMP_FINISHED"]) - int(os.environ["DUMP_STARTED"]),
    "restore_and_second_dump_seconds": int(os.environ["RESTORE_FINISHED"]) - int(os.environ["RESTORE_STARTED"]),
    "protected_business_fingerprint_unchanged": protected_unchanged,
    "restored_fingerprint_matches": restore_matches,
    "pending_modules": pending,
    "modules": modules,
    "demo_module_state_changed": pre["module_states"][0:1] != post["module_states"][0:1],
    "dumps": {
        "upgraded_sha256": sha(root / "upgraded.dump"),
        "restored_second_sha256": sha(root / "restored-second.dump"),
    },
}
(root / "summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print("[production-blocker-history-upgrade] " + json.dumps(payload, sort_keys=True))
if not protected_unchanged or not restore_matches or pending != 0:
    raise SystemExit(1)
if any(modules[name]["state"] != "installed" for name in (
    "smart_core", "smart_construction_core", "smart_construction_portal", "smart_construction_custom"
)):
    raise SystemExit(1)
PY
