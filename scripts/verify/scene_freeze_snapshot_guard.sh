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

from odoo.addons.smart_core.delivery.scene_snapshot_service import SceneSnapshotService

OUT_JSON = Path("/mnt/artifacts/backend/scene_freeze_snapshot_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/scene_freeze_snapshot_guard.md")
EXPECTED = [
    "projects.intake",
    "project.management",
    "cost",
    "payment",
    "settlement",
    "my_work.workspace",
]


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "product_key": "construction.standard", "version": "v1", "channel": "stable", "snapshots": []}
try:
    service = SceneSnapshotService(env)
    rows = service.freeze_policy_surface(product_key="construction.standard", version="v1", channel="stable")
    scene_keys = sorted(str(row.get("scene_key") or "").strip() for row in rows)
    if scene_keys != sorted(EXPECTED):
        raise RuntimeError(f"scene freeze keys drift: {scene_keys}")
    for row in rows:
        contract = row.get("contract_json") if isinstance(row.get("contract_json"), dict) else {}
        identity = contract.get("identity") if isinstance(contract.get("identity"), dict) else {}
        governance = contract.get("governance") if isinstance(contract.get("governance"), dict) else {}
        if str(contract.get("contract_version") or "").strip() != "scene_contract_standard_v1":
            raise RuntimeError(f"{row.get('scene_key')}: contract_version drift")
        if str(identity.get("version") or "").strip() != "v1":
            raise RuntimeError(f"{row.get('scene_key')}: identity.version drift")
        if governance.get("released") is not True:
            raise RuntimeError(f"{row.get('scene_key')}: governance.released must be true")
        if str(row.get("state") or "").strip() != "draft":
            raise RuntimeError(f"{row.get('scene_key')}: freeze snapshot must default to draft")
        if row.get("is_active") is not False:
            raise RuntimeError(f"{row.get('scene_key')}: draft freeze snapshot must default to inactive")
        report["snapshots"].append(
            {
                "scene_key": row.get("scene_key"),
                "product_key": row.get("product_key"),
                "version": row.get("version"),
                "channel": row.get("channel"),
                "state": row.get("state"),
                "is_active": row.get("is_active"),
                "snapshot_id": row.get("id"),
            }
        )
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Scene Freeze Snapshot Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[scene_freeze_snapshot_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Scene Freeze Snapshot Guard\n\n"
    f"- status: `PASS`\n"
    f"- snapshot_count: `{len(report['snapshots'])}`\n"
    f"- scenes: `{', '.join(sorted(item['scene_key'] for item in report['snapshots']))}`\n",
)
print("[scene_freeze_snapshot_guard] PASS")
PY
