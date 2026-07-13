#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
ACCESS_POLICY = ROOT / "addons/smart_core/utils/contract_governance_access_policy.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 3780


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
    access_policy_text = _read(ACCESS_POLICY)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not access_policy_text:
        errors.append(f"missing access policy module: {ACCESS_POLICY.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_access_policy_module()",
            "contract_governance_access_policy.py",
            "_access_policy.realign_access_policy_with_visible_fields(data)",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing access policy split token: {token}")

    if access_policy_text:
        for token in [
            "def realign_access_policy_with_visible_fields(",
            "RELATION_READ_FORBIDDEN_CORE",
            "access_policy:{mode}:{reason_code or 'UNKNOWN'}",
        ]:
            if token not in access_policy_text:
                errors.append(f"access policy module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in access_policy_text:
                errors.append(f"access policy module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_access_policy_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_access_policy_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_access_policy_split_under_guard")
        data = {
            "fields": {"name": {}, "partner_id": {}},
            "visible_fields": ["name"],
            "access_policy": {
                "blocked_fields": [
                    {"field": "partner_id", "model": "res.partner", "reason_code": "RELATION_READ_FORBIDDEN"},
                    {"field": "__model__", "model": "project.project", "reason_code": "MODEL_BLOCKED"},
                ],
                "degraded_fields": [{"field": "name", "reason_code": "RELATION_READ_FORBIDDEN"}],
            },
            "warnings": ["access_policy:old:STALE"],
        }
        governance._realign_access_policy_with_visible_fields(data)
        policy = data.get("access_policy") or {}
        if policy.get("mode") != "block" or policy.get("reason_code") != "MODEL_BLOCKED":
            errors.append("access policy must prioritize visible/model blocked rows")
        if any(row.get("field") == "partner_id" for row in policy.get("blocked_fields") or []):
            errors.append("access policy must drop hidden blocked fields")
        if data.get("warnings") != ["access_policy:block:MODEL_BLOCKED"]:
            errors.append("access policy warning marker must be refreshed")

    if errors:
        print("[contract_governance_access_policy_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_access_policy_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
