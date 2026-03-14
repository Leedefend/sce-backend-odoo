#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CORE_INIT = ROOT / "addons/smart_scene/core/__init__.py"


def _fail(errors: list[str]) -> int:
    print("[verify.scene.core_api_boundary.guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    if not CORE_INIT.is_file():
        return _fail([f"missing file: {CORE_INIT.relative_to(ROOT).as_posix()}"])
    text = CORE_INIT.read_text(encoding="utf-8", errors="ignore")

    forbidden = [
        "resolve_workspace_home_provider_path",
        "resolve_project_dashboard_scene_content_path",
        "resolve_scene_registry_content_path",
    ]
    required = [
        "SceneContentProvider",
        "SceneProviderRegistry",
        "build_scene_provider_registry",
        "resolve_scene_provider_path",
    ]

    errors: list[str] = []
    for token in forbidden:
        if token in text:
            errors.append(f"forbidden export token present: {token}")
    for token in required:
        if token not in text:
            errors.append(f"missing required export token: {token}")

    if errors:
        return _fail(errors)

    print("[verify.scene.core_api_boundary.guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

