#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
CANONICALIZATION = ROOT / "addons/smart_core/utils/contract_governance_canonicalization.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 3769


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
    canonicalization_text = _read(CANONICALIZATION)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not canonicalization_text:
        errors.append(f"missing canonicalization module: {CANONICALIZATION.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_canonicalization_module()",
            "contract_governance_canonicalization.py",
            "return _canonicalization.canonicalize_contract_keys(obj, path=path, conflicts=conflicts)",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing canonicalization split token: {token}")

    if canonicalization_text:
        for token in [
            "def canonicalize_contract_keys(",
            "_CONTRACT_KEY_CANONICAL_MAP",
            "conflicts.append(",
            "should_replace = key == snake_preferred",
        ]:
            if token not in canonicalization_text:
                errors.append(f"canonicalization module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in canonicalization_text:
                errors.append(f"canonicalization module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_canonicalization_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_canonicalization_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_canonicalization_split_under_guard")
        conflicts: list[dict] = []
        result = governance._canonicalize_contract_keys(
            {
                "requiredCapabilities": [{"groupKey": "project", "isPrimary": True}],
                "required_capabilities": [{"group_key": "override"}],
            },
            conflicts=conflicts,
        )
        capabilities = result.get("required_capabilities") or []
        first = capabilities[0] if capabilities else {}
        if first.get("group_key") != "override":
            errors.append("snake_case canonical key must win over earlier alias")
        if not conflicts or conflicts[0].get("canonical") != "required_capabilities":
            errors.append("canonicalization conflicts must record dropped aliases")

    if errors:
        print("[contract_governance_canonicalization_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_canonicalization_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
