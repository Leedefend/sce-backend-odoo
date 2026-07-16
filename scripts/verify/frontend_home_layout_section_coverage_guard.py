#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HOME = ROOT / "frontend/apps/web/src/components/role-home/ContractRoleHome.vue"


def main() -> int:
    text = HOME.read_text(encoding="utf-8", errors="ignore") if HOME.is_file() else ""
    required = [
        'class="contract-role-home__header"',
        'class="contract-role-home__tasks"',
        'class="contract-role-home__overview"',
        'class="contract-role-home__access"',
        'v-if="loading"',
        'v-else-if="error"',
        'v-else-if="tasks.length"',
        '@media (max-width: 700px)',
    ]
    forbidden = ["role ===", "role_code ===", "workspaceHome", "legacy_home", "HUD:"]
    errors = [f"missing token: {token}" for token in required if token not in text]
    errors += [f"forbidden token: {token}" for token in forbidden if token in text]
    if errors:
        print("[frontend_home_layout_section_coverage_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[frontend_home_layout_section_coverage_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
