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

from odoo.addons.smart_core.delivery.release_operator_surface_service import ReleaseOperatorSurfaceService

OUT_JSON = Path("/mnt/artifacts/backend/release_operator_surface_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/release_operator_surface_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "standard": {}, "preview": {}}
try:
    service = ReleaseOperatorSurfaceService(env)
    standard = service.build_surface(product_key="construction.standard")
    preview = service.build_surface(product_key="construction.preview")
    for label, payload in (("standard", standard), ("preview", preview)):
        if str(payload.get("contract_version") or "").strip() != "release_operator_surface_v1":
            raise RuntimeError(f"{label}: contract drift")
        pending = payload.get("pending_approval") if isinstance(payload.get("pending_approval"), dict) else {}
        history = payload.get("release_history") if isinstance(payload.get("release_history"), dict) else {}
        state = payload.get("release_state") if isinstance(payload.get("release_state"), dict) else {}
        if not isinstance(payload.get("products"), list) or len(payload.get("products")) < 2:
            raise RuntimeError(f"{label}: products missing")
        if not isinstance(pending.get("actions"), list):
            raise RuntimeError(f"{label}: pending approval surface missing")
        if not isinstance(history.get("actions"), list) or not isinstance(history.get("snapshots"), list):
            raise RuntimeError(f"{label}: history surface missing")
        if not isinstance(state.get("runtime_summary"), dict):
            raise RuntimeError(f"{label}: runtime summary missing")
        report[label] = {
            "product_key": payload.get("identity", {}).get("product_key"),
            "pending_count": pending.get("count"),
            "history_actions": len(history.get("actions") or []),
            "history_snapshots": len(history.get("snapshots") or []),
        }
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Release Operator Surface Guard\n\n"
        "- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[release_operator_surface_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Release Operator Surface Guard\n\n"
    "- status: `PASS`\n"
    f"- standard history actions: `{report['standard'].get('history_actions')}`\n"
    f"- preview history actions: `{report['preview'].get('history_actions')}`\n",
)
print("[release_operator_surface_guard] PASS")
PY
