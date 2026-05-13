#!/usr/bin/env python3
"""Guard the Web frontend Contract V2 architecture boundary.

The default mode is a debt-lock guard: existing violations are reported and
bounded, while new default-path violations fail the check. Set
WEB_CONTRACT_V2_ARCH_GUARD_STRICT=1 to require zero debt after the cleanup
batches retire the compatibility paths.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = ROOT / "frontend/apps/web/src"
REPORT_JSON = ROOT / "artifacts/backend/web_contract_v2_frontend_architecture_guard.json"
REPORT_MD = ROOT / "docs/ops/audit/web_contract_v2_frontend_architecture_guard_report.md"
ROUTE_MATRIX = ROOT / "docs/ops/audits/web_frontend_contract_v2_route_runtime_matrix_v1.md"
AUDIT_DOC = ROOT / "docs/ops/audits/web_frontend_contract_v2_architecture_audit_v1.md"


@dataclass(frozen=True)
class DebtRule:
    key: str
    severity: str
    path: str
    pattern: str
    max_count: int
    rationale: str
    next_action: str
    regex: bool = False


DEBT_RULES: tuple[DebtRule, ...] = (
    DebtRule(
        key="v2_to_legacy_projection_entry",
        severity="P1",
        path="api/contract.ts",
        pattern="buildRuntimeProjectionFromV2",
        max_count=2,
        rationale="Contract v2 is still projected back into a legacy runtime shape.",
        next_action="Move v2-to-legacy projection behind an explicit compat boundary and remove default imports.",
    ),
    DebtRule(
        key="legacy_field_descriptor_synthesis",
        severity="P1",
        path="api/contract.ts",
        pattern="buildLegacyFieldDescriptor",
        max_count=2,
        rationale="Frontend synthesizes legacy field descriptors from v2 widgets.",
        next_action="Consume typed v2 widget descriptors directly from ContractV2Store.",
    ),
    DebtRule(
        key="legacy_form_layout_synthesis",
        severity="P1",
        path="api/contract.ts",
        pattern="buildLegacyFormLayout",
        max_count=2,
        rationale="Frontend synthesizes legacy form layout from v2 widgets.",
        next_action="Render containerTree/layoutContract directly through the v2 renderer registry.",
    ),
    DebtRule(
        key="legacy_subview_policy_synthesis",
        severity="P1",
        path="api/contract.ts",
        pattern="buildLegacySubViews",
        max_count=2,
        rationale="Frontend synthesizes relation subviews and edit policies.",
        next_action="Use relation_entry/dataContract/actionRuleList declarations without policy defaults.",
    ),
    DebtRule(
        key="legacy_layout_button_synthesis",
        severity="P1",
        path="api/contract.ts",
        pattern="collectV2LayoutButtons",
        max_count=2,
        rationale="Frontend walks v2 layout to synthesize legacy buttons.",
        next_action="Render actionContract.actionRuleList and widget status directly.",
    ),
    DebtRule(
        key="action_view_loose_contract",
        severity="P1",
        path="views/ActionView.vue",
        pattern="ActionContractLoose",
        max_count=4,
        rationale="ActionView still consumes a mixed legacy/v2 action contract type.",
        next_action="Replace with ContractV2ActionSnapshot after the v2 action renderer lands.",
    ),
    DebtRule(
        key="action_meta_loose_contract",
        severity="P2",
        path="app/action_runtime/useActionViewActionMetaRuntime.ts",
        pattern="ActionContractLoose",
        max_count=5,
        rationale="Action metadata runtime still models a loose legacy-shaped action contract.",
        next_action="Switch action metadata to the normalized v2 store view model.",
    ),
    DebtRule(
        key="product_page_direct_data_imports",
        severity="P1",
        path="pages/ContractFormPage.vue",
        pattern=r"from '../api/data'",
        max_count=1,
        rationale="Contract form page calls low-level data APIs directly.",
        next_action="Route reads/writes through ContractV2Runtime declared dataSource/action operations.",
        regex=True,
    ),
    DebtRule(
        key="action_view_direct_data_imports",
        severity="P1",
        path="views/ActionView.vue",
        pattern=r"from '../api/data'",
        max_count=1,
        rationale="ActionView calls low-level data APIs directly.",
        next_action="Route list/write/delete through ContractV2Runtime declared operations.",
        regex=True,
    ),
    DebtRule(
        key="record_view_direct_data_imports",
        severity="P1",
        path="views/RecordView.vue",
        pattern=r"from '../api/data'",
        max_count=1,
        rationale="RecordView keeps a parallel raw record runtime.",
        next_action="Remove or diagnostics-isolate RecordView after product routes converge.",
        regex=True,
    ),
    DebtRule(
        key="relation_renderer_direct_data_imports",
        severity="P1",
        path="components/view/ViewRelationalRenderer.vue",
        pattern=r"from '../../api/data'",
        max_count=1,
        rationale="Relation renderer performs its own CRUD instead of dispatching contract operations.",
        next_action="Move relation operations behind the v2 runtime relation action executor.",
        regex=True,
    ),
    DebtRule(
        key="contract_form_groups_usage",
        severity="P1",
        path="pages/ContractFormPage.vue",
        pattern="groups_xmlids",
        max_count=8,
        rationale="Generic form path still reads groups for field/action decisions.",
        next_action="Consume backend entitlement/status contract only.",
    ),
    DebtRule(
        key="action_view_groups_usage",
        severity="P1",
        path="views/ActionView.vue",
        pattern="groups_xmlids",
        max_count=1,
        rationale="ActionView still passes user groups into action runtime.",
        next_action="Remove group input from product runtime; backend must emit action availability.",
    ),
    DebtRule(
        key="record_view_groups_usage",
        severity="P1",
        path="views/RecordView.vue",
        pattern="groups_xmlids",
        max_count=1,
        rationale="RecordView still reads groups in its parallel runtime.",
        next_action="Remove or diagnostics-isolate RecordView.",
    ),
    DebtRule(
        key="form_lifecycle_label_mapping",
        severity="P1",
        path="pages/ContractFormPage.vue",
        pattern="'草稿': 'draft'",
        max_count=1,
        rationale="Frontend maps business lifecycle labels back to status codes.",
        next_action="Backend statusContract must provide canonical status code and label.",
    ),
    DebtRule(
        key="lite_legacy_default_fallback",
        severity="P1",
        path="app/contracts/unifiedPageContractLite.ts",
        pattern="legacy_default",
        max_count=2,
        rationale="Lite contract preview still declares legacy default fallback behavior.",
        next_action="Retire lite pilot or convert it into a formal versioned compatibility harness.",
    ),
    DebtRule(
        key="api_contract_lite_legacy_default_fallback",
        severity="P1",
        path="api/contract.ts",
        pattern="legacy_default",
        max_count=1,
        rationale="API contract adapter still exposes lite legacy fallback mode.",
        next_action="Remove from product default path when lite pilot is retired.",
    ),
)


REQUIRED_ROUTE_TOKENS: tuple[str, ...] = (
    "path: '/a/:actionId'",
    "import('../views/ActionViewShell.vue')",
    "path: '/f/:model/:id'",
    "import('../pages/ContractFormPage.vue')",
    "path: '/r/:model/:id'",
    "name: 'record'",
)

FORBIDDEN_ROUTE_TOKENS: tuple[str, ...] = (
    "component: RecordView",
    "component: ModelFormPage",
    "component: ModelListPage",
)

REQUIRED_DOC_TOKENS: tuple[str, ...] = (
    "ContractV2Client",
    "ContractV2Store",
    "ContractV2Runtime",
    "ContractV2Renderer",
    "Compatibility Lifecycle",
)

REQUIRED_ROUTE_MATRIX_TOKENS: tuple[str, ...] = (
    "/a/:actionId",
    "/f/:model/:id",
    "/r/:model/:id",
    "ActionViewShell",
    "ContractFormPage",
    "RecordView.vue",
    "diagnostics-only",
)

REQUIRED_V2_BOUNDARY_FILES: dict[str, tuple[str, ...]] = {
    "app/contracts/v2/types.ts": (
        "ContractV2Snapshot",
        "ContractV2NormalizedStore",
        "ContractV2UnsupportedFeature",
    ),
    "app/contracts/v2/schema.ts": (
        "decodeContractV2Snapshot",
        "ContractV2DecodeError",
        "must be semantic version 2.x.y",
    ),
    "app/contracts/v2/store.ts": (
        "createContractV2Store",
        "widgetsById",
        "actionsById",
        "primaryDataSource",
    ),
    "app/contracts/v2/client.ts": (
        "loadActionContractV2",
        "loadModelContractV2",
        "accepted_contract_versions",
        "client_contract_capabilities",
    ),
    "app/contracts/v2/runtime.ts": (
        "resolveContractV2ActionPlan",
        "resolveContractV2DataSourcePlan",
    ),
}

REQUIRED_FORM_SHADOW_TOKENS: tuple[str, ...] = (
    "decodeContractV2Snapshot",
    "createContractV2Store",
    "v2ContractStore",
    "syncContractV2ShadowStore(response.data)",
    "v2_shadow_store",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def count_matches(text: str, rule: DebtRule) -> int:
    if rule.regex:
        return len(re.findall(rule.pattern, text))
    return text.count(rule.pattern)


def scan_debt(strict: bool) -> tuple[list[dict[str, object]], list[str]]:
    findings: list[dict[str, object]] = []
    errors: list[str] = []
    for rule in DEBT_RULES:
        path = WEB_ROOT / rule.path
        text = read(path)
        count = count_matches(text, rule)
        finding = {
            "key": rule.key,
            "severity": rule.severity,
            "path": f"frontend/apps/web/src/{rule.path}",
            "count": count,
            "max_count": rule.max_count,
            "rationale": rule.rationale,
            "next_action": rule.next_action,
        }
        if count:
            findings.append(finding)
        if strict and count:
            errors.append(f"{rule.key}: strict mode requires zero occurrences, found {count}")
        elif count > rule.max_count:
            errors.append(f"{rule.key}: count increased to {count}, allowed {rule.max_count}")
    return findings, errors


def validate_router() -> list[str]:
    router = read(WEB_ROOT / "router/index.ts")
    errors: list[str] = []
    for token in REQUIRED_ROUTE_TOKENS:
        if token not in router:
            errors.append(f"router missing required default-route token: {token}")
    for token in FORBIDDEN_ROUTE_TOKENS:
        if token in router:
            errors.append(f"router imports forbidden legacy product component: {token}")
    return errors


def validate_docs() -> list[str]:
    errors: list[str] = []
    audit = read(AUDIT_DOC)
    matrix = read(ROUTE_MATRIX)
    if not audit:
        errors.append(f"missing audit doc: {AUDIT_DOC.relative_to(ROOT)}")
    if not matrix:
        errors.append(f"missing route/runtime matrix: {ROUTE_MATRIX.relative_to(ROOT)}")
    for token in REQUIRED_DOC_TOKENS:
        if token not in audit:
            errors.append(f"audit doc missing token: {token}")
    for token in REQUIRED_ROUTE_MATRIX_TOKENS:
        if token not in matrix:
            errors.append(f"route/runtime matrix missing token: {token}")
    return errors


def validate_v2_boundary() -> list[str]:
    errors: list[str] = []
    for relative_path, tokens in REQUIRED_V2_BOUNDARY_FILES.items():
        text = read(WEB_ROOT / relative_path)
        if not text:
            errors.append(f"missing v2 boundary file: frontend/apps/web/src/{relative_path}")
            continue
        for token in tokens:
            if token not in text:
                errors.append(f"v2 boundary file {relative_path} missing token: {token}")
        if relative_path.startswith("app/contracts/v2/") and "api/contract" in text:
            errors.append(f"v2 boundary file {relative_path} must not import legacy api/contract projection")
    return errors


def validate_form_shadow_host() -> list[str]:
    errors: list[str] = []
    text = read(WEB_ROOT / "pages/ContractFormPage.vue")
    for token in REQUIRED_FORM_SHADOW_TOKENS:
        if token not in text:
            errors.append(f"ContractFormPage v2 shadow host missing token: {token}")
    return errors


def write_reports(strict: bool, findings: list[dict[str, object]], errors: list[str]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    severity_counts: dict[str, int] = {}
    for finding in findings:
        severity = str(finding["severity"])
        severity_counts[severity] = severity_counts.get(severity, 0) + int(finding["count"])

    payload = {
        "check": "web_contract_v2_frontend_architecture_guard",
        "mode": "strict" if strict else "debt_lock",
        "status": "fail" if errors else "pass",
        "finding_count": len(findings),
        "severity_counts": severity_counts,
        "findings": findings,
        "errors": errors,
    }
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Web Contract V2 Frontend Architecture Guard Report",
        "",
        f"- mode: {'strict' if strict else 'debt_lock'}",
        f"- status: {'FAIL' if errors else 'PASS'}",
        f"- findings: {len(findings)}",
        "",
        "## Findings",
        "",
    ]
    if findings:
        for finding in findings:
            lines.append(
                f"- [{finding['severity']}] {finding['key']} "
                f"`{finding['path']}` count={finding['count']}/{finding['max_count']}"
            )
    else:
        lines.append("- none")
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in errors)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    strict = os.environ.get("WEB_CONTRACT_V2_ARCH_GUARD_STRICT") == "1"
    findings, errors = scan_debt(strict)
    errors.extend(validate_router())
    errors.extend(validate_docs())
    errors.extend(validate_v2_boundary())
    errors.extend(validate_form_shadow_host())
    write_reports(strict, findings, errors)

    if errors:
        print("[web_contract_v2_frontend_architecture_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        print(f"report={REPORT_JSON.relative_to(ROOT)}")
        return 1
    print(
        "[web_contract_v2_frontend_architecture_guard] PASS "
        f"mode={'strict' if strict else 'debt_lock'} findings={len(findings)}"
    )
    print(f"report={REPORT_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
