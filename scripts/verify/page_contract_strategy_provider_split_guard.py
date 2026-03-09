#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "addons/smart_core/core/page_contracts_builder.py"
PROVIDER = ROOT / "addons/smart_core/core/page_orchestration_data_provider.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _fail(errors: list[str]) -> int:
    print("[page_contract_strategy_provider_split_guard] FAIL")
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
        'fn = getattr(provider, "build_page_type", None)',
        'fn = getattr(provider, "build_page_audience", None)',
        'fn = getattr(provider, "build_default_page_actions", None)',
    ]
    for token in required_builder_tokens:
        if token not in builder_text:
            errors.append(f"builder missing token: {token}")

    required_provider_tokens = [
        "def build_page_type(page_key: str)",
        "def build_page_audience(page_key: str)",
        "def build_default_page_actions(page_key: str)",
    ]
    for token in required_provider_tokens:
        if token not in provider_text:
            errors.append(f"provider missing token: {token}")

    if errors:
        return _fail(errors)

    print("[page_contract_strategy_provider_split_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

