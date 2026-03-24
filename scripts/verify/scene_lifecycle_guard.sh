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
from odoo.addons.smart_core.delivery.scene_snapshot_service import SceneSnapshotService

OUT_JSON = Path("/mnt/artifacts/backend/scene_lifecycle_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/scene_lifecycle_guard.md")
ALLOWED = {"draft", "ready", "beta", "stable", "deprecated"}


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "checked": []}
try:
    snapshot_service = SceneSnapshotService(env)
    promotion_service = ScenePromotionService(env)
    rows = snapshot_service.freeze_policy_surface(product_key="construction.standard", version="v1", channel="stable")
    for row in rows:
        if str(row.get("state") or "").strip() not in ALLOWED:
            raise RuntimeError(f"illegal state: {row.get('state')}")
    target = next((row for row in rows if str(row.get("scene_key") or "").strip() == "cost"), None)
    if not isinstance(target, dict):
        raise RuntimeError("cost snapshot missing")
    ready = promotion_service.promote_to_ready(int(target["id"]), state_reason="lifecycle_guard_ready")
    if str(ready.get("state") or "").strip() != "ready":
        raise RuntimeError("ready promotion failed")
    beta = promotion_service.promote_to_beta(int(target["id"]), state_reason="lifecycle_guard_beta")
    if str(beta.get("state") or "").strip() != "beta":
        raise RuntimeError("beta promotion failed")
    stable = promotion_service.promote_to_stable(int(target["id"]), replace_active=True, state_reason="lifecycle_guard_stable")
    if str(stable.get("state") or "").strip() != "stable" or stable.get("is_active") is not True:
        raise RuntimeError("stable promotion failed")
    deprecated = promotion_service.deprecate(int(target["id"]), state_reason="lifecycle_guard_deprecated")
    if str(deprecated.get("state") or "").strip() != "deprecated":
        raise RuntimeError("deprecate failed")
    if deprecated.get("is_active") is not False:
        raise RuntimeError("deprecated snapshot must be inactive")
    if not str(deprecated.get("deprecated_at") or "").strip():
        raise RuntimeError("deprecated_at missing")
    report["checked"].append(
        {
            "scene_key": deprecated.get("scene_key"),
            "state_path": ["draft", "ready", "beta", "stable", "deprecated"],
        }
    )
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Scene Lifecycle Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[scene_lifecycle_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Scene Lifecycle Guard\n\n"
    f"- status: `PASS`\n"
    f"- checked_count: `{len(report['checked'])}`\n",
)
print("[scene_lifecycle_guard] PASS")
PY
