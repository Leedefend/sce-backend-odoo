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

from odoo.addons.smart_core.delivery.release_operator_read_model_service import (
    RELEASE_OPERATOR_READ_MODEL_CONTRACT_VERSION,
    ReleaseOperatorReadModelService,
)

OUT_JSON = Path("/mnt/artifacts/backend/release_operator_read_model_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/release_operator_read_model_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "standard": {}, "preview": {}}
try:
    service = ReleaseOperatorReadModelService(env)
    for label, product_key in (("standard", "construction.standard"), ("preview", "construction.preview")):
        payload = service.build_read_model(product_key=product_key)
        if str(payload.get("contract_version") or "").strip() != RELEASE_OPERATOR_READ_MODEL_CONTRACT_VERSION:
            raise RuntimeError(f"{label}: read model contract drift")
        if not isinstance(payload.get("products"), list) or len(payload.get("products")) < 2:
            raise RuntimeError(f"{label}: products missing")
        state = payload.get("current_release_state") if isinstance(payload.get("current_release_state"), dict) else {}
        queue = payload.get("pending_approval_queue") if isinstance(payload.get("pending_approval_queue"), dict) else {}
        history = payload.get("release_history_summary") if isinstance(payload.get("release_history_summary"), dict) else {}
        actions = payload.get("available_operator_actions") if isinstance(payload.get("available_operator_actions"), dict) else {}
        if not isinstance(state.get("runtime_summary"), dict):
            raise RuntimeError(f"{label}: current release state missing runtime summary")
        if not isinstance(queue.get("actions"), list):
            raise RuntimeError(f"{label}: pending approval queue missing")
        if not isinstance(history.get("actions"), list) or not isinstance(history.get("snapshots"), list):
            raise RuntimeError(f"{label}: release history summary missing")
        if not isinstance(actions.get("promote"), list) or not isinstance(actions.get("rollback"), dict):
            raise RuntimeError(f"{label}: available operator actions missing")
        report[label] = {
            "product_key": payload.get("identity", {}).get("product_key"),
            "pending_count": queue.get("count"),
            "history_actions": len(history.get("actions") or []),
            "candidate_snapshots": len(payload.get("candidate_snapshots") or []),
        }
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Release Operator Read Model Guard\n\n"
        "- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[release_operator_read_model_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Release Operator Read Model Guard\n\n"
    "- status: `PASS`\n"
    f"- standard history actions: `{report['standard'].get('history_actions')}`\n"
    f"- preview history actions: `{report['preview'].get('history_actions')}`\n",
)
print("[release_operator_read_model_guard] PASS")
PY
