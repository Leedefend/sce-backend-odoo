#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HOME = ROOT / "frontend/apps/web/src/views/HomeView.vue"
SURFACE = ROOT / "frontend/apps/web/src/components/role-home/ContractRoleHome.vue"
RUNTIME = ROOT / "frontend/apps/web/src/composables/shared-surface/useContractRoleHome.ts"


def main() -> int:
    sources = {
        "HomeView.vue": HOME.read_text(encoding="utf-8", errors="ignore") if HOME.is_file() else "",
        "ContractRoleHome.vue": SURFACE.read_text(encoding="utf-8", errors="ignore") if SURFACE.is_file() else "",
        "useContractRoleHome.ts": RUNTIME.read_text(encoding="utf-8", errors="ignore") if RUNTIME.is_file() else "",
    }
    required = {
        "HomeView.vue": ["<ContractRoleHome />"],
        "ContractRoleHome.vue": ["tasks.length", "summaries.length", "quickLinks.length", "recentItems.length"],
        "useContractRoleHome.ts": ["usePageContract('home')", "fetchMyWorkSummary(", "session.menuTree", "session.activityPages"],
    }
    errors = []
    for scope, tokens in required.items():
        if not sources[scope]:
            errors.append(f"missing file: {scope}")
        errors.extend(f"{scope} missing token: {token}" for token in tokens if token not in sources[scope])
    combined = "\n".join(sources.values())
    for token in ["legacy_home", "minimum-workspace-fallback", "capability-home", "role ===", "role_code ==="]:
        if token in combined:
            errors.append(f"forbidden legacy/inference token: {token}")
    if errors:
        print("[frontend_home_orchestration_consumption_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[frontend_home_orchestration_consumption_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
