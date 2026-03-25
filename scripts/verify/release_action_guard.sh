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
from odoo.addons.smart_core.delivery.release_orchestrator import ReleaseOrchestrator

OUT_JSON = Path("/mnt/artifacts/backend/release_action_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/release_action_guard.md")
PRODUCT_KEY = "construction.preview"
VERSION = "release-action-guard-v1"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "snapshot": {}, "action": {}, "active": {}}
try:
    snapshot_service = EditionReleaseSnapshotService(env)
    orchestrator = ReleaseOrchestrator(env)
    approved = snapshot_service.freeze_release_surface(
        product_key=PRODUCT_KEY,
        version=VERSION,
        role_code="pm",
        note="release_action_guard candidate",
        replace_active=False,
    )
    action = orchestrator.promote_snapshot(
        product_key=PRODUCT_KEY,
        snapshot_id=int(approved.get("id") or 0),
        note="release_action_guard promote",
        replace_active=True,
    )
    active = snapshot_service.resolve_active_snapshot(product_key=PRODUCT_KEY)
    if str(action.get("state") or "").strip() != "succeeded":
        raise RuntimeError("release action not succeeded")
    if str(action.get("action_type") or "").strip() != "promote_snapshot":
        raise RuntimeError("release action type drift")
    if int(action.get("target_snapshot_id") or 0) != int(approved.get("id") or 0):
        raise RuntimeError("action target snapshot drift")
    if int(action.get("result_snapshot_id") or 0) != int(active.get("id") or 0):
        raise RuntimeError("action result snapshot drift")
    report["snapshot"] = {
        "snapshot_id": approved.get("id"),
        "product_key": approved.get("product_key"),
        "version": approved.get("version"),
        "state": approved.get("state"),
    }
    report["action"] = {
        "action_id": action.get("id"),
        "action_type": action.get("action_type"),
        "state": action.get("state"),
        "source_snapshot_id": action.get("source_snapshot_id"),
        "target_snapshot_id": action.get("target_snapshot_id"),
        "result_snapshot_id": action.get("result_snapshot_id"),
    }
    report["active"] = {
        "snapshot_id": active.get("id"),
        "version": active.get("version"),
        "state": active.get("state"),
    }
    env.cr.commit()
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Release Action Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[release_action_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Release Action Guard\n\n"
    f"- status: `PASS`\n"
    f"- action: `{report['action'].get('action_type')}#{report['action'].get('action_id')}`\n"
    f"- active_snapshot: `{report['active'].get('version')}`\n",
)
print("[release_action_guard] PASS")
PY
