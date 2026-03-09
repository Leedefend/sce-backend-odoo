#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "addons/smart_core/core/workspace_home_contract_builder.py"
PROVIDER = ROOT / "addons/smart_core/core/workspace_home_data_provider.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _fail(errors: list[str]) -> int:
    print("[workspace_home_provider_split_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    builder_text = _read(BUILDER)
    provider_text = _read(PROVIDER)
    errors: list[str] = []

    if not builder_text:
        errors.append(f"missing file: {BUILDER.relative_to(ROOT).as_posix()}")
    if not provider_text:
        errors.append(f"missing file: {PROVIDER.relative_to(ROOT).as_posix()}")
    if errors:
        return _fail(errors)

    required_builder_tokens = [
        "def _load_data_provider():",
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

    required_provider_tokens = [
        "def build_today_actions(ready_caps",
        "def build_advice_items(locked_caps",
        "def build_role_focus_config(role_code: str)",
        "def build_v1_focus_map()",
        "def build_v1_page_profile(role_code: str)",
        "def build_v1_data_sources()",
        "def build_v1_state_schema()",
        "def build_v1_action_specs()",
        "def build_v1_zones(role_code: str, audience: List[str], zone_rank: Dict[str, int])",
        "def build_legacy_zones(role_code: str, zone_rank: Dict[str, int])",
        "def build_legacy_blocks(role_code: str)",
    ]
    for token in required_provider_tokens:
        if token not in provider_text:
            errors.append(f"provider missing token: {token}")

    if errors:
        return _fail(errors)

    print("[workspace_home_provider_split_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
