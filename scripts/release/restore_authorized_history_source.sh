#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"
target_db="${HISTORY_SOURCE_DB:-sc_user_data_rehearsal}"
[[ "$target_db" == "sc_user_data_rehearsal" ]] || { echo "[history.source.restore] target must be sc_user_data_rehearsal" >&2; exit 2; }
project="${DAILY_DEV_PROJECT:-sc-backend-odoo-dev}"
db_dump="${HISTORY_DB_DUMP:-artifacts/db_sync/server_sc_demo_20260602_132355.dump}"
filestore_archive="${HISTORY_FILESTORE_ARCHIVE:-artifacts/db_sync/server_filestore_sc_demo_20260602_132355.tar.gz}"
artifacts="${CANDIDATE_ARTIFACTS:-artifacts/release/immutable-production-candidate-v1}"
[[ -f "$db_dump" && -f "$filestore_archive" ]] || { echo "[history.source.restore] paired backup files missing" >&2; exit 2; }
compose=(docker compose -p "$project" -f docker-compose.yml)

exists="$("${compose[@]}" exec -T db psql -U "$DB_USER" -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname='$target_db'")"
[[ -z "$exists" ]] || { echo "[history.source.restore] target database already exists; refusing overwrite" >&2; exit 2; }
target_fs_exists="$("${compose[@]}" exec -T odoo sh -c "test -e '/var/lib/odoo/filestore/$target_db' && echo yes || true")"
[[ -z "$target_fs_exists" ]] || { echo "[history.source.restore] target filestore already exists; refusing overwrite" >&2; exit 2; }

start_s="$(date +%s)"; started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
"${compose[@]}" exec -T db createdb -U "$DB_USER" "$target_db"
"${compose[@]}" exec -T db pg_restore -U "$DB_USER" -d "$target_db" --no-owner --no-privileges < "$db_dump"
"${compose[@]}" exec -T odoo sh -c "rm -rf /tmp/authorized-history-source; mkdir -p /tmp/authorized-history-source /var/lib/odoo/filestore; tar -C /tmp/authorized-history-source -xzf -; cp -a /tmp/authorized-history-source/sc_demo '/var/lib/odoo/filestore/$target_db'; rm -rf /tmp/authorized-history-source" < "$filestore_archive"
"${compose[@]}" exec -T db pg_dump -U "$DB_USER" -d "$target_db" -Fc >/dev/null
duration="$(( $(date +%s) - start_s ))"; finished="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
db_sha="$(sha256sum "$db_dump" | awk '{print $1}')"; fs_sha="$(sha256sum "$filestore_archive" | awk '{print $1}')"
mkdir -p "$artifacts"
TARGET_DB="$target_db" DB_DUMP="$db_dump" FILESTORE_ARCHIVE="$filestore_archive" DB_SHA="$db_sha" FS_SHA="$fs_sha" STARTED="$started" FINISHED="$finished" DURATION="$duration" python3 - <<'PY'
import json,os
from pathlib import Path
out=Path(os.environ.get("CANDIDATE_ARTIFACTS","artifacts/release/immutable-production-candidate-v1"))
payload={"schema_version":1,"target_database":os.environ["TARGET_DB"],"source_class":"authorized_paired_historical_backup","database_dump":os.environ["DB_DUMP"],"filestore_archive":os.environ["FILESTORE_ARCHIVE"],"checksums":{"database_dump":os.environ["DB_SHA"],"filestore_archive":os.environ["FS_SHA"]},"started_at":os.environ["STARTED"],"finished_at":os.environ["FINISHED"],"duration_seconds":int(os.environ["DURATION"]),"standard_pg_dump_after_restore":True,"paired":True,"production_database_write_count":0}
(out/"history-source-restore.json").write_text(json.dumps(payload,indent=2)+"\n")
PY
echo "[history.source.restore] PASS target=$target_db duration=${duration}s"
