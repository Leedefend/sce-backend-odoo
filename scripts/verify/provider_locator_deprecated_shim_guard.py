#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
LOCATOR = ROOT / "addons/smart_scene/core/provider_locator.py"


def _fail(errors: list[str]) -> int:
    print("[verify.scene.provider_locator.deprecated_shim.guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    if not LOCATOR.is_file():
        return _fail([f"missing file: {LOCATOR.relative_to(ROOT).as_posix()}"])

    text = LOCATOR.read_text(encoding="utf-8", errors="ignore")
    errors: list[str] = []

    required = [
        "Deprecated shim",
        "return _resolve_by_registry(\"workspace.home\", base_dir)",
        "return _resolve_by_registry(\"project.dashboard\", base_dir)",
        "return _resolve_by_registry(\"scene.registry\", base_dir)",
    ]
    forbidden = [
        "workspace_home_data_provider.py",
        "project_dashboard_scene_content.py",
        "scene_registry_content.py",
    ]

    for token in required:
        if token not in text:
            errors.append(f"missing token: {token}")
    for token in forbidden:
        if token in text:
            errors.append(f"forbidden fallback token present: {token}")

    if errors:
        return _fail(errors)

    print("[verify.scene.provider_locator.deprecated_shim.guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

