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

from odoo.addons.smart_core.delivery.product_edition_promotion_service import ProductEditionPromotionService
from odoo.addons.smart_core.delivery.scene_promotion_service import ScenePromotionService
from odoo.addons.smart_core.delivery.scene_snapshot_service import SceneSnapshotService

OUT_JSON = Path("/mnt/artifacts/backend/edition_promotion_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/edition_promotion_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "promotion": {}, "rollback": {}}
try:
    snapshot_service = SceneSnapshotService(env)
    scene_promotion = ScenePromotionService(env)
    frozen = snapshot_service.freeze_policy_surface(product_key="construction.standard", version="v1", channel="stable")
    base_snapshot = next(
        (
            row for row in frozen
            if str(row.get("scene_key") or "").strip() == "project.management"
            and str(row.get("product_key") or "").strip() == "fr2"
        ),
        None,
    )
    if not isinstance(base_snapshot, dict):
        raise RuntimeError("base project.management snapshot missing")
    scene_promotion.promote_to_ready(int(base_snapshot["id"]), state_reason="edition_promotion_guard_ready")
    scene_promotion.promote_to_stable(int(base_snapshot["id"]), replace_active=True, state_reason="edition_promotion_guard_stable")

    policy_model = env["sc.product.policy"].sudo()
    template = policy_model.search([("product_key", "=", "construction.standard")], limit=1)
    if not template:
        raise RuntimeError("construction.standard template missing")
    base_product_key = "construction_guard"
    old_stable_key = "construction_guard.standard"
    preview_key = "construction_guard.preview"
    policy_model.search([("base_product_key", "=", base_product_key)]).unlink()
    scene_entries = [
        row for row in (template.scene_entries or [])
        if isinstance(row, dict) and str(row.get("scene_key") or "").strip() == "project.management"
    ]
    capability_entries = [
        row for row in (template.capability_entries or [])
        if isinstance(row, dict) and str(row.get("target_scene_key") or "").strip() == "project.management"
    ]
    bindings = {"project.management": {"version": "v1", "channel": "stable"}}
    menu_groups = template.menu_groups if isinstance(template.menu_groups, list) and template.menu_groups else [{"group_key": "guard", "group_label": "Guard", "menus": []}]
    policy_model.create({
        "product_key": old_stable_key,
        "base_product_key": base_product_key,
        "edition_key": "standard",
        "state": "stable",
        "access_level": "public",
        "allowed_role_codes": [],
        "label": "Construction Guard Standard",
        "version": "v1",
        "menu_groups": menu_groups,
        "scene_entries": scene_entries,
        "capability_entries": capability_entries,
        "scene_version_bindings": bindings,
    })
    policy_model.create({
        "product_key": preview_key,
        "base_product_key": base_product_key,
        "edition_key": "preview",
        "state": "draft",
        "access_level": "role_restricted",
        "allowed_role_codes": ["pm"],
        "label": "Construction Guard Preview",
        "version": "v2",
        "menu_groups": menu_groups,
        "scene_entries": scene_entries,
        "capability_entries": capability_entries,
        "scene_version_bindings": bindings,
    })
    promotion = ProductEditionPromotionService(env)
    invalid_transition = False
    try:
        promotion.promote_to_stable(preview_key, state_reason="invalid_direct_stable")
    except Exception:
        invalid_transition = True
    if not invalid_transition:
        raise RuntimeError("draft_to_stable should fail")
    promotion.promote_to_ready(preview_key, state_reason="guard_ready")
    preview = promotion.promote_to_preview(preview_key, state_reason="guard_preview")
    stable = promotion.promote_to_stable(preview_key, replace_stable=True, state_reason="guard_stable")
    if str(preview.get("state") or "").strip() != "preview":
        raise RuntimeError("preview promotion drift")
    if str(stable.get("state") or "").strip() != "stable":
        raise RuntimeError("stable promotion drift")
    old_stable = policy_model.search([("product_key", "=", old_stable_key)], limit=1)
    if str(old_stable.state or "").strip() != "deprecated":
        raise RuntimeError("old stable should deprecate on replace")
    rollback = promotion.rollback_to_previous_stable(
        base_product_key=base_product_key,
        current_product_key=preview_key,
        state_reason="guard_rollback",
        promotion_note="rollback to previous stable edition",
    )
    rolled_preview = policy_model.search([("product_key", "=", preview_key)], limit=1)
    if str(rollback.get("product_key") or "").strip() != old_stable_key:
        raise RuntimeError("rollback target drift")
    if str(rolled_preview.state or "").strip() != "deprecated":
        raise RuntimeError("preview should deprecate after rollback")
    report["promotion"] = stable
    report["rollback"] = rollback
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Edition Promotion Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[edition_promotion_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Edition Promotion Guard\n\n"
    f"- status: `PASS`\n"
    f"- promoted: `{report['promotion'].get('product_key')}@{report['promotion'].get('state')}`\n"
    f"- rollback: `{report['rollback'].get('product_key')}@{report['rollback'].get('state')}`\n",
)
print("[edition_promotion_guard] PASS")
PY
