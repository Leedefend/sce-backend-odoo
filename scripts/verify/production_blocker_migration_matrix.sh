#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"

project="sc-production-blocker-matrix"
compose_file="docker-compose.migration-safety.yml"
image="${BLOCKER_RUNTIME_IMAGE:-sce-blocker-runtime:test}"
artifacts="${BLOCKER_MATRIX_ARTIFACTS:-artifacts/production-blocker/migration-matrix}"
backup_root="${BLOCKER_HISTORY_BACKUP_ROOT:-artifacts/production-blocker/source/daily-dev-history-source-backup}"
dump="$backup_root/database.dump"
filestore="$backup_root/filestore.tar.gz"
manifest="$backup_root/manifest.json"
source_filestore_db="$(python3 - "$manifest" <<'PY'
import json, sys
print(json.load(open(sys.argv[1]))["source"]["database"])
PY
)"
databases=(sc_demo sc_user_data_rehearsal sc_pilot_history_rehearsal sc_random_history_7c341f)
compose=(docker compose -p "$project" -f "$compose_file")

export BLOCKER_RUNTIME_IMAGE="$image"
mkdir -p "$artifacts/fingerprints" "$artifacts/logs"
[[ -f "$dump" && -f "$filestore" && -f "$manifest" ]] || {
  echo "[migration-matrix] paired history backup is unavailable: $backup_root" >&2
  exit 2
}
python3 - "$backup_root" <<'PY'
import hashlib, json, sys
from pathlib import Path
root = Path(sys.argv[1])
manifest = json.loads((root / "manifest.json").read_text())
if manifest.get("source", {}).get("environment") != "daily_development_server":
    raise SystemExit("snapshot source is not the daily development server")
if not manifest.get("watermarks", {}).get("pair_stable_during_capture"):
    raise SystemExit("database/filestore pair was not stable during capture")
for name, expected in manifest["checksums"].items():
    actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"checksum mismatch: {name}")
PY

"${compose[@]}" up -d --wait db
for database in "${databases[@]}"; do
  "${compose[@]}" exec -T db dropdb -U odoo --if-exists "$database"
  "${compose[@]}" exec -T db createdb -U odoo "$database"
  "${compose[@]}" exec -T db pg_restore -U odoo -d "$database" --no-owner --no-privileges < "$dump"
  "${compose[@]}" run --rm --no-deps --user root --entrypoint bash odoo -lc \
    "rm -rf '/var/lib/odoo/filestore/$database' /tmp/matrix-filestore; mkdir -p /tmp/matrix-filestore /var/lib/odoo/filestore; tar -C /tmp/matrix-filestore -xzf -; cp -a '/tmp/matrix-filestore/$source_filestore_db' '/var/lib/odoo/filestore/$database'; rm -rf /tmp/matrix-filestore" \
    < "$filestore"
  "${compose[@]}" exec -T db psql -U odoo -d "$database" \
    < scripts/verify/prepare_migration_safety_fixture.sql
  python3 scripts/verify/migration_safety_fingerprint.py \
    --project "$project" --compose-file "$compose_file" --database "$database" \
    --output "$artifacts/fingerprints/${database}-pre.json"
done

for database in "${databases[@]}"; do
  set +e
  "${compose[@]}" run --rm --no-deps --entrypoint odoo odoo \
    --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo \
    --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux \
    --data-dir=/var/lib/odoo -d "$database" --no-http --workers=0 --max-cron-threads=0 \
    -u smart_construction_seed --without-demo=all --stop-after-init \
    2>&1 | tee "$artifacts/logs/${database}-upgrade.log"
  status="${PIPESTATUS[0]}"
  set -e
  if [[ "$status" -ne 0 ]]; then
    echo "[migration-matrix] upgrade failed database=$database status=$status" >&2
    exit "$status"
  fi
  python3 scripts/verify/migration_safety_fingerprint.py \
    --project "$project" --compose-file "$compose_file" --database "$database" \
    --output "$artifacts/fingerprints/${database}-post.json"
done

ARTIFACTS="$artifacts" DATABASES="${databases[*]}" python3 - <<'PY'
import json, os
from pathlib import Path

root = Path(os.environ["ARTIFACTS"])
databases = os.environ["DATABASES"].split()
rows = []
for database in databases:
    pre = json.loads((root / "fingerprints" / f"{database}-pre.json").read_text())
    post = json.loads((root / "fingerprints" / f"{database}-post.json").read_text())
    same = pre["protected_fingerprint_sha256"] == post["protected_fingerprint_sha256"]
    rows.append({
        "database": database,
        "pre": pre["protected_fingerprint_sha256"],
        "post": post["protected_fingerprint_sha256"],
        "protected_data_unchanged": same,
        "demo_xmlids_unchanged": pre["demo_xmlids"] == post["demo_xmlids"],
        "relationships_unchanged": pre["relationships"] == post["relationships"],
        "filestore_unchanged": pre["filestore"] == post["filestore"],
        "demo_module_state_unchanged": [x for x in pre["module_states"] if x.startswith("smart_construction_demo=")] == [x for x in post["module_states"] if x.startswith("smart_construction_demo=")],
    })
first_pre = rows[0]["pre"]
first_post = rows[0]["post"]
pass_gate = all(
    row["protected_data_unchanged"]
    and row["demo_xmlids_unchanged"]
    and row["relationships_unchanged"]
    and row["filestore_unchanged"]
    and row["demo_module_state_unchanged"]
    and row["pre"] == first_pre
    and row["post"] == first_post
    for row in rows
)
payload = {
    "schema_version": 1,
    "matrix": rows,
    "database_rename_changes_semantics": False if pass_gate else True,
    "pass": pass_gate,
}
(root / "matrix-summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print("[migration-matrix] " + json.dumps(payload, sort_keys=True))
if not pass_gate:
    raise SystemExit(1)
PY

echo "[migration-matrix] PASS databases=${databases[*]}"
