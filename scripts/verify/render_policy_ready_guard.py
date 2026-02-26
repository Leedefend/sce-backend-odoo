#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "addons/smart_core/utils/contract_governance.py"
FORM = ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue"
POLICY = ROOT / "frontend/apps/web/src/app/contractPolicies.ts"
REPORT_JSON = ROOT / "artifacts/backend/render_policy_ready_report.json"
REPORT_MD = ROOT / "docs/ops/audit/render_policy_ready_report.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def main() -> int:
    gov_text = _read(GOV)
    form_text = _read(FORM)
    policy_text = _read(POLICY)
    errors: list[str] = []

    for path, text in ((GOV, gov_text), (FORM, form_text), (POLICY, policy_text)):
        if not text:
            errors.append(f"missing file: {path.relative_to(ROOT).as_posix()}")

    governance_tokens = [
        'data["field_policies"] = _build_form_field_policies(data)',
        'data["action_policies"] = _build_form_action_policies(data)',
        'data["validation_rules"] = _build_form_validation_rules(data)',
        '"required_fields": required_fields[:12]',
        '"required_capabilities"',
        '"required_groups"',
        '"required_roles"',
        '"conditions"',
        '"condition_expr"',
        '"lifecycle"',
        '"code": "REQUIRED"',
    ]
    for token in governance_tokens:
        if token not in gov_text:
            errors.append(f"contract_governance missing token: {token}")

    policy_tokens = [
        "export function evaluateFieldPolicy(",
        "export function evaluateActionPolicy(",
        "export function collectPolicyValidationErrors(",
        "function evaluateConditionExpr(",
        "required_fields",
        "required_capabilities",
        "required_groups",
        "required_roles",
        "conditions",
        "condition_expr",
        "lifecycle",
        "visible_profiles",
        "required_profiles",
        "readonly_profiles",
    ]
    for token in policy_tokens:
        if token not in policy_text:
            errors.append(f"contractPolicies missing token: {token}")

    form_tokens = [
        "evaluateFieldPolicy(",
        "evaluateActionPolicy(contract.value, key, policyContext.value)",
        "collectPolicyValidationErrors(contract.value, policyContext.value)",
        "capabilities: runtimeCapabilities.value",
        "userGroups: runtimeUserGroups.value",
        "roleCode: runtimeRoleCode.value",
    ]
    for token in form_tokens:
        if token not in form_text:
            errors.append(f"ContractFormPage missing token: {token}")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "backend_policy_contract": all(t in gov_text for t in governance_tokens),
            "frontend_policy_engine": all(t in policy_text for t in policy_tokens),
            "frontend_policy_consumption": all(t in form_text for t in form_tokens),
        },
        "errors": errors,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Render Policy Ready Report",
        "",
        f"- ok: `{report['ok']}`",
        f"- backend_policy_contract: `{report['summary']['backend_policy_contract']}`",
        f"- frontend_policy_engine: `{report['summary']['frontend_policy_engine']}`",
        f"- frontend_policy_consumption: `{report['summary']['frontend_policy_consumption']}`",
    ]
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {err}" for err in errors])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[render_policy_ready_guard] FAIL")
        for err in errors:
            print(err)
        return 1
    print("[render_policy_ready_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
