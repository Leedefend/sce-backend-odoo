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

OUT_JSON = Path("/mnt/artifacts/backend/edition_access_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/edition_access_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "preview_pm": {}, "preview_finance": {}, "standard_finance": {}}
try:
    engine = DeliveryEngine(env)
    pm = engine.build(data={"role_surface": {"role_code": "pm"}, "scenes": [], "capabilities": []}, product_key="construction.preview", edition_key="preview", base_product_key="construction")
    finance = engine.build(data={"role_surface": {"role_code": "finance"}, "scenes": [], "capabilities": []}, product_key="construction.preview", edition_key="preview", base_product_key="construction")
    standard_finance = engine.build(data={"role_surface": {"role_code": "finance"}, "scenes": [], "capabilities": []}, product_key="construction.standard", edition_key="standard", base_product_key="construction")
    if str(pm.get("product_key") or "").strip() != "construction.preview":
        raise RuntimeError("pm should access preview edition")
    if str(finance.get("product_key") or "").strip() != "construction.standard":
        raise RuntimeError("finance should fallback to standard edition")
    if str(standard_finance.get("product_key") or "").strip() != "construction.standard":
        raise RuntimeError("finance standard access drift")
    finance_diag = finance.get("product_policy", {}).get("edition_diagnostics") if isinstance(finance.get("product_policy"), dict) else {}
    if str(finance_diag.get("fallback_reason") or "").strip() != "EDITION_ACCESS_DENIED":
        raise RuntimeError("preview finance fallback reason drift")
    report["preview_pm"] = pm.get("product_policy", {}).get("edition_diagnostics") if isinstance(pm.get("product_policy"), dict) else {}
    report["preview_finance"] = finance_diag
    report["standard_finance"] = standard_finance.get("product_policy", {}).get("edition_diagnostics") if isinstance(standard_finance.get("product_policy"), dict) else {}
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Edition Access Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[edition_access_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Edition Access Guard\n\n"
    f"- status: `PASS`\n"
    f"- finance_preview_fallback: `{report['preview_finance'].get('fallback_reason')}`\n",
)
print("[edition_access_guard] PASS")
PY
