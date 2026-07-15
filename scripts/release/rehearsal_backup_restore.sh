#!/usr/bin/env bash
set -euo pipefail
action="${1:?action required}"
source_db="${2:?source database required}"
target_db="${3:-}"
export SC_ENVIRONMENT=release_rehearsal SC_ALLOW_DEMO_DATA=0 DB_NAME="$source_db"
python3 scripts/release/rehearsal_guard.py >/dev/null
if [[ -n "$target_db" ]]; then
  SC_ENVIRONMENT=release_rehearsal SC_ALLOW_DEMO_DATA=0 DB_NAME="$target_db" python3 scripts/release/rehearsal_guard.py >/dev/null
fi

project="${RELEASE_PROJECT:-sc-release-rehearsal}"
if docker compose version >/dev/null 2>&1; then compose=(docker compose); else compose=(docker-compose); fi
compose+=( -p "$project" -f docker-compose.yml -f docker-compose.release-rehearsal.yml )
artifact="artifacts/release/frontend-pilot-readiness"
backup="$artifact/backup"
mkdir -p "$backup"
db_dump="$backup/database.dump"
filestore_tar="$backup/filestore.tar.gz"
manifest="$backup/manifest.json"

if [[ "$action" == "recover-source" ]]; then
  [[ -f "$filestore_tar" && -f "$manifest" ]] || { echo "[release.filestore.recover] backup set missing" >&2; exit 2; }
  python3 - <<'PY'
import hashlib,json
from pathlib import Path
p=Path('artifacts/release/frontend-pilot-readiness/backup'); m=json.loads((p/'manifest.json').read_text())
for name,want in m['checksums'].items():
    if hashlib.sha256((p/name).read_bytes()).hexdigest() != want: raise SystemExit(f'checksum mismatch: {name}')
PY
  "${compose[@]}" exec -T odoo sh -c "test ! -e '/var/lib/odoo/filestore/$source_db' && mkdir -p /var/lib/odoo/filestore && tar -C /var/lib/odoo/filestore -xzf -" < "$filestore_tar"
  echo "[release.filestore.recover] PASS source=$source_db"
  exit 0
fi

if [[ "$action" == "backup" ]]; then
  start="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; start_s="$(date +%s)"
  "${compose[@]}" exec -T db pg_dump -U "$DB_USER" -d "$source_db" -Fc > "$db_dump"
  "${compose[@]}" exec -T odoo sh -c "mkdir -p /var/lib/odoo/filestore/$source_db && tar -C /var/lib/odoo/filestore -czf - '$source_db'" > "$filestore_tar"
  db_sha="$(sha256sum "$db_dump" | cut -d' ' -f1)"; fs_sha="$(sha256sum "$filestore_tar" | cut -d' ' -f1)"
  end="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; duration="$(( $(date +%s) - start_s ))"
  DB="$source_db" START="$start" END="$end" DURATION="$duration" DB_SHA="$db_sha" FS_SHA="$fs_sha" GIT_SHA="$(git rev-parse HEAD)" python3 - <<'PY'
import json, os
from pathlib import Path
p=Path('artifacts/release/frontend-pilot-readiness/backup')
payload={'schema_version':1,'database':os.environ['DB'],'release_sha':os.environ['GIT_SHA'],'started_at':os.environ['START'],'finished_at':os.environ['END'],'duration_seconds':int(os.environ['DURATION']),'database_bytes':(p/'database.dump').stat().st_size,'filestore_bytes':(p/'filestore.tar.gz').stat().st_size,'checksums':{'database.dump':os.environ['DB_SHA'],'filestore.tar.gz':os.environ['FS_SHA']}}
(p/'manifest.json').write_text(json.dumps(payload,indent=2)+'\n')
PY
  echo "[release.backup] PASS manifest=$manifest"
  exit 0
fi

