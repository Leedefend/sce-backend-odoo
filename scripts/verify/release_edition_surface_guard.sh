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

OUT_JSON = Path("/mnt/artifacts/backend/release_edition_surface_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/release_edition_surface_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "standard": {}, "preview": {}}
try:
    engine = DeliveryEngine(env)
    standard = engine.build(data={"role_surface": {"role_code": "pm"}, "scenes": [], "capabilities": []}, product_key="construction.standard", edition_key="standard", base_product_key="construction")
    preview = engine.build(data={"role_surface": {"role_code": "pm"}, "scenes": [], "capabilities": []}, product_key="construction.preview", edition_key="preview", base_product_key="construction")
    if str(standard.get("product_key") or "").strip() != "construction.standard":
        raise RuntimeError("standard product_key drift")
    if str(preview.get("product_key") or "").strip() != "construction.preview":
        raise RuntimeError("preview product_key drift")
    if str(standard.get("edition_key") or "").strip() != "standard":
        raise RuntimeError("standard edition_key drift")
    if str(preview.get("edition_key") or "").strip() != "preview":
        raise RuntimeError("preview edition_key drift")
    if str(standard.get("base_product_key") or "").strip() != "construction":
        raise RuntimeError("standard base_product_key drift")
    if str(preview.get("base_product_key") or "").strip() != "construction":
        raise RuntimeError("preview base_product_key drift")
    report["standard"] = {
        "product_key": standard.get("product_key"),
        "edition_key": standard.get("edition_key"),
        "scene_count": len(standard.get("scenes") or []),
    }
    report["preview"] = {
        "product_key": preview.get("product_key"),
        "edition_key": preview.get("edition_key"),
        "scene_count": len(preview.get("scenes") or []),
    }
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Release Edition Surface Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[release_edition_surface_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Release Edition Surface Guard\n\n"
    f"- status: `PASS`\n"
    f"- standard: `{report['standard'].get('product_key')}@{report['standard'].get('edition_key')}`\n"
    f"- preview: `{report['preview'].get('product_key')}@{report['preview'].get('edition_key')}`\n",
)
print("[release_edition_surface_guard] PASS")
PY
