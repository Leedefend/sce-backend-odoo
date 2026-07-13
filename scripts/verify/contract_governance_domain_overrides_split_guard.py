#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
DOMAIN_OVERRIDES = ROOT / "addons/smart_core/utils/contract_governance_domain_overrides.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 1792


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
    domain_text = _read(DOMAIN_OVERRIDES)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not domain_text:
        errors.append(f"missing domain overrides module: {DOMAIN_OVERRIDES.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_domain_overrides_module()",
            "contract_governance_domain_overrides.py",
            "_domain_overrides.register_contract_domain_override(name, handler, priority=priority)",
            "_domain_overrides.append_governance_diagnostic(data, key, value)",
            "return _domain_overrides.apply_domain_overrides(data, contract_mode)",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing domain override split token: {token}")
        if "_DOMAIN_OVERRIDE_REGISTRY" in governance_text:
            errors.append("contract_governance.py must not keep the domain override registry")

    if domain_text:
        for token in [
            "DOMAIN_OVERRIDE_REGISTRY",
            "def register_contract_domain_override(",
            "def append_governance_diagnostic(",
            "def apply_domain_overrides(",
            "\"error_type\": exc.__class__.__name__",
            "\"message\": _safe_text(str(exc))[:240]",
            "DOMAIN_OVERRIDE_REGISTRY.sort(",
        ]:
            if token not in domain_text:
                errors.append(f"domain overrides module missing token: {token}")
        for forbidden in ("requests.", "env[", ".write(", ".search(", "registry["):
            if forbidden in domain_text:
                errors.append(f"domain overrides module must stay projection-only; forbidden token: {forbidden}")

    if "python3 scripts/verify/contract_governance_domain_overrides_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_domain_overrides_split_guard.py")

    if not errors:
        domain = _load(DOMAIN_OVERRIDES, "contract_governance_domain_overrides_under_guard")
        domain.DOMAIN_OVERRIDE_REGISTRY.clear()
        calls: list[str] = []

        def first(data: dict, mode: str) -> None:
            calls.append(f"first:{mode}")
            data["first"] = True

        def failing(_data: dict, _mode: str) -> None:
            raise RuntimeError("boom")

        domain.register_contract_domain_override("second", failing, priority=20)
        domain.register_contract_domain_override("first", first, priority=10)
        domain.register_contract_domain_override("second", failing, priority=30)
        data: dict = {}
        failures = domain.apply_domain_overrides(data, "user")
        if calls != ["first:user"] or data.get("first") is not True:
            errors.append("domain overrides must run callable handlers in priority order")
        if len(failures) != 1 or failures[0].get("name") != "second":
            errors.append("domain overrides must capture failing override diagnostics")
        if failures and failures[0].get("error_type") != "RuntimeError":
            errors.append("domain override failures must include exception type")
        diagnostic_data: dict = {}
        domain.append_governance_diagnostic(diagnostic_data, "sample", [{"ok": True}])
        if diagnostic_data.get("diagnostic") != {"sample": [{"ok": True}]}:
            errors.append("append_governance_diagnostic must merge diagnostic payloads")
        domain.DOMAIN_OVERRIDE_REGISTRY.clear()

    if errors:
        print("[contract_governance_domain_overrides_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_domain_overrides_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
