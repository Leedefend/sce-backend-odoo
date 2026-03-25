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

from odoo.addons.smart_core.delivery.release_approval_policy_service import ReleaseApprovalPolicyService

OUT_JSON = Path("/mnt/artifacts/backend/release_policy_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/release_policy_guard.md")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


report = {"status": "PASS", "preview_promote": {}, "standard_promote": {}, "standard_rollback": {}}
try:
    service = ReleaseApprovalPolicyService(env)
    preview_promote = service.resolve_policy(action_type="promote_snapshot", product_key="construction.preview")
    standard_promote = service.resolve_policy(action_type="promote_snapshot", product_key="construction.standard")
    standard_rollback = service.resolve_policy(action_type="rollback_snapshot", product_key="construction.standard")

    if preview_promote.get("approval_required") is not False:
        raise RuntimeError("preview promote should not require approval")
    if "pm" not in (preview_promote.get("allowed_executor_role_codes") or []):
        raise RuntimeError("preview promote should allow pm execution")
    if standard_promote.get("approval_required") is not True:
        raise RuntimeError("standard promote should require approval")
    if "pm" not in (standard_promote.get("allowed_executor_role_codes") or []):
        raise RuntimeError("standard promote should allow pm request")
    if "admin" not in (standard_promote.get("required_approver_role_codes") or []):
        raise RuntimeError("standard promote should require admin/executive approver")
    if standard_rollback.get("approval_required") is not True:
        raise RuntimeError("rollback should require approval")
    if "pm" in (standard_rollback.get("allowed_executor_role_codes") or []):
        raise RuntimeError("rollback should not allow pm execution")

    report["preview_promote"] = preview_promote
    report["standard_promote"] = standard_promote
    report["standard_rollback"] = standard_rollback
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)
    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Release Policy Guard\n\n"
        f"- status: `FAIL`\n"
        f"- error: `{str(exc)}`\n",
    )
    print("[release_policy_guard] FAIL")
    print(f" - {exc}")
    raise SystemExit(1)

write_json(OUT_JSON, report)
write(
    OUT_MD,
    "# Release Policy Guard\n\n"
    f"- status: `PASS`\n"
    f"- preview policy: `{report['preview_promote'].get('policy_key')}`\n"
    f"- standard promote policy: `{report['standard_promote'].get('policy_key')}`\n"
    f"- standard rollback policy: `{report['standard_rollback'].get('policy_key')}`\n",
)
print("[release_policy_guard] PASS")
PY
