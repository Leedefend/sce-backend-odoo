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
from odoo.addons.smart_core.delivery.release_operator_surface_service import ReleaseOperatorSurfaceService
from odoo.addons.smart_core.handlers.release_operator import (
    ReleaseOperatorApproveHandler,
    ReleaseOperatorPromoteHandler,
    ReleaseOperatorRollbackHandler,
)

OUT_JSON = Path("/mnt/artifacts/backend/release_operator_orchestration_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/release_operator_orchestration_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "standard": {}, "preview": {}, "rollback": {}}
try:
    snapshot_service = EditionReleaseSnapshotService(env)
    pm_user = env["res.users"].sudo().search([("login", "=", "demo_pm")], limit=1)
    admin_user = env.ref("base.user_admin")
    if not pm_user:
        raise RuntimeError("demo_pm missing")

    standard = snapshot_service.freeze_release_surface(
        product_key="construction.standard",
        version="operator-guard-standard-v1",
        role_code="pm",
        note="release operator guard standard freeze",
        replace_active=False,
    )
    preview = snapshot_service.freeze_release_surface(
        product_key="construction.preview",
        version="operator-guard-preview-v1",
        role_code="pm",
        note="release operator guard preview freeze",
        replace_active=False,
    )

    promote_handler = ReleaseOperatorPromoteHandler(env(user=pm_user.id))
    standard_request = promote_handler.handle(payload={"params": {"product_key": "construction.standard", "snapshot_id": int(standard.get("id") or 0), "replace_active": True}})
    if str(standard_request.get("approval_state") or "").strip() != "pending_approval":
        raise RuntimeError("standard operator promote should require approval")

    approve_handler = ReleaseOperatorApproveHandler(env(user=admin_user.id))
    standard_done = approve_handler.handle(payload={"params": {"action_id": int(standard_request.get("id") or 0), "execute_after_approval": True}})
    if str(standard_done.get("state") or "").strip() != "succeeded":
        raise RuntimeError("approved standard operator action did not succeed")

    preview_done = promote_handler.handle(payload={"params": {"product_key": "construction.preview", "snapshot_id": int(preview.get("id") or 0), "replace_active": True}})
    if str(preview_done.get("state") or "").strip() != "succeeded":
        raise RuntimeError("preview operator promote should succeed directly")

    rollback_handler = ReleaseOperatorRollbackHandler(env(user=admin_user.id))
    rollback = rollback_handler.handle(payload={"params": {"product_key": "construction.standard"}})
    if str(rollback.get("state") or "").strip() not in {"succeeded", "failed"}:
        raise RuntimeError("rollback operator result drift")

    surface = ReleaseOperatorSurfaceService(env(user=admin_user.id)).build_surface(product_key="construction.standard")
    if not isinstance(surface.get("release_history", {}).get("actions"), list):
        raise RuntimeError("operator history missing after action flow")

    report["standard"] = {
        "request_action_id": standard_request.get("id"),
        "approval_state": standard_request.get("approval_state"),
        "result_state": standard_done.get("state"),
        "result_snapshot_id": standard_done.get("result_snapshot_id"),
    }
    report["preview"] = {
        "action_id": preview_done.get("id"),
        "state": preview_done.get("state"),
        "result_snapshot_id": preview_done.get("result_snapshot_id"),
    }
    report["rollback"] = {
        "action_id": rollback.get("id"),
        "state": rollback.get("state"),
        "reason_code": rollback.get("reason_code"),
    }
    env.cr.commit()
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Release Operator Orchestration Guard\n\n"
        "- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[release_operator_orchestration_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Release Operator Orchestration Guard\n\n"
    "- status: `PASS`\n"
    f"- standard action: `{report['standard'].get('request_action_id')}`\n"
    f"- preview action: `{report['preview'].get('action_id')}`\n"
    f"- rollback action: `{report['rollback'].get('action_id')}`\n",
)
print("[release_operator_orchestration_guard] PASS")
PY
