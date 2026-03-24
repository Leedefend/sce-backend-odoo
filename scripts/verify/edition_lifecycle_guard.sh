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

OUT_JSON = Path("/mnt/artifacts/backend/edition_lifecycle_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/edition_lifecycle_guard.md")


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
        raise RuntimeError(f"edition lifecycle keys drift: {sorted(by_key.keys())}")
    standard = by_key["construction.standard"]
    preview = by_key["construction.preview"]
    if str(standard.state or "").strip() != "stable":
        raise RuntimeError("construction.standard must be stable")
    if str(standard.access_level or "").strip() != "public":
        raise RuntimeError("construction.standard access_level drift")
    if str(preview.state or "").strip() != "preview":
        raise RuntimeError("construction.preview must be preview")
    if str(preview.access_level or "").strip() != "role_restricted":
        raise RuntimeError("construction.preview access_level drift")
    allowed_role_codes = preview.allowed_role_codes if isinstance(preview.allowed_role_codes, list) else []
    if "pm" not in allowed_role_codes:
        raise RuntimeError("construction.preview pm access missing")
    stable_rows = env["sc.product.policy"].sudo().search([
        ("base_product_key", "=", "construction"),
        ("state", "=", "stable"),
        ("active", "=", True),
    ])
    if len(stable_rows) != 1:
        raise RuntimeError(f"active stable edition uniqueness drift: {len(stable_rows)}")
    report["policies"] = {
        "construction.standard": {
            "state": standard.state,
            "access_level": standard.access_level,
        },
        "construction.preview": {
            "state": preview.state,
            "access_level": preview.access_level,
            "allowed_role_codes": allowed_role_codes,
        },
    }
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Edition Lifecycle Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[edition_lifecycle_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Edition Lifecycle Guard\n\n"
    f"- status: `PASS`\n"
    f"- standard_state: `{report['policies']['construction.standard']['state']}`\n"
    f"- preview_state: `{report['policies']['construction.preview']['state']}`\n",
)
print("[edition_lifecycle_guard] PASS")
PY
