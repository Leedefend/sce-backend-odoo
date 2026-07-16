#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HOME = ROOT / "frontend/apps/web/src/views/HomeView.vue"
SURFACE = ROOT / "frontend/apps/web/src/components/role-home/ContractRoleHome.vue"
RUNTIME = ROOT / "frontend/apps/web/src/composables/shared-surface/useContractRoleHome.ts"


def main() -> int:
    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""
        for path in (HOME, SURFACE, RUNTIME)
    )
    required = ["ContractRoleHome", "fetchMyWorkSummary", "quickLinks", "recentItems"]
    forbidden = ["strictHomeOrchestrationContract", "homeOrchestrationDatasets", "legacy_home", "workspaceHome"]
    errors = [f"missing token: {token}" for token in required if token not in combined]
    errors += [f"legacy token remains: {token}" for token in forbidden if token in combined]
    if errors:
        print("[frontend_portal_dashboard_block_migration_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[frontend_portal_dashboard_block_migration_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
