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

from odoo.addons.smart_core.delivery.scene_promotion_service import ScenePromotionService
from odoo.addons.smart_core.delivery.scene_replication_service import SceneReplicationService
from odoo.addons.smart_core.delivery.scene_snapshot_service import SceneSnapshotService

OUT_JSON = Path("/mnt/artifacts/backend/scene_active_uniqueness_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/scene_active_uniqueness_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "conflict_error": "", "final_active_stable_count": 0}
try:
    snapshot_service = SceneSnapshotService(env)
    promotion_service = ScenePromotionService(env)
    rows = snapshot_service.freeze_policy_surface(product_key="construction.standard", version="v1", channel="stable")
    base = next((row for row in rows if str(row.get("scene_key") or "").strip() == "project.management" and str(row.get("product_key") or "").strip() == "fr2"), None)
    if not isinstance(base, dict):
        raise RuntimeError("project.management stable base missing")
    promotion_service.promote_to_ready(int(base["id"]), state_reason="uniqueness_base_ready")
    promotion_service.promote_to_stable(int(base["id"]), replace_active=True, state_reason="uniqueness_base_stable")

    clone = SceneReplicationService(env).clone(
        source_scene_key="project.management",
        source_product_key="fr2",
        source_version="v1",
        source_channel="stable",
        target_version="v2",
        target_channel="beta",
        note="uniqueness guard beta clone",
    )
    promotion_service.promote_to_ready(int(clone["id"]), state_reason="uniqueness_clone_ready")
    promotion_service.promote_to_beta(int(clone["id"]), state_reason="uniqueness_clone_beta")
    try:
        promotion_service.promote_to_stable(int(clone["id"]), state_reason="uniqueness_conflict")
        raise RuntimeError("active_stable_conflict_should_fail")
    except Exception as exc:
        message = str(exc)
        if "ACTIVE_STABLE_CONFLICT" not in message:
            raise
        report["conflict_error"] = message

    promotion_service.promote_to_stable(int(clone["id"]), replace_active=True, state_reason="uniqueness_replace")
    active = snapshot_service.list_active_stable_snapshots(scene_key="project.management", product_key="fr2")
    report["final_active_stable_count"] = len(active)
    if len(active) != 1:
        raise RuntimeError(f"active stable uniqueness drift: {len(active)}")
    if str(active[0].get("version") or "").strip() != "v2":
        raise RuntimeError("active stable replacement drift")
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Scene Active Uniqueness Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[scene_active_uniqueness_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Scene Active Uniqueness Guard\n\n"
    f"- status: `PASS`\n"
    f"- conflict_error: `{report['conflict_error']}`\n"
    f"- final_active_stable_count: `{report['final_active_stable_count']}`\n",
)
print("[scene_active_uniqueness_guard] PASS")
PY
