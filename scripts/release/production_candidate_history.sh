#!/usr/bin/env bash
set -euo pipefail

action="${1:?action is required}"
root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"

source_db="${HISTORY_SOURCE_DB:-sc_demo}"
candidate_db="${CANDIDATE_DB:-sc_user_data_rehearsal_candidate}"
candidate_project="${CANDIDATE_PROJECT:-sc-production-candidate}"
candidate_image="${CANDIDATE_IMAGE:?CANDIDATE_IMAGE is required}"
artifacts="${CANDIDATE_ARTIFACTS:-artifacts/release/immutable-production-candidate-v1}"
source_backup="${HISTORY_SOURCE_BACKUP:-artifacts/production-blocker/source/daily-dev-history-source-backup}"
backup="$artifacts/history-source-backup"
mkdir -p "$backup" "$artifacts/fingerprints"

candidate_compose=(docker compose -p "$candidate_project" -f docker-compose.production-candidate.yml)
export CANDIDATE_IMAGE="$candidate_image" CANDIDATE_DB="$candidate_db" CANDIDATE_PROJECT="$candidate_project"

validate_daily_dev_pair() {
  python3 - "$source_backup" "$source_db" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
expected_database = sys.argv[2]
manifest = json.loads((root / "manifest.json").read_text())
source = manifest.get("source") or {}
if source.get("environment") != "daily_development_server":
    raise SystemExit("history source is not the daily development server")
if source.get("database") != expected_database:
    raise SystemExit("history source database does not match approval")
if source.get("database_access") != "read_only_export":
    raise SystemExit("history source was not captured read-only")
if not (manifest.get("watermarks") or {}).get("pair_stable_during_capture"):
    raise SystemExit("database/filestore pair was not stable during capture")
for name, expected in (manifest.get("checksums") or {}).items():
    path = root / name
    if not path.is_file():
        raise SystemExit(f"history source file missing: {name}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"history source checksum mismatch: {name}")
PY
}

case "$action" in
  source-probe)
    validate_daily_dev_pair
    SOURCE_DB="$source_db" SOURCE_BACKUP="$source_backup" CANDIDATE_ARTIFACTS="$artifacts" python3 - <<'PY'
import json, os
from pathlib import Path
out=Path(os.environ.get("CANDIDATE_ARTIFACTS","artifacts/release/immutable-production-candidate-v1"))
source=Path(os.environ["SOURCE_BACKUP"])
manifest=json.loads((source/"manifest.json").read_text())
watermarks=manifest["watermarks"]
payload={"schema_version":1,"database":os.environ["SOURCE_DB"],"source_class":"authorized_daily_development_server_pair","source_repo_head":manifest["source"]["repo_head"],"database_bytes":watermarks["database_after"]["database_bytes"],"filestore":{"file_count":watermarks["filestore_after"]["file_count"],"bytes":watermarks["filestore_after"]["total_bytes"],"content_path_sha256":watermarks["filestore_after"]["content_path_sha256"]},"pair_stable_during_capture":watermarks["pair_stable_during_capture"],"checksums":manifest["checksums"],"production_database_write_count":0,"authorized":True}
(out/"history-source.json").write_text(json.dumps(payload,indent=2)+"\n")
PY
    echo "[candidate.history] source-probe PASS source=daily-development-server db=$source_db paired=true"
    ;;
  backup)
    validate_daily_dev_pair
    start_s="$(date +%s)"; started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    cp "$source_backup/database.dump" "$backup/database.dump"
    cp "$source_backup/filestore.tar.gz" "$backup/filestore.tar.gz"
    db_sha="$(sha256sum "$backup/database.dump" | awk '{print $1}')"
    fs_sha="$(sha256sum "$backup/filestore.tar.gz" | awk '{print $1}')"
    duration="$(( $(date +%s) - start_s ))"; finished="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    SOURCE_DB="$source_db" STARTED="$started" FINISHED="$finished" DURATION="$duration" DB_SHA="$db_sha" FS_SHA="$fs_sha" python3 - <<'PY'
import json,os
from pathlib import Path
p=Path(os.environ.get("CANDIDATE_ARTIFACTS","artifacts/release/immutable-production-candidate-v1"))/"history-source-backup"
payload={"schema_version":1,"database":os.environ["SOURCE_DB"],"source_class":"authorized_daily_development_server_pair","started_at":os.environ["STARTED"],"finished_at":os.environ["FINISHED"],"duration_seconds":int(os.environ["DURATION"]),"database_bytes":(p/"database.dump").stat().st_size,"filestore_bytes":(p/"filestore.tar.gz").stat().st_size,"checksums":{"database.dump":os.environ["DB_SHA"],"filestore.tar.gz":os.environ["FS_SHA"]},"paired":True,"production_database_write_count":0}
(p/"manifest.json").write_text(json.dumps(payload,indent=2)+"\n")
PY
    echo "[candidate.history] backup PASS duration=${duration}s"
    ;;
  restore)
    python3 - "$backup" <<'PY'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]); m=json.loads((p/"manifest.json").read_text())
for name,want in m["checksums"].items():
    got=hashlib.sha256((p/name).read_bytes()).hexdigest()
    if got != want: raise SystemExit(f"checksum mismatch: {name}")
