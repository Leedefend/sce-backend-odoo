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

from odoo import fields

from odoo.addons.smart_core.delivery.edition_release_snapshot_service import EditionReleaseSnapshotService
from odoo.addons.smart_core.delivery.release_operator_write_model_service import (
    RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
    ReleaseOperatorWriteModelService,
)
from odoo.addons.smart_core.delivery.release_orchestrator import ReleaseOrchestrator

OUT_JSON = Path("/mnt/artifacts/backend/release_operator_write_model_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/release_operator_write_model_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "promote": {}, "approve": {}, "rollback": {}}
try:
    snapshot_service = EditionReleaseSnapshotService(env)
    write_model_service = ReleaseOperatorWriteModelService(env)
    orchestrator = ReleaseOrchestrator(env)

    candidate = snapshot_service.freeze_release_surface(
        product_key="construction.standard",
        version="operator-write-model-guard-v1",
        note="release operator write model guard",
        replace_active=True,
    )

    promote_model = write_model_service.build_from_intent(
        intent="release.operator.promote",
        params={
            "product_key": "construction.standard",
            "snapshot_id": int(candidate.get("id") or 0),
            "replace_active": True,
            "note": "promote via write model",
        },
    )
    if promote_model.get("contract_version") != RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION:
        raise RuntimeError("promote write model contract drift")
    promote_result = orchestrator.submit_write_model(promote_model)
    if str(promote_result.get("action_type") or "") != "promote_snapshot":
        raise RuntimeError("promote write model did not create promote action")
    report["promote"] = {
        "action_id": promote_result.get("id"),
        "state": promote_result.get("state"),
        "approval_state": promote_result.get("approval_state"),
    }

    pending_action = env["sc.release.action"].sudo().create(
        {
            "name": "approve_action:construction.standard",
            "action_type": "promote_snapshot",
            "state": "pending",
            "product_key": "construction.standard",
            "base_product_key": "construction",
            "edition_key": "standard",
            "requested_by_user_id": int(env.user.id) if env.user else False,
            "requested_at": fields.Datetime.now(),
            "policy_key": "release.promote.standard",
            "approval_required": True,
            "approval_state": "pending_approval",
            "allowed_executor_role_codes_json": ["admin", "executive", "pm"],
            "required_approver_role_codes_json": ["admin", "executive"],
            "policy_snapshot_json": {
                "policy_key": "release.promote.standard",
                "allow_self_approval": True,
                "allowed_executor_role_codes": ["admin", "executive", "pm"],
                "required_approver_role_codes": ["admin", "executive"],
            },
            "reason_code": "APPROVAL_REQUIRED",
            "note": "pending approval for write model guard",
            "request_payload_json": {"snapshot_id": int(candidate.get("id") or 0), "replace_active": True},
            "result_payload_json": {"status": "pending"},
            "diagnostics_json": {"status": "pending"},
            "execution_protocol_version": "release_execution_protocol_v1",
            "execution_trace_json": {"contract_version": "release_execution_protocol_v1", "runs": []},
        }
    )
    approve_model = write_model_service.build_from_intent(
        intent="release.operator.approve",
        params={
            "action_id": int(pending_action.id),
            "execute_after_approval": False,
            "note": "approve via write model",
        },
    )
    if approve_model.get("contract_version") != RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION:
        raise RuntimeError("approve write model contract drift")
    approve_result = orchestrator.submit_write_model(approve_model)
    if str(approve_result.get("approval_state") or "") != "approved":
        raise RuntimeError("approve write model did not approve action")
    report["approve"] = {
        "action_id": approve_result.get("id"),
        "state": approve_result.get("state"),
        "approval_state": approve_result.get("approval_state"),
    }

    rollback_model = write_model_service.build_from_intent(
        intent="release.operator.rollback",
        params={
            "product_key": "construction.standard",
            "target_snapshot_id": int(candidate.get("rollback_target_snapshot_id") or 0) or 0,
            "note": "rollback via write model",
        },
    )
    if rollback_model.get("contract_version") != RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION:
        raise RuntimeError("rollback write model contract drift")
    rollback_result = orchestrator.submit_write_model(rollback_model)
    if str(rollback_result.get("action_type") or "") != "rollback_snapshot":
        raise RuntimeError("rollback write model did not create rollback action")
    report["rollback"] = {
        "action_id": rollback_result.get("id"),
        "state": rollback_result.get("state"),
        "approval_state": rollback_result.get("approval_state"),
    }
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Release Operator Write Model Guard\n\n"
        "- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[release_operator_write_model_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Release Operator Write Model Guard\n\n"
    "- status: `PASS`\n"
    f"- promote state: `{report['promote'].get('state')}`\n"
    f"- approve state: `{report['approve'].get('approval_state')}`\n"
    f"- rollback state: `{report['rollback'].get('state')}`\n",
)
print("[release_operator_write_model_guard] PASS")
PY
