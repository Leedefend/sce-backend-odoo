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

OUT_JSON = Path("/mnt/artifacts/backend/scene_promotion_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/scene_promotion_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "invalid_transition": "", "valid_path": []}
try:
    snapshot_service = SceneSnapshotService(env)
    promotion_service = ScenePromotionService(env)
    rows = snapshot_service.freeze_policy_surface(product_key="construction.standard", version="v1", channel="stable")
    target = next((row for row in rows if str(row.get("scene_key") or "").strip() == "payment"), None)
    if not isinstance(target, dict):
        raise RuntimeError("payment snapshot missing")

    try:
        promotion_service.promote_to_stable(int(target["id"]), state_reason="guard_invalid_direct_stable")
        raise RuntimeError("draft_to_stable_should_fail")
    except Exception as exc:
        message = str(exc)
        if "INVALID_STATE_TRANSITION" not in message:
            raise
        report["invalid_transition"] = message

    report["valid_path"].append(promotion_service.promote_to_ready(int(target["id"]), state_reason="guard_ready").get("state"))
    report["valid_path"].append(promotion_service.promote_to_beta(int(target["id"]), state_reason="guard_beta").get("state"))
    stable = promotion_service.promote_to_stable(int(target["id"]), replace_active=True, state_reason="guard_stable")
    report["valid_path"].append(stable.get("state"))
    if report["valid_path"] != ["ready", "beta", "stable"]:
        raise RuntimeError(f"valid path drift: {report['valid_path']}")
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Scene Promotion Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[scene_promotion_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Scene Promotion Guard\n\n"
    f"- status: `PASS`\n"
    f"- invalid_transition: `{report['invalid_transition']}`\n"
    f"- valid_path: `{', '.join(report['valid_path'])}`\n",
)
print("[scene_promotion_guard] PASS")
PY
