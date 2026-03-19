#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "addons/smart_core/utils/contract_governance.py"
ACTION_VIEW = ROOT / "frontend/apps/web/src/views/ActionView.vue"
ACTION_PRESENTATION_RUNTIME = ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewActionPresentationRuntime.ts"
FILTER_COMPUTED_RUNTIME = ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewFilterComputedRuntime.ts"
REPORT_JSON = ROOT / "artifacts/backend/list_surface_clean_report.json"
REPORT_MD = ROOT / "docs/ops/audit/list_surface_clean_report.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def main() -> int:
    gov_text = _read(GOV)
    view_text = _read(ACTION_VIEW)
    action_presentation_runtime_text = _read(ACTION_PRESENTATION_RUNTIME)
    filter_computed_runtime_text = _read(FILTER_COMPUTED_RUNTIME)
    errors: list[str] = []

    if not gov_text:
        errors.append(f"missing file: {GOV.relative_to(ROOT).as_posix()}")
    if not view_text:
        errors.append(f"missing file: {ACTION_VIEW.relative_to(ROOT).as_posix()}")
    if not action_presentation_runtime_text:
        errors.append(f"missing file: {ACTION_PRESENTATION_RUNTIME.relative_to(ROOT).as_posix()}")
    if not filter_computed_runtime_text:
        errors.append(f"missing file: {FILTER_COMPUTED_RUNTIME.relative_to(ROOT).as_posix()}")

    gov_tokens = [
        "_apply_user_surface_noise_reduction",
        "_build_user_surface_action_groups",
        "surface_policies",
        '"filters_primary_max"',
        '"actions_primary_max"',
    ]
    for token in gov_tokens:
        if token not in gov_text:
            errors.append(f"contract_governance missing token: {token}")

    view_tokens = [
        "contractPrimaryActions",
        "vm.actions.primary",
        "vm.actions.overflowGroups",
        "showMoreContractActions",
        "showMoreContractFilters",
    ]
    for token in view_tokens:
        if token not in view_text:
            errors.append(f"ActionView missing token: {token}")

    action_presentation_tokens = [
        "surface_policies?.actions_primary_max",
        "contractActionGroupsRaw",
        "resolveContractActionPresentation",
        "contractOverflowActionGroups",
    ]
    for token in action_presentation_tokens:
        if token not in action_presentation_runtime_text:
            errors.append(f"useActionViewActionPresentationRuntime missing token: {token}")

    filter_runtime_tokens = [
        "surface_policies?.filters_primary_max",
        "contractFilterChips",
        "filterPrimaryBudget",
    ]
    for token in filter_runtime_tokens:
        if token not in filter_computed_runtime_text:
            errors.append(f"useActionViewFilterComputedRuntime missing token: {token}")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "backend_surface_policy": all(token in gov_text for token in gov_tokens),
            "frontend_grouped_actions": all(token in view_text for token in view_tokens),
        },
        "errors": errors,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# List Surface Clean Report",
        "",
        f"- ok: `{report['ok']}`",
        f"- backend_surface_policy: `{report['summary']['backend_surface_policy']}`",
        f"- frontend_grouped_actions: `{report['summary']['frontend_grouped_actions']}`",
    ]
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {err}" for err in errors])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[list_surface_clean_guard] FAIL")
        for err in errors:
            print(err)
        return 1
    print("[list_surface_clean_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
