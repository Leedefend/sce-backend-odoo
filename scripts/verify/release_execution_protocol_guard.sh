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
from odoo.addons.smart_core.delivery.release_execution_engine import RELEASE_EXECUTION_PROTOCOL_VERSION
from odoo.addons.smart_core.delivery.release_orchestrator import ReleaseOrchestrator

OUT_JSON = Path("/mnt/artifacts/backend/release_execution_protocol_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/release_execution_protocol_guard.md")
PRODUCT_KEY = "construction.preview"
VERSION = "release-execution-protocol-guard-v1"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "action": {}, "trace": {}}
try:
    snapshot_service = EditionReleaseSnapshotService(env)
    orchestrator = ReleaseOrchestrator(env)
    candidate = snapshot_service.freeze_release_surface(
        product_key=PRODUCT_KEY,
        version=VERSION,
        role_code="pm",
        note="release_execution_protocol_guard candidate",
        replace_active=False,
    )
    action = orchestrator.promote_snapshot(
        product_key=PRODUCT_KEY,
        snapshot_id=int(candidate.get("id") or 0),
        note="release_execution_protocol_guard promote",
        replace_active=True,
    )
    trace = action.get("execution_trace_json") if isinstance(action.get("execution_trace_json"), dict) else {}
    runs = trace.get("runs") if isinstance(trace.get("runs"), list) else []
    if str(action.get("execution_protocol_version") or "").strip() != RELEASE_EXECUTION_PROTOCOL_VERSION:
        raise RuntimeError("execution protocol version drift")
    if not runs:
        raise RuntimeError("execution trace missing runs")
    last = runs[-1] if isinstance(runs[-1], dict) else {}
    steps = last.get("steps") if isinstance(last.get("steps"), list) else []
    step_keys = [str((step or {}).get("key") or "").strip() for step in steps if isinstance(step, dict)]
    for required in ("executor_gate", "approval_gate", "operation_execute"):
        if required not in step_keys:
            raise RuntimeError(f"missing execution step: {required}")
    if str(last.get("state") or "").strip() != "succeeded":
        raise RuntimeError("execution trace last run not succeeded")
    report["action"] = {
        "action_id": action.get("id"),
        "action_type": action.get("action_type"),
        "state": action.get("state"),
    }
    report["trace"] = {
        "contract_version": trace.get("contract_version"),
        "run_count": len(runs),
        "last_run_operation": last.get("operation"),
        "step_keys": step_keys,
    }
    env.cr.commit()
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Release Execution Protocol Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[release_execution_protocol_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Release Execution Protocol Guard\n\n"
    f"- status: `PASS`\n"
    f"- action: `{report['action'].get('action_type')}#{report['action'].get('action_id')}`\n"
    f"- steps: `{', '.join(report['trace'].get('step_keys') or [])}`\n",
)
print("[release_execution_protocol_guard] PASS")
PY
