#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
CAPABILITIES = ROOT / "addons/smart_core/utils/contract_governance_capabilities.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 4272


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    errors: list[str] = []
    governance_text = _read(GOVERNANCE)
    capabilities_text = _read(CAPABILITIES)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not capabilities_text:
        errors.append(f"missing capability module: {CAPABILITIES.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_capabilities_module()",
            "contract_governance_capabilities.py",
            "_capabilities._CAPABILITY_GROUP_PROFILE_REGISTRY = _CAPABILITY_GROUP_PROFILE_REGISTRY",
            "def normalize_capabilities(capabilities: list) -> list[dict]:",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing capability split token: {token}")

    if capabilities_text:
        for token in [
            "def normalize_capabilities(",
            "def is_internal_or_smoke(",
            "def _has_demo_semantics(",
            "def _normalized_tags_for_item(",
            "_CAPABILITY_GROUP_PROFILE_REGISTRY",
        ]:
            if token not in capabilities_text:
                errors.append(f"capability module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in capabilities_text:
                errors.append(f"capability module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_capabilities_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_capabilities_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_capabilities_split_under_guard")
        before = dict(governance._CAPABILITY_GROUP_PROFILE_REGISTRY)
        governance.register_capability_group_profile(
            "guard_group",
            {"label": "Guard Group", "icon": "shield", "key_prefixes": ["guard."]},
        )
        normalized = governance.normalize_capabilities([{"key": "guard.case", "name": "Guard Case"}])
        if not normalized or normalized[0].get("group_key") != "guard_group":
            errors.append("normalize_capabilities must read the shared capability group registry")
        governance._CAPABILITY_GROUP_PROFILE_REGISTRY.clear()
        governance._CAPABILITY_GROUP_PROFILE_REGISTRY.update(before)

    if errors:
        print("[contract_governance_capabilities_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_capabilities_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
