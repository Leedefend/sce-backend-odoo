#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"

source_host="${BLOCKER_DAILY_DEV_SSH_HOST:-sc-root}"
db_container="${BLOCKER_DAILY_DEV_DB_CONTAINER:-sc-backend-odoo-dev-db-1}"
odoo_container="${BLOCKER_DAILY_DEV_ODOO_CONTAINER:-sc-backend-odoo-dev-odoo-1}"
source_database="${BLOCKER_DAILY_DEV_DATABASE:-sc_demo}"
output="${BLOCKER_HISTORY_BACKUP_ROOT:-artifacts/production-blocker/source/daily-dev-history-source-backup}"
dump="$output/database.dump"
filestore="$output/filestore.tar.gz"

mkdir -p "$output"

remote_db_watermark() {
  ssh -o BatchMode=yes "$source_host" \
    "docker exec '$db_container' psql -U odoo -d '$source_database' -AtF '|' -c \"select pg_database_size(current_database()), (select count(*) from ir_attachment), coalesce((select max(write_date)::text from ir_attachment),''), (select count(*) from ir_model_data where module='smart_construction_demo'), coalesce((select state from ir_module_module where name='smart_construction_demo'),'missing');\""
}

remote_filestore_watermark() {
  ssh -o BatchMode=yes "$source_host" \
    "docker exec '$odoo_container' sh -lc \"set -eu; root='/var/lib/odoo/filestore/$source_database'; count=\\\$(find \\\"\\\$root\\\" -type f | wc -l); bytes=\\\$(find \\\"\\\$root\\\" -type f -printf '%s\\\\n' | awk '{s+=\\\$1} END {print s+0}'); digest=\\\$(find \\\"\\\$root\\\" -type f -exec sha256sum {} + | sort -k2 | sha256sum | awk '{print \\\$1}'); printf '%s|%s|%s\\\\n' \\\"\\\$count\\\" \\\"\\\$bytes\\\" \\\"\\\$digest\\\"\""
}

before_db="$(remote_db_watermark)"
before_filestore="$(remote_filestore_watermark)"
source_repo="$(ssh -o BatchMode=yes "$source_host" "cd /opt/projects/repos/sce-backend-odoo && printf '%s|%s|%s' \"\$(git rev-parse HEAD)\" \"\$(git branch --show-current)\" \"\$(git status --short | wc -l)\"")"
printf '%s\n' "$before_db" > "$output/.database-before"
printf '%s\n' "$before_filestore" > "$output/.filestore-before"
printf '%s\n' "$source_repo" > "$output/.source-repo"

rm -f "$dump.part" "$filestore.part"
ssh -o BatchMode=yes "$source_host" \
  "docker exec '$db_container' pg_dump -U odoo -d '$source_database' -Fc --no-owner --no-privileges" \
  > "$dump.part"
mv "$dump.part" "$dump"

ssh -o BatchMode=yes "$source_host" \
  "docker exec '$odoo_container' tar -C /var/lib/odoo/filestore -czf - '$source_database'" \
  > "$filestore.part"
mv "$filestore.part" "$filestore"

after_db="$(remote_db_watermark)"
after_filestore="$(remote_filestore_watermark)"
printf '%s\n' "$after_db" > "$output/.database-after"
printf '%s\n' "$after_filestore" > "$output/.filestore-after"
if command -v pg_restore >/dev/null 2>&1; then
  pg_restore --list "$dump" >/dev/null
else
  docker run --rm -v "$(realpath "$output"):/snapshot:ro" postgres:15 \
    pg_restore --list /snapshot/database.dump >/dev/null
fi
tar -tzf "$filestore" >/dev/null

BEFORE_DB="$before_db" AFTER_DB="$after_db" \
BEFORE_FILESTORE="$before_filestore" AFTER_FILESTORE="$after_filestore" \
SOURCE_REPO="$source_repo" SOURCE_HOST_ALIAS="$source_host" \
SOURCE_DB_CONTAINER="$db_container" SOURCE_ODOO_CONTAINER="$odoo_container" \
SOURCE_DATABASE="$source_database" OUTPUT="$output" python3 - <<'PY'
import datetime
import hashlib
import json
import os
from pathlib import Path

root = Path(os.environ["OUTPUT"])

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def db_watermark(value):
    size, attachment_count, attachment_write_max, demo_xmlids, demo_state = value.split("|", 4)
    return {
        "database_bytes": int(size),
        "attachment_count": int(attachment_count),
        "attachment_write_date_max": attachment_write_max,
        "demo_xmlid_count": int(demo_xmlids),
        "demo_module_state": demo_state,
    }

def filestore_watermark(value):
    count, size, digest = value.split("|", 2)
    return {"file_count": int(count), "total_bytes": int(size), "content_path_sha256": digest}

repo_head, repo_branch, repo_dirty_count = os.environ["SOURCE_REPO"].split("|", 2)
before_db = db_watermark(os.environ["BEFORE_DB"])
after_db = db_watermark(os.environ["AFTER_DB"])
before_fs = filestore_watermark(os.environ["BEFORE_FILESTORE"])
after_fs = filestore_watermark(os.environ["AFTER_FILESTORE"])
stable = (
    before_db["attachment_count"] == after_db["attachment_count"]
    and before_db["attachment_write_date_max"] == after_db["attachment_write_date_max"]
    and before_fs == after_fs
)
manifest = {
    "schema_version": 1,
    "captured_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "source": {
        "environment": "daily_development_server",
        "ssh_alias": os.environ["SOURCE_HOST_ALIAS"],
        "compose_project": "sc-backend-odoo-dev",
        "database_container": os.environ["SOURCE_DB_CONTAINER"],
        "odoo_container": os.environ["SOURCE_ODOO_CONTAINER"],
        "database": os.environ["SOURCE_DATABASE"],
        "repo_head": repo_head,
        "repo_branch": repo_branch,
        "repo_dirty_count": int(repo_dirty_count),
        "database_access": "read_only_export",
    },
    "watermarks": {
        "database_before": before_db,
        "database_after": after_db,
        "filestore_before": before_fs,
        "filestore_after": after_fs,
        "pair_stable_during_capture": stable,
    },
    "checksums": {
        "database.dump": sha256(root / "database.dump"),
        "filestore.tar.gz": sha256(root / "filestore.tar.gz"),
    },
}
(root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "source_database": manifest["source"]["database"],
    "source_repo_head": repo_head,
    "pair_stable_during_capture": stable,
    "database_bytes": after_db["database_bytes"],
    "filestore": after_fs,
    "checksums": manifest["checksums"],
}, sort_keys=True))
if not stable:
    raise SystemExit("daily development database/filestore changed during capture; snapshot rejected")
PY