[[ -f "$manifest" && -f "$db_dump" && -f "$filestore_tar" ]] || { echo "[release.restore] backup set missing" >&2; exit 2; }
python3 - <<'PY'
import hashlib,json
from pathlib import Path
p=Path('artifacts/release/frontend-pilot-readiness/backup'); m=json.loads((p/'manifest.json').read_text())
for name,want in m['checksums'].items():
    got=hashlib.sha256((p/name).read_bytes()).hexdigest()
    if got != want: raise SystemExit(f'checksum mismatch: {name}')
PY
start="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; start_s="$(date +%s)"
"${compose[@]}" exec -T db psql -U "$DB_USER" -d postgres -v ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$target_db' AND pid <> pg_backend_pid();" >/dev/null
"${compose[@]}" exec -T db dropdb -U "$DB_USER" --if-exists "$target_db"
"${compose[@]}" exec -T db createdb -U "$DB_USER" "$target_db"
"${compose[@]}" exec -T db pg_restore -U "$DB_USER" -d "$target_db" --no-owner --no-privileges < "$db_dump"
"${compose[@]}" exec -T odoo sh -c "rm -rf /tmp/release-filestore-restore '/var/lib/odoo/filestore/$target_db'; mkdir -p /tmp/release-filestore-restore /var/lib/odoo/filestore; tar -C /tmp/release-filestore-restore -xzf -; cp -a '/tmp/release-filestore-restore/$source_db' '/var/lib/odoo/filestore/$target_db'; rm -rf /tmp/release-filestore-restore" < "$filestore_tar"
tables="res_company res_users project_project construction_contract sc_settlement_order payment_request sc_payment_execution payment_ledger ir_attachment"
source_counts=""; target_counts=""
for table in $tables; do
  source_counts+="$table=$("${compose[@]}" exec -T db psql -U "$DB_USER" -d "$source_db" -Atc "SELECT count(*) FROM $table");"
  target_counts+="$table=$("${compose[@]}" exec -T db psql -U "$DB_USER" -d "$target_db" -Atc "SELECT count(*) FROM $table");"
done
[[ "$source_counts" == "$target_counts" ]] || { echo "[release.$action] restored table counts differ" >&2; exit 1; }
source_fs="$("${compose[@]}" exec -T odoo sh -c "find '/var/lib/odoo/filestore/$source_db' -type f -printf '%P\n' | sort | while read p; do sha256sum \"/var/lib/odoo/filestore/$source_db/\$p\" | sed \"s|/var/lib/odoo/filestore/$source_db/||\"; done | sha256sum" | cut -d' ' -f1)"
target_fs="$("${compose[@]}" exec -T odoo sh -c "find '/var/lib/odoo/filestore/$target_db' -type f -printf '%P\n' | sort | while read p; do sha256sum \"/var/lib/odoo/filestore/$target_db/\$p\" | sed \"s|/var/lib/odoo/filestore/$target_db/||\"; done | sha256sum" | cut -d' ' -f1)"
[[ "$source_fs" == "$target_fs" ]] || { echo "[release.$action] restored filestore digest differs" >&2; exit 1; }
end="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; duration="$(( $(date +%s) - start_s ))"
ACTION="$action" SOURCE="$source_db" TARGET="$target_db" START="$start" END="$end" DURATION="$duration" python3 - <<'PY'
import json,os
from pathlib import Path
out=Path('artifacts/release/frontend-pilot-readiness')/f"{os.environ['ACTION']}.json"
out.write_text(json.dumps({'schema_version':1,'action':os.environ['ACTION'],'source_database':os.environ['SOURCE'],'target_database':os.environ['TARGET'],'started_at':os.environ['START'],'finished_at':os.environ['END'],'duration_seconds':int(os.environ['DURATION']),'checksums_verified':True,'database_counts_verified':True,'filestore_digest_verified':True,'pass':True},indent=2)+'\n')
PY
echo "[release.$action] PASS target=$target_db duration=${duration}s"
