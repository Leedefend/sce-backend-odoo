#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HOME = ROOT / "frontend/apps/web/src/views/HomeView.vue"
RUNTIME = ROOT / "frontend/apps/web/src/composables/shared-surface/useContractRoleHome.ts"
REPORT_JSON = ROOT / "artifacts/backend/frontend_home_suggestion_semantics_report.json"
REPORT_MD = ROOT / "docs/ops/audit/frontend_home_suggestion_semantics_report.md"


def main() -> int:
    home = HOME.read_text(encoding="utf-8", errors="ignore") if HOME.is_file() else ""
    runtime = RUNTIME.read_text(encoding="utf-8", errors="ignore") if RUNTIME.is_file() else ""
    required_home = ["<ContractRoleHome />", "components/role-home/ContractRoleHome.vue"]
    required_runtime = [
        "fetchMyWorkSummary(",
        "result.product_workspace",
        "topNodes(session.menuTree)",
        "session.activityPages",
        "isCurrentContextEpoch(requestEpoch)",
    ]
    forbidden = ["session.workspaceHome", "keywordList(", "role ===", "role_code ===", "listRecords("]
    errors = [f"HomeView missing token: {token}" for token in required_home if token not in home]
    errors += [f"runtime missing token: {token}" for token in required_runtime if token not in runtime]
    errors += [f"runtime forbidden token: {token}" for token in forbidden if token in runtime]
    payload = {
        "ok": not errors,
        "contract_boundary": "page_identity_plus_authoritative_my_work_navigation_activity",
        "errors": errors,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(
        "# Frontend Home Contract Boundary Report\n\n"
        f"- ok: `{payload['ok']}`\n"
        f"- contract_boundary: `{payload['contract_boundary']}`\n"
        f"- error_count: `{len(errors)}`\n",
        encoding="utf-8",
    )
    if errors:
        print("[frontend_home_contract_boundary_guard] FAIL")
        for error in errors:
            print(error)
        return 1
    print("[frontend_home_contract_boundary_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
