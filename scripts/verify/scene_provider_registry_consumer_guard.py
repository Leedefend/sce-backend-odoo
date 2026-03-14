#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TARGETS = [
    ROOT / "addons/smart_core/core/workspace_home_contract_builder.py",
    ROOT / "addons/smart_construction_core/services/project_dashboard_service.py",
    ROOT / "addons/smart_scene/core/scene_registry_engine.py",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _fail(errors: list[str]) -> int:
    print("[verify.scene.provider.registry.consumer.guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    errors: list[str] = []
    for path in TARGETS:
        text = _read(path)
        rel = path.relative_to(ROOT).as_posix()
        if not text:
            errors.append(f"missing file: {rel}")
            continue
        if "provider_locator.py" in text:
            errors.append(f"{rel} should not depend on provider_locator.py")
        if "resolve_scene_provider_path" not in text:
            errors.append(f"{rel} missing resolve_scene_provider_path usage")

    if errors:
        return _fail(errors)

    print("[verify.scene.provider.registry.consumer.guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

