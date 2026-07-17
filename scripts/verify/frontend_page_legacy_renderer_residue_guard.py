#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HOME = ROOT / "frontend/apps/web/src/views/HomeView.vue"
RETIRED_DELEGATES = [
    ROOT / "frontend/apps/web/src/views/RecordView.vue",
    ROOT / "frontend/apps/web/src/pages/ModelFormPage.vue",
]


def main() -> int:
    text = HOME.read_text(encoding="utf-8", errors="ignore") if HOME.is_file() else ""
    errors = []
    if "<ContractRoleHome />" not in text:
        errors.append("HomeView must mount the shared role-home surface")
    for token in ["legacy_home", "minimum-workspace-fallback", "capability-home", "PageRenderer", "workspaceHome"]:
        if token in text:
            errors.append(f"HomeView contains legacy residue: {token}")
    if len(text.splitlines()) > 40:
        errors.append("HomeView must remain a thin route entry")
    for path in RETIRED_DELEGATES:
        if path.exists():
            errors.append(f"retired compatibility delegate still exists: {path.relative_to(ROOT)}")
    if errors:
        print("[frontend_page_legacy_renderer_residue_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[frontend_page_legacy_renderer_residue_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
