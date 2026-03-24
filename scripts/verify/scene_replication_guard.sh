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

from odoo.addons.smart_core.delivery.scene_replication_service import SceneReplicationService
from odoo.addons.smart_core.delivery.scene_snapshot_service import SceneSnapshotService

OUT_JSON = Path("/mnt/artifacts/backend/scene_replication_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/scene_replication_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "source": {}, "clone": {}}
try:
    snapshot_service = SceneSnapshotService(env)
    snapshot_service.freeze_policy_surface(product_key="construction.standard", version="v1", channel="stable")
    service = SceneReplicationService(env)
    clone = service.clone(
        source_scene_key="project.management",
        source_product_key="fr2",
        source_version="v1",
        source_channel="stable",
        target_version="v2",
        target_channel="beta",
        target_label="FR-2 项目推进 Beta",
        note="replication guard beta clone",
    )
    contract = clone.get("contract_json") if isinstance(clone.get("contract_json"), dict) else {}
    identity = contract.get("identity") if isinstance(contract.get("identity"), dict) else {}
    if str(identity.get("scene_key") or "").strip() != "project.management":
        raise RuntimeError("clone scene_key drift")
    if str(identity.get("product_key") or "").strip() != "fr2":
        raise RuntimeError("clone product_key drift")
    if str(identity.get("version") or "").strip() != "v2":
        raise RuntimeError("clone version drift")
    if str(clone.get("channel") or "").strip() != "beta":
        raise RuntimeError("clone channel drift")
    if int(clone.get("cloned_from_snapshot_id") or 0) <= 0:
        raise RuntimeError("clone missing cloned_from_snapshot_id")
    if str(clone.get("state") or "").strip() != "draft":
        raise RuntimeError("replicated snapshot must default to draft")
    if clone.get("is_active") is not False:
        raise RuntimeError("replicated snapshot must default to inactive")
    report["clone"] = {
        "scene_key": clone.get("scene_key"),
        "product_key": clone.get("product_key"),
        "version": clone.get("version"),
        "channel": clone.get("channel"),
        "state": clone.get("state"),
        "snapshot_id": clone.get("id"),
        "cloned_from_snapshot_id": clone.get("cloned_from_snapshot_id"),
    }
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Scene Replication Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[scene_replication_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Scene Replication Guard\n\n"
    f"- status: `PASS`\n"
    f"- clone: `{report['clone'].get('scene_key')}@{report['clone'].get('version')}:{report['clone'].get('channel')}`\n",
)
print("[scene_replication_guard] PASS")
PY
