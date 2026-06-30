# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/mnt") if Path("/mnt/scripts").exists() else Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "artifacts" / "backend" / "lifecycle_audit_export.json"

SCENE_KEYS = ["portal.lifecycle", "portal.capability_matrix"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_report(payload: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _capability_items(matrix: dict) -> list[dict]:
    sections = matrix.get("sections") if isinstance(matrix.get("sections"), list) else []
    out: list[dict] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        items = section.get("items") if isinstance(section.get("items"), list) else []
        for item in items:
            if isinstance(item, dict):
                row = dict(item)
                row["section_key"] = section.get("key")
                out.append(row)
    return out


def _scene_exports() -> list[dict]:
    Scene = env["sc.scene"].sudo()  # noqa: F821
    rows = []
    for scene_key in SCENE_KEYS:
        scene = Scene.search([("code", "=", scene_key)], limit=1)
        active_version = scene.active_version_id if scene else False
        rows.append(
            {
                "scene_key": scene_key,
                "exists": bool(scene),
                "scene_id": int(scene.id) if scene else 0,
                "active_version_id": int(active_version.id) if active_version else 0,
                "active_version_state": str(getattr(active_version, "state", "") or "") if active_version else "",
            }
        )
    return rows


def _matrix_meta_exists(lifecycle: dict) -> bool:
    matrix_meta = lifecycle.get("matrix_meta") if isinstance(lifecycle.get("matrix_meta"), dict) else {}
    path = str(matrix_meta.get("path") or "").strip()
    return bool(path) and Path(path).is_file()


errors: list[str] = []
try:
    from odoo.addons.smart_construction_portal.services.portal_contract_service import PortalContractService
    from odoo.addons.smart_construction_core.services.capability_matrix_service import CapabilityMatrixService

    lifecycle = PortalContractService(env).build_lifecycle_dashboard(  # noqa: F821
        route="/portal/lifecycle",
        trace_id="delivery-lifecycle-audit-export",
    )
    capability_matrix = CapabilityMatrixService(env).build_matrix()  # noqa: F821
except Exception as exc:
    lifecycle = {}
    capability_matrix = {}
    errors.append(f"service_export_failed:{type(exc).__name__}:{exc}")

scene_exports = _scene_exports()
capability_items = _capability_items(capability_matrix)
allowed_items = [item for item in capability_items if item.get("allowed") is True]
lifecycle_codes = lifecycle.get("capability_codes") if isinstance(lifecycle.get("capability_codes"), list) else []
lifecycle_states = lifecycle.get("lifecycle_states") if isinstance(lifecycle.get("lifecycle_states"), list) else []

if lifecycle.get("schema_version") != "portal-lifecycle-v1":
    errors.append("lifecycle_schema_version_mismatch")
if lifecycle.get("route") != "/portal/lifecycle":
    errors.append("lifecycle_route_mismatch")
if len(lifecycle_states) < 5:
    errors.append("lifecycle_states_too_few")
if len(lifecycle_codes) < 5:
    errors.append("lifecycle_capability_codes_too_few")
if not _matrix_meta_exists(lifecycle):
    errors.append("lifecycle_matrix_meta_path_missing")
if not capability_items:
    errors.append("capability_matrix_items_empty")
if not allowed_items:
    errors.append("capability_matrix_allowed_items_empty")
missing_scenes = [row["scene_key"] for row in scene_exports if not row["exists"]]
if missing_scenes:
    errors.append(f"missing_scenes:{','.join(missing_scenes)}")

payload = {
    "generated_at_utc": _utc_now(),
    "ok": not errors,
    "export": "lifecycle_audit_export",
    "db": env.cr.dbname,  # noqa: F821
    "company_id": int(env.company.id),  # noqa: F821
    "scenes": scene_exports,
    "lifecycle": {
        "schema_version": lifecycle.get("schema_version"),
        "contract_version": lifecycle.get("contract_version"),
        "route": lifecycle.get("route"),
        "subject": lifecycle.get("subject"),
        "trace_id": lifecycle.get("trace_id"),
        "lifecycle_states": lifecycle_states,
        "capability_codes": lifecycle_codes,
        "matrix_meta": lifecycle.get("matrix_meta") if isinstance(lifecycle.get("matrix_meta"), dict) else {},
        "layout": lifecycle.get("layout") if isinstance(lifecycle.get("layout"), dict) else {},
    },
    "capability_matrix": {
        "section_count": len(capability_matrix.get("sections") if isinstance(capability_matrix.get("sections"), list) else []),
        "item_count": len(capability_items),
        "allowed_item_count": len(allowed_items),
        "scene_keys": sorted({str(item.get("scene_key") or "") for item in capability_items if str(item.get("scene_key") or "").strip()}),
    },
    "errors": errors,
    "report_path": str(REPORT_PATH.relative_to(ROOT)),
}
_write_report(payload)
print(REPORT_PATH)
print("[lifecycle_audit_export] PASS" if payload["ok"] else "[lifecycle_audit_export] FAIL")
if errors:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(1)
