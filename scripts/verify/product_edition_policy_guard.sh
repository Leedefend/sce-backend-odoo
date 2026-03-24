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

OUT_JSON = Path("/mnt/artifacts/backend/product_edition_policy_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/product_edition_policy_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "policies": {}}
try:
    keys = ["construction.standard", "construction.preview"]
    rows = env["sc.product.policy"].sudo().search([("product_key", "in", keys), ("active", "=", True)])
    by_key = {str(row.product_key or "").strip(): row for row in rows}
    if sorted(by_key.keys()) != sorted(keys):
        raise RuntimeError(f"edition policy keys drift: {sorted(by_key.keys())}")
    seen_pairs = set()
    for key in keys:
        row = by_key[key]
        base_product_key = str(row.base_product_key or "").strip()
        edition_key = str(row.edition_key or "").strip()
        if not base_product_key:
            raise RuntimeError(f"{key}: base_product_key missing")
        if not edition_key:
            raise RuntimeError(f"{key}: edition_key missing")
        pair = (base_product_key, edition_key)
        if pair in seen_pairs:
            raise RuntimeError(f"duplicate edition pair: {pair}")
        seen_pairs.add(pair)
        report["policies"][key] = {
            "base_product_key": base_product_key,
            "edition_key": edition_key,
            "scene_count": len(row.scene_entries or []),
            "binding_count": len((row.scene_version_bindings or {}).keys()) if isinstance(row.scene_version_bindings, dict) else 0,
        }
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Product Edition Policy Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[product_edition_policy_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Product Edition Policy Guard\n\n"
    f"- status: `PASS`\n"
    f"- policy_keys: `{', '.join(sorted(report['policies'].keys()))}`\n",
)
print("[product_edition_policy_guard] PASS")
PY
