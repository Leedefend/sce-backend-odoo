#!/usr/bin/env python3
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "addons/smart_core/core/workspace_home_contract_builder.py"
LOCATOR = ROOT / "addons/smart_scene/core/provider_locator.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load_module(path: Path, module_name: str):
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"spec unavailable: {path.as_posix()}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fail(errors: list[str]) -> int:
    print("[workspace_home_provider_split_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    builder_text = _read(BUILDER)
    errors: list[str] = []

    if not builder_text:
        errors.append(f"missing file: {BUILDER.relative_to(ROOT).as_posix()}")
    if not LOCATOR.is_file():
        errors.append(f"missing file: {LOCATOR.relative_to(ROOT).as_posix()}")
    if errors:
        return _fail(errors)

    required_builder_tokens = [
        "def _load_data_provider():",
        "resolve_workspace_home_provider_path",
        "Path(__file__).with_name(\"workspace_home_data_provider.py\")",
        "fn = getattr(provider, \"build_today_actions\", None)",
        "fn = getattr(provider, \"build_advice_items\", None)",
        "fn = getattr(provider, \"build_role_focus_config\", None)",
        "fn = getattr(provider, \"build_v1_focus_map\", None)",
        "fn = getattr(provider, \"build_v1_page_profile\", None)",
        "fn = getattr(provider, \"build_v1_data_sources\", None)",
        "fn = getattr(provider, \"build_v1_state_schema\", None)",
        "fn = getattr(provider, \"build_v1_action_specs\", None)",
        "fn = getattr(provider, \"build_v1_zones\", None)",
        "zones_fn = getattr(provider, \"build_legacy_zones\", None)",
        "blocks_fn = getattr(provider, \"build_legacy_blocks\", None)",
    ]
    for token in required_builder_tokens:
        if token not in builder_text:
            errors.append(f"builder missing token: {token}")

    try:
        locator_module = _load_module(LOCATOR, "workspace_home_provider_locator_guard")
        resolver = getattr(locator_module, "resolve_workspace_home_provider_path", None)
        if not callable(resolver):
            errors.append("provider locator missing resolve_workspace_home_provider_path")
        else:
            provider_path = resolver(BUILDER)
            if not isinstance(provider_path, Path) or not provider_path.is_file():
                errors.append("workspace_home provider path not resolved")
            else:
                rel = provider_path.relative_to(ROOT).as_posix()
                if "/profiles/" not in f"/{rel}":
                    errors.append(f"workspace_home provider must resolve to profiles path, got: {rel}")
                provider_module = _load_module(provider_path, "workspace_home_scene_content_guard")
                required_provider_symbols = [
                    "build_today_actions",
                    "build_advice_items",
                    "build_role_focus_config",
                    "build_v1_focus_map",
                    "build_v1_page_profile",
                    "build_v1_data_sources",
                    "build_v1_state_schema",
                    "build_v1_action_specs",
                    "build_v1_zones",
                    "build_legacy_zones",
                    "build_legacy_blocks",
                ]
                for symbol in required_provider_symbols:
                    if not callable(getattr(provider_module, symbol, None)):
                        errors.append(f"provider missing callable: {symbol}")
    except Exception as exc:
        errors.append(f"provider load failed: {exc}")

    if errors:
        return _fail(errors)

    print("[workspace_home_provider_split_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
