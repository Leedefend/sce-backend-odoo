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

OUT_JSON = Path("/mnt/artifacts/backend/edition_release_snapshot_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/edition_release_snapshot_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "standard": {}, "preview": {}}
try:
    service = EditionReleaseSnapshotService(env)
    service.freeze_release_surface(product_key="construction.standard", version="freeze-standard-v1", role_code="pm")
    service.freeze_release_surface(product_key="construction.preview", version="freeze-preview-v1", role_code="pm")
    standard = service.resolve_active_snapshot(product_key="construction.standard")
    preview = service.resolve_active_snapshot(product_key="construction.preview")
    for label, row, expected_state in (
        ("standard", standard, "stable"),
        ("preview", preview, "preview"),
    ):
        if not isinstance(row, dict) or not row:
            raise RuntimeError(f"{label}: active snapshot missing")
        if row.get("is_active") is not True:
            raise RuntimeError(f"{label}: active snapshot drift")
        snapshot = row.get("snapshot_json") if isinstance(row.get("snapshot_json"), dict) else {}
        policy = snapshot.get("policy") if isinstance(snapshot.get("policy"), dict) else {}
        runtime_meta = snapshot.get("runtime_meta") if isinstance(snapshot.get("runtime_meta"), dict) else {}
        effective = runtime_meta.get("effective") if isinstance(runtime_meta.get("effective"), dict) else {}
        if int(row.get("source_policy_id") or 0) <= 0:
            raise RuntimeError(f"{label}: source policy missing")
        if str(policy.get("state") or "").strip() != expected_state:
            raise RuntimeError(f"{label}: policy state drift")
        if str(effective.get("product_key") or "").strip() != str(row.get("product_key") or "").strip():
            raise RuntimeError(f"{label}: effective product drift")
        report[label] = {
            "snapshot_id": row.get("id"),
            "product_key": row.get("product_key"),
            "version": row.get("version"),
            "policy_state": policy.get("state"),
            "effective_product_key": effective.get("product_key"),
            "rollback_target_snapshot_id": row.get("rollback_target_snapshot_id"),
        }
    env.cr.commit()
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Edition Release Snapshot Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[edition_release_snapshot_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Edition Release Snapshot Guard\n\n"
    f"- status: `PASS`\n"
    f"- standard: `{report['standard'].get('product_key')}@{report['standard'].get('version')}`\n"
    f"- preview: `{report['preview'].get('product_key')}@{report['preview'].get('version')}`\n",
)
print("[edition_release_snapshot_guard] PASS")
PY
