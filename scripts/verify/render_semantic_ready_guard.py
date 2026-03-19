#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
FORM_PAGE = ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue"
REPORT_JSON = ROOT / "artifacts/backend/render_semantic_ready_report.json"
REPORT_MD = ROOT / "docs/ops/audit/render_semantic_ready_report.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _extract_core_cap(text: str) -> int | None:
    m = re.search(r"_FORM_CORE_FIELD_MAX\s*=\s*(\d+)", text)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def main() -> int:
    governance_text = _read(GOVERNANCE)
    form_text = _read(FORM_PAGE)
    errors: list[str] = []

    if not governance_text:
        errors.append(f"missing file: {GOVERNANCE.relative_to(ROOT).as_posix()}")
    if not form_text:
        errors.append(f"missing file: {FORM_PAGE.relative_to(ROOT).as_posix()}")

    core_cap = _extract_core_cap(governance_text)
    if core_cap is None:
        errors.append("missing _FORM_CORE_FIELD_MAX")
    elif core_cap >= 10:
        errors.append(f"core field cap invalid: {core_cap} (must be < 10)")

    required_governance_tokens = [
        'data["render_profile"] = _resolve_render_profile(data)',
        'data["hide_filters_on_create"] = True',
        '"name": "core"',
        '"name": "advanced"',
        '"collapsed_by_default": True',
        "primary_assigned = False",
        'row["semantic"] = semantic',
        'row["visible_profiles"] = profiles or [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT]',
    ]
    for token in required_governance_tokens:
        if token not in governance_text:
            errors.append(f"contract_governance missing token: {token}")

    required_frontend_tokens = [
        "const renderProfile = computed<'create' | 'edit' | 'readonly'>",
        "const showDebugActions = computed(() => renderProfile.value !== 'create');",
        "const showSearchFilters = computed(() => {",
        "if (renderProfile.value !== 'create') return true;",
        "return !contract.value.hide_filters_on_create;",
        "const hasPrimaryHeaderAction = computed(() => headerActionsVisible.value.some((item) => item.semantic === 'primary_action'));",
        "advancedExpanded.value = renderProfile.value !== 'create'",
        "isFieldVisible(node.name)",
        "收起高级信息",
        "展开高级信息",
        "v-if=\"showDebugActions\" class=\"ghost\" :disabled=\"busy || !contract\" @click=\"exportContractJson\"",
    ]
    for token in required_frontend_tokens:
        if token not in form_text:
            errors.append(f"ContractFormPage missing token: {token}")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "core_field_cap": core_cap,
            "core_field_cap_lt_10": core_cap is not None and core_cap < 10,
            "single_primary_action_guard": "primary_assigned = False" in governance_text,
            "create_hide_search_filters": "showSearchFilters" in form_text,
            "create_hide_export_button": "showDebugActions" in form_text and "exportContractJson" in form_text,
            "advanced_default_collapsed_on_create": "advancedExpanded.value = renderProfile.value !== 'create'" in form_text,
        },
        "errors": errors,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Render Semantic Ready Report",
        "",
        f"- ok: `{report['ok']}`",
        f"- core_field_cap: `{report['summary']['core_field_cap']}`",
        f"- core_field_cap_lt_10: `{report['summary']['core_field_cap_lt_10']}`",
        f"- single_primary_action_guard: `{report['summary']['single_primary_action_guard']}`",
        f"- create_hide_search_filters: `{report['summary']['create_hide_search_filters']}`",
        f"- create_hide_export_button: `{report['summary']['create_hide_export_button']}`",
        f"- advanced_default_collapsed_on_create: `{report['summary']['advanced_default_collapsed_on_create']}`",
    ]
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {err}" for err in errors])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[render_semantic_ready_guard] FAIL")
        for err in errors:
            print(err)
        return 1
    print("[render_semantic_ready_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
