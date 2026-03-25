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

OUT_JSON = Path("/mnt/artifacts/backend/edition_rollback_evidence_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/edition_rollback_evidence_guard.md")
PRODUCT_KEY = "construction.standard"
FIRST_VERSION = "rollback-guard-v1"
SECOND_VERSION = "rollback-guard-v2"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "first": {}, "second": {}, "rollback": {}}
try:
    service = EditionReleaseSnapshotService(env)
    first = service.freeze_release_surface(
        product_key=PRODUCT_KEY,
        version=FIRST_VERSION,
        role_code="pm",
        note="edition_rollback_evidence_guard first freeze",
    )
    second = service.freeze_release_surface(
        product_key=PRODUCT_KEY,
        version=SECOND_VERSION,
        role_code="pm",
        note="edition_rollback_evidence_guard second freeze",
    )
    if int(second.get("rollback_target_snapshot_id") or 0) != int(first.get("id") or 0):
        raise RuntimeError("rollback target evidence drift")
    rolled = service.rollback_to_snapshot(
        product_key=PRODUCT_KEY,
        target_snapshot_id=int(first.get("id") or 0),
        note="edition_rollback_evidence_guard rollback",
    )
    active = service.resolve_active_snapshot(product_key=PRODUCT_KEY)
    if int(active.get("id") or 0) != int(first.get("id") or 0):
        raise RuntimeError("rollback did not reactivate expected snapshot")
    report["first"] = {
        "snapshot_id": first.get("id"),
        "product_key": first.get("product_key"),
        "version": first.get("version"),
    }
    report["second"] = {
        "snapshot_id": second.get("id"),
        "product_key": second.get("product_key"),
        "version": second.get("version"),
        "rollback_target_snapshot_id": second.get("rollback_target_snapshot_id"),
    }
    report["rollback"] = {
        "reactivated_snapshot_id": rolled.get("id"),
        "reactivated_version": rolled.get("version"),
        "active_snapshot_id": active.get("id"),
        "active_version": active.get("version"),
    }
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Edition Rollback Evidence Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[edition_rollback_evidence_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Edition Rollback Evidence Guard\n\n"
    f"- status: `PASS`\n"
    f"- rollback_target: `{report['second'].get('rollback_target_snapshot_id')}`\n"
    f"- reactivated: `{report['rollback'].get('active_version')}`\n",
)
print("[edition_rollback_evidence_guard] PASS")
PY
