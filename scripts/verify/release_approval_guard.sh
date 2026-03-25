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

OUT_JSON = Path("/mnt/artifacts/backend/release_approval_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/release_approval_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "standard_request": {}, "standard_approval": {}, "preview_direct": {}, "rollback_blocked": {}}
try:
    snapshot_service = EditionReleaseSnapshotService(env)
    admin_user = env.ref("base.user_admin")
    pm_user = env["res.users"].sudo().search([("login", "=", "demo_pm")], limit=1)
    if not pm_user:
        raise RuntimeError("demo_pm user missing")

    standard = snapshot_service.freeze_release_surface(
        product_key="construction.standard",
        version="approval-guard-standard-v1",
        role_code="pm",
        note="release_approval_guard standard freeze",
        replace_active=False,
    )
    preview = snapshot_service.freeze_release_surface(
        product_key="construction.preview",
        version="approval-guard-preview-v1",
        role_code="pm",
        note="release_approval_guard preview freeze",
        replace_active=False,
    )

    pm_orchestrator = ReleaseOrchestrator(env(user=pm_user.id))
    admin_orchestrator = ReleaseOrchestrator(env(user=admin_user.id))

    standard_request = pm_orchestrator.promote_snapshot(
        product_key="construction.standard",
        snapshot_id=int(standard.get("id") or 0),
        note="release_approval_guard standard request",
        replace_active=True,
    )
    if str(standard_request.get("state") or "").strip() != "pending":
        raise RuntimeError("standard promote request should stay pending")
    if str(standard_request.get("approval_state") or "").strip() != "pending_approval":
        raise RuntimeError("standard promote request should require approval")
    if str(standard_request.get("reason_code") or "").strip() != "APPROVAL_REQUIRED":
        raise RuntimeError("standard promote request reason drift")

    approved = admin_orchestrator.approve_action(
        action_id=int(standard_request.get("id") or 0),
        note="release_approval_guard admin approval",
    )
    if str(approved.get("approval_state") or "").strip() != "approved":
        raise RuntimeError("admin approval drift")
    standard_executed = admin_orchestrator.execute_action(action_id=int(standard_request.get("id") or 0))
    if str(standard_executed.get("state") or "").strip() != "succeeded":
        raise RuntimeError("approved standard promote did not succeed")

    preview_direct = pm_orchestrator.promote_snapshot(
        product_key="construction.preview",
        snapshot_id=int(preview.get("id") or 0),
        note="release_approval_guard preview direct",
        replace_active=True,
    )
    if str(preview_direct.get("state") or "").strip() != "succeeded":
        raise RuntimeError("preview promote should succeed directly")
    if str(preview_direct.get("approval_state") or "").strip() != "not_required":
        raise RuntimeError("preview promote approval state drift")

    rollback_blocked = pm_orchestrator.rollback_snapshot(
        product_key="construction.standard",
        target_snapshot_id=int(standard.get("id") or 0),
        note="release_approval_guard rollback blocked",
    )
    if str(rollback_blocked.get("state") or "").strip() != "failed":
        raise RuntimeError("pm rollback should fail")
    if str(rollback_blocked.get("reason_code") or "").strip() != "RELEASE_EXECUTOR_NOT_ALLOWED":
        raise RuntimeError("pm rollback reason drift")

    report["standard_request"] = {
        "action_id": standard_request.get("id"),
        "approval_state": standard_request.get("approval_state"),
        "state": standard_request.get("state"),
    }
    report["standard_approval"] = {
        "approved_by_user_id": approved.get("approved_by_user_id"),
        "approval_state": approved.get("approval_state"),
        "result_snapshot_id": standard_executed.get("result_snapshot_id"),
        "state": standard_executed.get("state"),
    }
    report["preview_direct"] = {
        "action_id": preview_direct.get("id"),
        "approval_state": preview_direct.get("approval_state"),
        "state": preview_direct.get("state"),
        "result_snapshot_id": preview_direct.get("result_snapshot_id"),
    }
    report["rollback_blocked"] = {
        "action_id": rollback_blocked.get("id"),
        "state": rollback_blocked.get("state"),
        "reason_code": rollback_blocked.get("reason_code"),
    }
    env.cr.commit()
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Release Approval Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[release_approval_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Release Approval Guard\n\n"
    f"- status: `PASS`\n"
    f"- standard request action: `{report['standard_request'].get('action_id')}`\n"
    f"- preview direct action: `{report['preview_direct'].get('action_id')}`\n"
    f"- blocked rollback action: `{report['rollback_blocked'].get('action_id')}`\n",
)
print("[release_approval_guard] PASS")
PY
