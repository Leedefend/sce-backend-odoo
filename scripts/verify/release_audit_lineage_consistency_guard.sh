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
from odoo.addons.smart_core.delivery.release_orchestrator import ReleaseOrchestrator

OUT_JSON = Path("/mnt/artifacts/backend/release_audit_lineage_consistency_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/release_audit_lineage_consistency_guard.md")
PRODUCT_KEY = "construction.standard"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "summary": {}}
try:
    snapshot_service = EditionReleaseSnapshotService(env)
    orchestrator = ReleaseOrchestrator(env)
    audit_service = ReleaseAuditTrailService(env)

    first = snapshot_service.freeze_release_surface(
        product_key=PRODUCT_KEY,
        version="audit-lineage-standard-v1",
        role_code="pm",
        note="release_audit_lineage_consistency_guard first freeze",
        replace_active=False,
    )
    orchestrator.promote_snapshot(
        product_key=PRODUCT_KEY,
        snapshot_id=int(first.get("id") or 0),
        note="release_audit_lineage_consistency_guard promote first",
        replace_active=True,
    )
    second = snapshot_service.freeze_release_surface(
        product_key=PRODUCT_KEY,
        version="audit-lineage-standard-v2",
        role_code="pm",
        note="release_audit_lineage_consistency_guard second freeze",
        replace_active=False,
    )
    orchestrator.promote_snapshot(
        product_key=PRODUCT_KEY,
        snapshot_id=int(second.get("id") or 0),
        note="release_audit_lineage_consistency_guard promote second",
        replace_active=True,
    )
    orchestrator.rollback_snapshot(
        product_key=PRODUCT_KEY,
        target_snapshot_id=int(first.get("id") or 0),
        note="release_audit_lineage_consistency_guard rollback first",
    )

    audit = audit_service.build_audit_trail(product_key=PRODUCT_KEY)
    active = audit.get("active_released_snapshot") if isinstance(audit.get("active_released_snapshot"), dict) else {}
    lineage = audit.get("lineage") if isinstance(audit.get("lineage"), dict) else {}
    rollback = audit.get("rollback_evidence") if isinstance(audit.get("rollback_evidence"), dict) else {}
    snapshots = audit.get("release_snapshots") if isinstance(audit.get("release_snapshots"), list) else []
    actions = audit.get("release_actions") if isinstance(audit.get("release_actions"), list) else []
    runtime_lineage = lineage.get("released_snapshot_lineage") if isinstance(lineage.get("released_snapshot_lineage"), dict) else {}
    snapshot_ids = {int(row.get("id") or 0) for row in snapshots}
    active_count = sum(1 for row in snapshots if str(row.get("state") or "").strip() == "released" and row.get("is_active") is True)
    if not active:
        raise RuntimeError("active snapshot missing")
    if int(runtime_lineage.get("snapshot_id") or 0) != int(active.get("id") or 0):
        raise RuntimeError("runtime lineage active snapshot mismatch")
    if active_count != 1:
        raise RuntimeError("active released uniqueness drift")
    if rollback.get("rollback_target_snapshot_id") and int(rollback.get("rollback_target_snapshot_id") or 0) not in snapshot_ids:
        raise RuntimeError("rollback target snapshot missing from audit surface")
    for row in actions:
        for key in ("source_snapshot_id", "target_snapshot_id", "result_snapshot_id"):
            value = int(row.get(key) or 0)
            if value and value not in snapshot_ids:
                raise RuntimeError(f"action snapshot ref drift: {key}={value}")
    latest_rollback = next((row for row in actions if str(row.get("action_type") or "").strip() == "rollback_snapshot"), {})
    if latest_rollback and int(latest_rollback.get("result_snapshot_id") or 0) != int(active.get("id") or 0):
        raise RuntimeError("rollback result snapshot drift")
    report["summary"] = {
        "active_snapshot_id": active.get("id"),
        "active_version": active.get("version"),
        "runtime_lineage_snapshot_id": runtime_lineage.get("snapshot_id"),
        "rollback_target_snapshot_id": rollback.get("rollback_target_snapshot_id"),
        "action_count": len(actions),
        "snapshot_count": len(snapshots),
    }
    env.cr.commit()
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Release Audit Lineage Consistency Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[release_audit_lineage_consistency_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Release Audit Lineage Consistency Guard\n\n"
    f"- status: `PASS`\n"
    f"- active_snapshot: `{report['summary'].get('active_snapshot_id')}@{report['summary'].get('active_version')}`\n"
    f"- rollback_target: `{report['summary'].get('rollback_target_snapshot_id')}`\n",
)
print("[release_audit_lineage_consistency_guard] PASS")
PY
