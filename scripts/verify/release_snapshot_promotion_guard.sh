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

from odoo.addons.smart_core.delivery.edition_release_snapshot_promotion_service import (
    EditionReleaseSnapshotPromotionService,
)
from odoo.addons.smart_core.delivery.edition_release_snapshot_service import EditionReleaseSnapshotService

OUT_JSON = Path("/mnt/artifacts/backend/release_snapshot_promotion_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/release_snapshot_promotion_guard.md")
PRODUCT_KEY = "construction.preview"
VERSION = "snapshot-promotion-guard-v1"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "approved": {}, "released": {}, "illegal_transition_error": ""}
try:
    service = EditionReleaseSnapshotService(env)
    promotion = EditionReleaseSnapshotPromotionService(env)
    approved = service.freeze_release_surface(
        product_key=PRODUCT_KEY,
        version=VERSION,
        role_code="pm",
        note="release_snapshot_promotion_guard freeze",
        replace_active=False,
    )
    if str(approved.get("state") or "").strip() != "approved":
        raise RuntimeError("freeze result is not approved candidate lineage")
    try:
        promotion.supersede(
            int(approved.get("id") or 0),
            state_reason="illegal_jump_probe",
            promotion_note="should fail",
        )
        raise RuntimeError("illegal candidate->superseded transition unexpectedly succeeded")
    except ValueError as exc:
        report["illegal_transition_error"] = str(exc)
        if "INVALID_RELEASE_SNAPSHOT_TRANSITION" not in str(exc):
            raise
    released = promotion.promote_to_released(
        int(approved.get("id") or 0),
        replace_active=True,
        state_reason="promotion_guard_release",
        promotion_note="released by promotion guard",
    )
    if str(released.get("state") or "").strip() != "released":
        raise RuntimeError("promotion did not reach released state")
    if released.get("is_active") is not True:
        raise RuntimeError("released snapshot is not active")
    report["approved"] = {
        "snapshot_id": approved.get("id"),
        "product_key": approved.get("product_key"),
        "version": approved.get("version"),
        "state": approved.get("state"),
    }
    report["released"] = {
        "snapshot_id": released.get("id"),
        "product_key": released.get("product_key"),
        "version": released.get("version"),
        "state": released.get("state"),
        "is_active": released.get("is_active"),
    }
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Release Snapshot Promotion Guard\n\n"
        "- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[release_snapshot_promotion_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Release Snapshot Promotion Guard\n\n"
    "- status: `PASS`\n"
    f"- approved: `{report['approved'].get('product_key')}@{report['approved'].get('version')}`\n"
    f"- released: `{report['released'].get('product_key')}@{report['released'].get('version')}`\n"
    f"- illegal_transition_error: `{report['illegal_transition_error']}`\n",
)
print("[release_snapshot_promotion_guard] PASS")
PY