PY
    start_s="$(date +%s)"
    "${candidate_compose[@]}" up -d --wait db redis
    "${candidate_compose[@]}" exec -T db psql -U "$DB_USER" -d postgres -v ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$candidate_db' AND pid <> pg_backend_pid();" >/dev/null
    "${candidate_compose[@]}" exec -T db dropdb -U "$DB_USER" --if-exists "$candidate_db"
    "${candidate_compose[@]}" exec -T db createdb -U "$DB_USER" "$candidate_db"
    "${candidate_compose[@]}" exec -T db pg_restore -U "$DB_USER" -d "$candidate_db" --no-owner --no-privileges < "$backup/database.dump"
    "${candidate_compose[@]}" run --rm --no-deps --user root --entrypoint sh odoo -c "rm -rf '/var/lib/odoo/filestore/$candidate_db' /tmp/candidate-filestore; mkdir -p /tmp/candidate-filestore /var/lib/odoo/filestore; tar -C /tmp/candidate-filestore -xzf -; cp -a '/tmp/candidate-filestore/$source_db' '/var/lib/odoo/filestore/$candidate_db'; rm -rf /tmp/candidate-filestore" < "$backup/filestore.tar.gz"
    duration="$(( $(date +%s) - start_s ))"
    printf '{"schema_version":1,"action":"restore","duration_seconds":%s,"pass":true}\n' "$duration" > "$artifacts/history-restore.json"
    echo "[candidate.history] restore PASS duration=${duration}s"
    ;;
  upgrade)
    start_s="$(date +%s)"
    modules="${CANDIDATE_FORMAL_MODULES:-smart_core,smart_construction_core,smart_construction_portal,smart_construction_custom}"
    set +e
    "${candidate_compose[@]}" run --rm --no-deps --entrypoint odoo odoo \
      --db_host=db --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
      --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux \
      --data-dir=/var/lib/odoo -d "$candidate_db" --no-http --workers=0 --max-cron-threads=0 \
      -u "$modules" --without-demo=all --stop-after-init 2>&1 | tee "$artifacts/history-upgrade.log"
    odoo_status="${PIPESTATUS[0]}"
    set -e
    if [[ "$odoo_status" -ne 0 ]]; then
      duration="$(( $(date +%s) - start_s ))"
      CANDIDATE_ARTIFACTS="$artifacts" MODULES="$modules" DURATION="$duration" ODOO_STATUS="$odoo_status" python3 - <<'PY'
import json, os
from pathlib import Path
out = Path(os.environ["CANDIDATE_ARTIFACTS"])
payload = {
    "schema_version": 1,
    "action": "upgrade",
    "modules": os.environ["MODULES"].split(","),
    "duration_seconds": int(os.environ["DURATION"]),
    "odoo_exit_status": int(os.environ["ODOO_STATUS"]),
    "pass": False,
    "failure_class": "odoo_module_upgrade_failed",
}
(out / "history-upgrade.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
PY
      echo "[candidate.history] upgrade FAIL status=$odoo_status duration=${duration}s" >&2
      exit "$odoo_status"
    fi
    all_module_rows="$("${candidate_compose[@]}" exec -T db psql -U "$DB_USER" -d "$candidate_db" -At \
      -c "SELECT name || '=' || state FROM ir_module_module ORDER BY name")"
    module_rows="$(awk -F= -v wanted=",$modules," 'index(wanted, "," $1 ",") {print}' <<<"$all_module_rows")"
    installed_count="$(printf '%s\n' "$module_rows" | awk -F= '$2 == "installed" {count++} END {print count+0}')"
    expected_count="$(awk -F, '{print NF}' <<<"$modules")"
    pending_count="$("${candidate_compose[@]}" exec -T db psql -U "$DB_USER" -d "$candidate_db" -Atc \
      "SELECT count(*) FROM ir_module_module WHERE state IN ('to install','to upgrade','to remove')")"
    demo_state="$("${candidate_compose[@]}" exec -T db psql -U "$DB_USER" -d "$candidate_db" -Atc \
      "SELECT COALESCE((SELECT state FROM ir_module_module WHERE name='smart_construction_demo' LIMIT 1), 'missing')")"
    duration="$(( $(date +%s) - start_s ))"
    pass=false
    if [[ "$installed_count" == "$expected_count" && "$pending_count" == "0" && "$demo_state" == "uninstalled" ]]; then
      pass=true
    fi
    CANDIDATE_ARTIFACTS="$artifacts" MODULES="$modules" MODULE_ROWS="$module_rows" DURATION="$duration" PENDING_COUNT="$pending_count" DEMO_STATE="$demo_state" PASS="$pass" python3 - <<'PY'
import json, os
from pathlib import Path
out = Path(os.environ.get("CANDIDATE_ARTIFACTS", "artifacts/release/immutable-production-candidate-v1"))
payload = {
    "schema_version": 1,
    "action": "upgrade",
    "modules": os.environ["MODULES"].split(","),
    "module_states": dict(line.split("=", 1) for line in os.environ["MODULE_ROWS"].splitlines()),
    "pending_modules": int(os.environ["PENDING_COUNT"]),
    "demo_module_state": os.environ["DEMO_STATE"],
    "duration_seconds": int(os.environ["DURATION"]),
    "pass": os.environ["PASS"] == "true",
}
(out / "history-upgrade.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
PY
    if [[ "$pass" != true ]]; then
      echo "[candidate.history] upgrade gate FAIL installed=${installed_count}/${expected_count} pending=$pending_count demo=$demo_state" >&2
      exit 1
    fi
    echo "[candidate.history] upgrade PASS duration=${duration}s modules=$modules"
    ;;
  runtime-up)
    "${candidate_compose[@]}" up -d --wait odoo nginx
    echo "[candidate.history] runtime-up PASS url=http://127.0.0.1:${CANDIDATE_NGINX_PORT:-18088}"
    ;;
  runtime-down)
    "${candidate_compose[@]}" down --remove-orphans
    echo "[candidate.history] runtime-down PASS"
    ;;
  *) echo "unknown action: $action" >&2; exit 2 ;;
esac
