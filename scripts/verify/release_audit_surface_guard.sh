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

OUT_JSON = Path("/mnt/artifacts/backend/release_audit_surface_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/release_audit_surface_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "standard": {}, "preview": {}}
try:
    snapshot_service = EditionReleaseSnapshotService(env)
    orchestrator = ReleaseOrchestrator(env)
    audit_service = ReleaseAuditTrailService(env)

    first = snapshot_service.freeze_release_surface(
        product_key="construction.standard",
        version="audit-surface-standard-v1",
        role_code="pm",
        note="release_audit_surface_guard first freeze",
        replace_active=False,
    )
    orchestrator.promote_snapshot(
        product_key="construction.standard",
        snapshot_id=int(first.get("id") or 0),
        note="release_audit_surface_guard promote first",
        replace_active=True,
    )
    second = snapshot_service.freeze_release_surface(
        product_key="construction.standard",
        version="audit-surface-standard-v2",
        role_code="pm",
        note="release_audit_surface_guard second freeze",
        replace_active=False,
    )
    orchestrator.promote_snapshot(
        product_key="construction.standard",
        snapshot_id=int(second.get("id") or 0),
        note="release_audit_surface_guard promote second",
        replace_active=True,
    )
    orchestrator.rollback_snapshot(
        product_key="construction.standard",
        target_snapshot_id=int(first.get("id") or 0),
        note="release_audit_surface_guard rollback first",
    )
    preview = snapshot_service.freeze_release_surface(
        product_key="construction.preview",
        version="audit-surface-preview-v1",
        role_code="pm",
        note="release_audit_surface_guard preview freeze",
        replace_active=False,
    )
    orchestrator.promote_snapshot(
        product_key="construction.preview",
        snapshot_id=int(preview.get("id") or 0),
        note="release_audit_surface_guard promote preview",
        replace_active=True,
    )

    standard_audit = audit_service.build_audit_trail(product_key="construction.standard")
    preview_audit = audit_service.build_audit_trail(product_key="construction.preview")
    for label, audit in (("standard", standard_audit), ("preview", preview_audit)):
        active = audit.get("active_released_snapshot") if isinstance(audit.get("active_released_snapshot"), dict) else {}
        runtime = audit.get("runtime") if isinstance(audit.get("runtime"), dict) else {}
        summary = runtime.get("release_audit_trail_summary") if isinstance(runtime.get("release_audit_trail_summary"), dict) else {}
        if str(audit.get("contract_version") or "").strip() != "release_audit_trail_surface_v1":
            raise RuntimeError(f"{label}: contract version drift")
        if not active:
            raise RuntimeError(f"{label}: active released snapshot missing")
        if str(active.get("state") or "").strip() != "released":
            raise RuntimeError(f"{label}: active snapshot state drift")
        if active.get("is_active") is not True:
            raise RuntimeError(f"{label}: active snapshot flag drift")
        if not audit.get("release_actions"):
            raise RuntimeError(f"{label}: release actions missing")
        if not audit.get("release_snapshots"):
            raise RuntimeError(f"{label}: release snapshots missing")
        if str(summary.get("active_snapshot_version") or "").strip() != str(active.get("version") or "").strip():
            raise RuntimeError(f"{label}: runtime summary drift")
        report[label] = {
            "active_snapshot_id": active.get("id"),
            "active_version": active.get("version"),
            "actions": len(audit.get("release_actions") or []),
            "snapshots": len(audit.get("release_snapshots") or []),
            "rollback_target_snapshot_id": (audit.get("rollback_evidence") or {}).get("rollback_target_snapshot_id"),
        }
    env.cr.commit()
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Release Audit Surface Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[release_audit_surface_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Release Audit Surface Guard\n\n"
    f"- status: `PASS`\n"
    f"- standard: `{report['standard'].get('active_snapshot_id')}@{report['standard'].get('active_version')}`\n"
    f"- preview: `{report['preview'].get('active_snapshot_id')}@{report['preview'].get('active_version')}`\n",
)
print("[release_audit_surface_guard] PASS")
PY
