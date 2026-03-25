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
from odoo.addons.smart_core.delivery.release_audit_trail_service import ReleaseAuditTrailService
from odoo.addons.smart_core.delivery.release_execution_engine import RELEASE_EXECUTION_PROTOCOL_VERSION
from odoo.addons.smart_core.delivery.release_orchestrator import ReleaseOrchestrator

OUT_JSON = Path("/mnt/artifacts/backend/release_execution_trace_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/release_execution_trace_guard.md")
PRODUCT_KEY = "construction.standard"
FIRST_VERSION = "release-execution-trace-guard-v1"
SECOND_VERSION = "release-execution-trace-guard-v2"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "release_action": {}, "rollback_action": {}, "audit": {}}
try:
    snapshot_service = EditionReleaseSnapshotService(env)
    orchestrator = ReleaseOrchestrator(env)
    audit_service = ReleaseAuditTrailService(env)
    first = snapshot_service.freeze_release_surface(
        product_key=PRODUCT_KEY,
        version=FIRST_VERSION,
        role_code="pm",
        note="release_execution_trace_guard first",
        replace_active=True,
    )
    second = snapshot_service.freeze_release_surface(
        product_key=PRODUCT_KEY,
        version=SECOND_VERSION,
        role_code="pm",
        note="release_execution_trace_guard second",
        replace_active=False,
    )
    release_action = orchestrator.promote_snapshot(
        product_key=PRODUCT_KEY,
        snapshot_id=int(second.get("id") or 0),
        note="release_execution_trace_guard promote",
        replace_active=True,
    )
    rollback_action = orchestrator.rollback_snapshot(
        product_key=PRODUCT_KEY,
        target_snapshot_id=int(first.get("id") or 0),
        note="release_execution_trace_guard rollback",
    )
    audit = audit_service.build_audit_trail(product_key=PRODUCT_KEY)
    actions = audit.get("release_actions") if isinstance(audit.get("release_actions"), list) else []
    indexed = {int((row or {}).get("id") or 0): row for row in actions if isinstance(row, dict)}
    for label, action in (("release_action", release_action), ("rollback_action", rollback_action)):
        row = indexed.get(int(action.get("id") or 0), {})
        trace = row.get("execution_trace_json") if isinstance(row.get("execution_trace_json"), dict) else {}
        if str(row.get("execution_protocol_version") or "").strip() != RELEASE_EXECUTION_PROTOCOL_VERSION:
            raise RuntimeError(f"{label} protocol version missing in audit")
        runs = trace.get("runs") if isinstance(trace.get("runs"), list) else []
        if not runs:
            raise RuntimeError(f"{label} trace missing in audit")
        if str((runs[-1] or {}).get("state") or "").strip() != "succeeded":
            raise RuntimeError(f"{label} audit trace last run not succeeded")
        report[label] = {
            "action_id": action.get("id"),
            "action_type": action.get("action_type"),
            "run_count": len(runs),
        }
    report["audit"] = {
        "release_action_ids": [int((row or {}).get("id") or 0) for row in actions[:5]],
        "active_snapshot_id": ((audit.get("active_released_snapshot") or {}).get("id") if isinstance(audit.get("active_released_snapshot"), dict) else 0),
    }
    env.cr.commit()
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Release Execution Trace Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[release_execution_trace_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Release Execution Trace Guard\n\n"
    f"- status: `PASS`\n"
    f"- release_action: `{report['release_action'].get('action_id')}`\n"
    f"- rollback_action: `{report['rollback_action'].get('action_id')}`\n",
)
print("[release_execution_trace_guard] PASS")
PY
