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

from odoo.addons.smart_core.delivery.edition_release_snapshot_service import (
    FREEZE_SURFACE_CONTRACT_VERSION,
    EditionReleaseSnapshotService,
)

OUT_JSON = Path("/mnt/artifacts/backend/edition_freeze_surface_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/edition_freeze_surface_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "standard": {}, "preview": {}}
try:
    service = EditionReleaseSnapshotService(env)
    standard = service.freeze_release_surface(
        product_key="construction.standard",
        version="freeze-standard-v1",
        role_code="pm",
        note="edition_freeze_surface_guard standard freeze",
    )
    preview = service.freeze_release_surface(
        product_key="construction.preview",
        version="freeze-preview-v1",
        role_code="pm",
        note="edition_freeze_surface_guard preview freeze",
    )
    for label, row, expected_edition in (
        ("standard", standard, "standard"),
        ("preview", preview, "preview"),
    ):
        snapshot = row.get("snapshot_json") if isinstance(row.get("snapshot_json"), dict) else {}
        identity = snapshot.get("identity") if isinstance(snapshot.get("identity"), dict) else {}
        runtime_meta = snapshot.get("runtime_meta") if isinstance(snapshot.get("runtime_meta"), dict) else {}
        requested = runtime_meta.get("requested") if isinstance(runtime_meta.get("requested"), dict) else {}
        effective = runtime_meta.get("effective") if isinstance(runtime_meta.get("effective"), dict) else {}
        if str(snapshot.get("contract_version") or "").strip() != FREEZE_SURFACE_CONTRACT_VERSION:
            raise RuntimeError(f"{label}: freeze contract_version drift")
        if str(identity.get("edition_key") or "").strip() != expected_edition:
            raise RuntimeError(f"{label}: identity edition drift")
        if str(effective.get("edition_key") or "").strip() != expected_edition:
            raise RuntimeError(f"{label}: runtime effective edition drift")
        if not isinstance(snapshot.get("nav"), list) or not snapshot.get("nav"):
            raise RuntimeError(f"{label}: nav missing")
        if not isinstance(snapshot.get("capabilities"), list) or not snapshot.get("capabilities"):
            raise RuntimeError(f"{label}: capabilities missing")
        if not isinstance(snapshot.get("scenes"), list) or len(snapshot.get("scenes")) < 6:
            raise RuntimeError(f"{label}: scenes missing")
        bindings = snapshot.get("scene_version_bindings") if isinstance(snapshot.get("scene_version_bindings"), dict) else {}
        if len(bindings) != 6:
            raise RuntimeError(f"{label}: scene bindings drift")
        report[label] = {
            "snapshot_id": row.get("id"),
            "product_key": row.get("product_key"),
            "version": row.get("version"),
            "requested_edition_key": requested.get("edition_key"),
            "effective_edition_key": effective.get("edition_key"),
            "scene_binding_count": len(bindings),
        }
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Edition Freeze Surface Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[edition_freeze_surface_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Edition Freeze Surface Guard\n\n"
    f"- status: `PASS`\n"
    f"- standard: `{report['standard'].get('product_key')}@{report['standard'].get('version')}`\n"
    f"- preview: `{report['preview'].get('product_key')}@{report['preview'].get('version')}`\n",
)
print("[edition_freeze_surface_guard] PASS")
PY
