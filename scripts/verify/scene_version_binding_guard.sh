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

OUT_JSON = Path("/mnt/artifacts/backend/scene_version_binding_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/scene_version_binding_guard.md")
PREVIEW_KEY = "construction.preview"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def clone_policy_payload(source: dict) -> dict:
    return {
        "product_key": PREVIEW_KEY,
        "label": "Construction Preview",
        "version": "v1",
        "menu_groups": source.get("menu_groups") if isinstance(source.get("menu_groups"), list) else [],
        "scene_entries": source.get("scenes") if isinstance(source.get("scenes"), list) else [],
        "capability_entries": source.get("capabilities") if isinstance(source.get("capabilities"), list) else [],
        "scene_version_bindings": dict(source.get("scene_version_bindings") or {}),
    }


report = {"status": "PASS", "preview_policy": PREVIEW_KEY, "binding": {}, "resolved_scene": {}}
try:
    snapshot_service = SceneSnapshotService(env)
    promotion_service = ScenePromotionService(env)
    frozen = snapshot_service.freeze_policy_surface(product_key="construction.standard", version="v1", channel="stable")
    base_snapshot = next((row for row in frozen if str(row.get("scene_key") or "").strip() == "project.management" and str(row.get("product_key") or "").strip() == "fr2"), None)
    if not isinstance(base_snapshot, dict):
        raise RuntimeError("base snapshot missing for project.management")
    promotion_service.promote_to_ready(int(base_snapshot["id"]), state_reason="guard_prepare_ready")
    promotion_service.promote_to_stable(int(base_snapshot["id"]), replace_active=True, state_reason="guard_prepare_stable")
    beta_clone = SceneReplicationService(env).clone(
        source_scene_key="project.management",
        source_product_key="fr2",
        source_version="v1",
        source_channel="stable",
        target_version="v2",
        target_channel="beta",
        target_label="FR-2 项目推进 Beta",
        note="version binding guard beta clone",
    )
    promotion_service.promote_to_ready(int(beta_clone["id"]), state_reason="guard_preview_ready")
    promotion_service.promote_to_beta(int(beta_clone["id"]), state_reason="guard_preview_beta")
    promotion_service.promote_to_stable(int(beta_clone["id"]), replace_active=True, state_reason="guard_preview_stable")

    source_policy = env["sc.product.policy"].sudo().search([("product_key", "=", "construction.standard")], limit=1)
    if not source_policy:
        raise RuntimeError("construction.standard policy missing")
    payload = clone_policy_payload(source_policy.to_runtime_dict())
    bindings = dict(payload.get("scene_version_bindings") or {})
    bindings["project.management"] = {"version": "v2", "channel": "beta"}
    payload["scene_version_bindings"] = bindings

    preview = env["sc.product.policy"].sudo().search([("product_key", "=", PREVIEW_KEY)], limit=1)
    values = {
        "label": payload["label"],
        "version": payload["version"],
        "menu_groups": payload["menu_groups"],
        "scene_entries": payload["scene_entries"],
        "capability_entries": payload["capability_entries"],
        "scene_version_bindings": payload["scene_version_bindings"],
        "active": True,
    }
    if preview:
        preview.write(values)
    else:
        values["product_key"] = PREVIEW_KEY
        preview = env["sc.product.policy"].sudo().create(values)

    delivery = DeliveryEngine(env).build(
        data={"role_surface": {"role_code": "pm"}, "scenes": [], "capabilities": []},
        product_key=PREVIEW_KEY,
    )
    scenes = delivery.get("scenes") if isinstance(delivery.get("scenes"), list) else []
    project_management = next((row for row in scenes if isinstance(row, dict) and str(row.get("scene_key") or "").strip() == "project.management"), None)
    if not isinstance(project_management, dict):
        raise RuntimeError("preview delivery missing project.management")
    binding = project_management.get("scene_asset_binding") if isinstance(project_management.get("scene_asset_binding"), dict) else {}
    contract = project_management.get("scene_contract_standard_v1") if isinstance(project_management.get("scene_contract_standard_v1"), dict) else {}
    identity = contract.get("identity") if isinstance(contract.get("identity"), dict) else {}
    if binding.get("resolved") is not True:
        raise RuntimeError("preview binding unresolved")
    if str(binding.get("version") or "").strip() != "v2":
        raise RuntimeError("preview binding version drift")
    if str(binding.get("channel") or "").strip() != "beta":
        raise RuntimeError("preview binding channel drift")
    if binding.get("binding_allowed") is not True:
        raise RuntimeError("preview binding_allowed drift")
    if str(binding.get("snapshot_state") or "").strip() != "stable":
        raise RuntimeError("preview snapshot_state drift")
    if str(identity.get("version") or "").strip() != "v2":
        raise RuntimeError("preview scene contract version drift")
    report["binding"] = binding
    report["resolved_scene"] = {
        "scene_key": project_management.get("scene_key"),
        "product_key": identity.get("product_key"),
        "version": identity.get("version"),
        "snapshot_id": binding.get("snapshot_id"),
    }
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Scene Version Binding Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[scene_version_binding_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Scene Version Binding Guard\n\n"
    f"- status: `PASS`\n"
    f"- preview_policy: `{PREVIEW_KEY}`\n"
    f"- resolved_scene: `{report['resolved_scene'].get('scene_key')}@{report['resolved_scene'].get('version')}`\n",
)
print("[scene_version_binding_guard] PASS")
PY
