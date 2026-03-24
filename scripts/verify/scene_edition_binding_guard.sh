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

from odoo.addons.smart_core.delivery.delivery_engine import DeliveryEngine
from odoo.addons.smart_core.delivery.scene_promotion_service import ScenePromotionService
from odoo.addons.smart_core.delivery.scene_replication_service import SceneReplicationService
from odoo.addons.smart_core.delivery.scene_snapshot_service import SceneSnapshotService

OUT_JSON = Path("/mnt/artifacts/backend/scene_edition_binding_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/scene_edition_binding_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def scene_index(rows):
    return {
        str(row.get("scene_key") or "").strip(): row
        for row in rows
        if isinstance(row, dict) and str(row.get("scene_key") or "").strip()
    }


report = {"status": "PASS", "standard": {}, "preview": {}}
try:
    snapshot_service = SceneSnapshotService(env)
    promotion_service = ScenePromotionService(env)
    frozen = snapshot_service.freeze_policy_surface(product_key="construction.standard", version="v1", channel="stable")
    base = next((row for row in frozen if str(row.get("scene_key") or "").strip() == "project.management" and str(row.get("product_key") or "").strip() == "fr2"), None)
    if not isinstance(base, dict):
        raise RuntimeError("base standard snapshot missing")
    promotion_service.promote_to_ready(int(base["id"]), state_reason="edition_guard_standard_ready")
    promotion_service.promote_to_stable(int(base["id"]), replace_active=True, state_reason="edition_guard_standard_stable")

    preview_clone = SceneReplicationService(env).clone(
        source_scene_key="project.management",
        source_product_key="fr2",
        source_version="v1",
        source_channel="stable",
        target_version="v2",
        target_channel="beta",
        target_label="FR-2 项目推进 Preview",
        note="edition binding guard preview clone",
    )
    promotion_service.promote_to_ready(int(preview_clone["id"]), state_reason="edition_guard_preview_ready")
    promotion_service.promote_to_beta(int(preview_clone["id"]), state_reason="edition_guard_preview_beta")
    promotion_service.promote_to_stable(int(preview_clone["id"]), replace_active=True, state_reason="edition_guard_preview_stable")

    preview_policy = env["sc.product.policy"].sudo().search([("product_key", "=", "construction.preview")], limit=1)
    if not preview_policy:
        raise RuntimeError("construction.preview policy missing")
    preview_bindings = dict(preview_policy.scene_version_bindings or {})
    preview_bindings["project.management"] = {"version": "v2", "channel": "beta"}
    preview_policy.write({"scene_version_bindings": preview_bindings})

    standard_delivery = DeliveryEngine(env).build(data={"role_surface": {"role_code": "pm"}, "scenes": [], "capabilities": []}, product_key="construction.standard", edition_key="standard", base_product_key="construction")
    preview_delivery = DeliveryEngine(env).build(data={"role_surface": {"role_code": "pm"}, "scenes": [], "capabilities": []}, product_key="construction.preview", edition_key="preview", base_product_key="construction")

    standard_scene = scene_index(standard_delivery.get("scenes") or {}).get("project.management")
    preview_scene = scene_index(preview_delivery.get("scenes") or {}).get("project.management")
    if not isinstance(standard_scene, dict) or not isinstance(preview_scene, dict):
        raise RuntimeError("project.management missing in edition deliveries")

    standard_binding = standard_scene.get("scene_asset_binding") if isinstance(standard_scene.get("scene_asset_binding"), dict) else {}
    preview_binding = preview_scene.get("scene_asset_binding") if isinstance(preview_scene.get("scene_asset_binding"), dict) else {}
    if str(standard_binding.get("version") or "").strip() != "v1":
        raise RuntimeError("standard binding version drift")
    if str(preview_binding.get("version") or "").strip() != "v2":
        raise RuntimeError("preview binding version drift")
    if str(preview_binding.get("snapshot_state") or "").strip() != "stable":
        raise RuntimeError("preview binding stable state missing")
    report["standard"] = standard_binding
    report["preview"] = preview_binding
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Scene Edition Binding Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[scene_edition_binding_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Scene Edition Binding Guard\n\n"
    f"- status: `PASS`\n"
    f"- standard_version: `{report['standard'].get('version')}`\n"
    f"- preview_version: `{report['preview'].get('version')}`\n",
)
print("[scene_edition_binding_guard] PASS")
PY
