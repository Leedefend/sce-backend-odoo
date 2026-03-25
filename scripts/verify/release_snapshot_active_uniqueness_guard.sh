#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

source "$ROOT_DIR/scripts/common/env.sh"
source "$ROOT_DIR/scripts/common/guard_prod.sh"
source "$ROOT_DIR/scripts/_lib/common.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME required}"

compose ${COMPOSE_FILES} exec -T odoo sh -lc "odoo shell -d '${DB_NAME}' -c '${ODOO_CONF}'" <<'PY'
import json
from pathlib import Path

from odoo.addons.smart_core.delivery.edition_release_snapshot_service import EditionReleaseSnapshotService

OUT_JSON = Path("/mnt/artifacts/backend/release_snapshot_active_uniqueness_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/release_snapshot_active_uniqueness_guard.md")
PRODUCT_KEY = "construction.standard"
FIRST_VERSION = "snapshot-uniqueness-guard-v1"
SECOND_VERSION = "snapshot-uniqueness-guard-v2"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "first": {}, "second": {}, "active_count": 0}
try:
    service = EditionReleaseSnapshotService(env)
    first = service.freeze_release_surface(
        product_key=PRODUCT_KEY,
        version=FIRST_VERSION,
        role_code="pm",
        note="release_snapshot_active_uniqueness_guard first freeze",
        replace_active=True,
    )
    second = service.freeze_release_surface(
        product_key=PRODUCT_KEY,
        version=SECOND_VERSION,
        role_code="pm",
        note="release_snapshot_active_uniqueness_guard second freeze",
        replace_active=True,
    )
    model = env["sc.edition.release.snapshot"].sudo()
    active_rows = model.search(
        [("product_key", "=", PRODUCT_KEY), ("state", "=", "released"), ("is_active", "=", True), ("active", "=", True)]
    )
    first_rec = model.browse(int(first.get("id") or 0))
    second_rec = model.browse(int(second.get("id") or 0))
    if len(active_rows) != 1:
        raise RuntimeError(f"expected exactly one active released snapshot, got {len(active_rows)}")
    if int(active_rows.id) != int(second.get("id") or 0):
        raise RuntimeError("new released snapshot did not become unique active release")
    if str(first_rec.state or "").strip() != "superseded":
        raise RuntimeError("previous released snapshot was not superseded")
    if int(first_rec.replaced_by_snapshot_id.id or 0) != int(second.get("id") or 0):
        raise RuntimeError("previous released snapshot missing explicit replacement link")
    report["first"] = {
        "snapshot_id": first.get("id"),
        "version": first.get("version"),
        "state": str(first_rec.state or "").strip(),
        "replaced_by_snapshot_id": int(first_rec.replaced_by_snapshot_id.id or 0),
    }
    report["second"] = {
        "snapshot_id": second.get("id"),
        "version": second.get("version"),
        "state": str(second_rec.state or "").strip(),
        "is_active": bool(second_rec.is_active),
    }
    report["active_count"] = len(active_rows)
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Release Snapshot Active Uniqueness Guard\n\n"
        "- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[release_snapshot_active_uniqueness_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Release Snapshot Active Uniqueness Guard\n\n"
    "- status: `PASS`\n"
    f"- active_count: `{report['active_count']}`\n"
    f"- active_version: `{report['second'].get('version')}`\n",
)
print("[release_snapshot_active_uniqueness_guard] PASS")
PY
