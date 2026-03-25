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

OUT_JSON = Path("/mnt/artifacts/backend/release_orchestration_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/release_orchestration_guard.md")
PRODUCT_KEY = "construction.standard"
FIRST_VERSION = "release-orchestration-guard-v1"
SECOND_VERSION = "release-orchestration-guard-v2"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "release_action": {}, "rollback_action": {}, "active": {}}
try:
    snapshot_service = EditionReleaseSnapshotService(env)
    orchestrator = ReleaseOrchestrator(env)
    first = snapshot_service.freeze_release_surface(
        product_key=PRODUCT_KEY,
        version=FIRST_VERSION,
        role_code="pm",
        note="release_orchestration_guard first release",
        replace_active=True,
    )
    second = snapshot_service.freeze_release_surface(
        product_key=PRODUCT_KEY,
        version=SECOND_VERSION,
        role_code="pm",
        note="release_orchestration_guard second candidate",
        replace_active=False,
    )
    release_action = orchestrator.promote_snapshot(
        product_key=PRODUCT_KEY,
        snapshot_id=int(second.get("id") or 0),
        note="release_orchestration_guard promote second",
        replace_active=True,
    )
    rollback_action = orchestrator.rollback_snapshot(
        product_key=PRODUCT_KEY,
        target_snapshot_id=int(first.get("id") or 0),
        note="release_orchestration_guard rollback first",
    )
    active = snapshot_service.resolve_active_snapshot(product_key=PRODUCT_KEY)
    if str(release_action.get("state") or "").strip() != "succeeded":
        raise RuntimeError("release orchestration promote failed")
    if str(rollback_action.get("state") or "").strip() != "succeeded":
        raise RuntimeError("release orchestration rollback failed")
    if str(rollback_action.get("action_type") or "").strip() != "rollback_snapshot":
        raise RuntimeError("rollback action type drift")
    if int(rollback_action.get("result_snapshot_id") or 0) != int(first.get("id") or 0):
        raise RuntimeError("rollback result snapshot drift")
    if int(active.get("id") or 0) != int(first.get("id") or 0):
        raise RuntimeError("active snapshot not restored after rollback")
    report["release_action"] = {
        "action_id": release_action.get("id"),
        "source_snapshot_id": release_action.get("source_snapshot_id"),
        "target_snapshot_id": release_action.get("target_snapshot_id"),
        "result_snapshot_id": release_action.get("result_snapshot_id"),
    }
    report["rollback_action"] = {
        "action_id": rollback_action.get("id"),
        "source_snapshot_id": rollback_action.get("source_snapshot_id"),
        "target_snapshot_id": rollback_action.get("target_snapshot_id"),
        "result_snapshot_id": rollback_action.get("result_snapshot_id"),
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
        "# Release Orchestration Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[release_orchestration_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Release Orchestration Guard\n\n"
    f"- status: `PASS`\n"
    f"- rollback_action: `{report['rollback_action'].get('action_id')}`\n"
    f"- active_after_rollback: `{report['active'].get('version')}`\n",
)
print("[release_orchestration_guard] PASS")
PY
