#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/engineering_convergence/action_view_responsibility_map.md"
VIEW = ROOT / "frontend/apps/web/src/views/ActionView.vue"
ROUTE_RUNTIME = ROOT / "frontend/apps/web/src/app/runtime/actionViewRouteRuntime.ts"
CONTRACT_ACTION_RUNTIME = ROOT / "frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts"
NAVIGATION_CONTEXT = ROOT / "frontend/apps/web/src/app/navigationContext.ts"
CI = ROOT / "make/ci.mk"

LINE_BUDGET = 3684


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _line_count(text: str) -> int:
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def main() -> int:
    errors: list[str] = []
    doc = _read(DOC)
    view = _read(VIEW)
    route_runtime = _read(ROUTE_RUNTIME)
    contract_action_runtime = _read(CONTRACT_ACTION_RUNTIME)
    navigation_context = _read(NAVIGATION_CONTEXT)
    ci = _read(CI)

    if not doc:
        errors.append(f"missing responsibility map: {DOC.relative_to(ROOT)}")
    if not view:
        errors.append(f"missing view: {VIEW.relative_to(ROOT)}")
    if not route_runtime:
        errors.append(f"missing route runtime: {ROUTE_RUNTIME.relative_to(ROOT)}")
    if not contract_action_runtime:
        errors.append(f"missing contract action runtime: {CONTRACT_ACTION_RUNTIME.relative_to(ROOT)}")
    if not navigation_context:
        errors.append(f"missing navigation context: {NAVIGATION_CONTEXT.relative_to(ROOT)}")

    for token in [
        "Action View Responsibility Map",
        "Current size: 3,684 lines",
        "Phase: Stage 6 business category create nav query split",
        "## Purpose",
        "## Route Entry",
        "## Responsibility Bands",
        "## Current Side-Effect Boundaries",
        "## Do Not Move Yet",
        "## Stage 1 Target",
        "## Stage 2 Target",
        "## Stage 3 Target",
        "## Stage 4 Target",
        "## Stage 5 Target",
        "## Stage 6 Target",
        "## Verification Gaps",
        "## Invariants",
        "`ActionView.vue` is locked at `<=3684` lines",
        "`usePageContract('action')`",
        "`useActionPageModel`",
        "`useActionViewActionRuntime`",
        "`actionViewRouteRuntime.ts` owns the pure",
        "`normalizeActivityRuntimeRouteQuery` helper",
        "`buildActivityRuntimeRouteState` helper",
        "`buildActionActivityRouteKey` helper",
        "`applyActionViewV2ButtonStatus` helpers",
        "`buildBusinessCategoryCreateNavQuery` helper",
        "runBatchPolicyAction",
        "loadListColumnPreference",
        "handleToggleRecordFavorite",
        "redirectMenuOnlyRouteIfNeeded",
        "PROJECT_CONTEXT_CHANGED_EVENT",
        "router.push",
        "router.replace",
        "window.open",
        "window.location.assign",
        "must not infer backend permission truth",
    ]:
        if token not in doc:
            errors.append(f"responsibility map missing token: {token}")

    if view:
        count = _line_count(view)
        if count > LINE_BUDGET:
            errors.append(f"ActionView.vue line budget exceeded: {count} > {LINE_BUDGET}")
        for token in [
            "<script setup lang=\"ts\">",
            "const route = useRoute();",
            "const router = useRouter();",
            "const pageContract = usePageContract('action');",
            "normalizeActivityRuntimeRouteQuery,",
            "buildActivityRuntimeRouteState,",
            "buildActionActivityRouteKey,",
            "applyActionViewV2ButtonStatus,",
            "buildBusinessCategoryCreateNavQuery,",
            "useActionPageModel({",
            "useActionViewActionRuntime({",
            "async function runBatchPolicyAction",
            "async function loadListColumnPreference",
            "async function handleToggleRecordFavorite",
            "async function redirectMenuOnlyRouteIfNeeded",
            "window.addEventListener(PROJECT_CONTEXT_CHANGED_EVENT",
            "window.removeEventListener(PROJECT_CONTEXT_CHANGED_EVENT",
            "router.push",
            "router.replace",
            "window.open",
            "window.location.assign",
            "watch(",
        ]:
            if token not in view:
                errors.append(f"ActionView.vue missing boundary token: {token}")
        if "function normalizeActivityRuntimeRouteQuery(" in view:
            errors.append("ActionView.vue must not locally implement normalizeActivityRuntimeRouteQuery")
        for token in [
            "function stableActionContractId(",
            "function resolveActionViewV2ButtonStatus(",
            "function applyActionViewV2ButtonStatus(",
            "defaults.default_business_category_id",
        ]:
            if token in view:
                errors.append(f"ActionView.vue must not locally implement {token}")

    if route_runtime:
        for token in [
            "export function normalizeActivityRuntimeRouteQuery(source: Dict): Dict",
            "export function buildActivityRuntimeRouteState(",
            "export function buildActionActivityRouteKey(",
            "'active_filter'",
            "'group_sort'",
            "delete next.active_filter",
            "delete next.group_sort",
        ]:
            if token not in route_runtime:
                errors.append(f"actionViewRouteRuntime.ts missing token: {token}")
        for token in [
            "router.push",
            "router.replace",
            "window.open",
            "window.location.assign",
            "updateActiveActivityRuntimeQuery",
            "intentRequest",
        ]:
            if token in route_runtime:
                errors.append(f"actionViewRouteRuntime.ts must remain pure; found: {token}")

    if contract_action_runtime:
        for token in [
            "export function stableActionContractId(",
            "export function resolveActionViewV2ButtonStatus(",
            "export function applyActionViewV2ButtonStatus",
            "UnifiedPageContractV2ButtonStatus",
            "disabled_by_status_contract",
        ]:
            if token not in contract_action_runtime:
                errors.append(f"actionViewContractActionRuntime.ts missing token: {token}")
        for token in [
            "router.push",
            "router.replace",
            "window.open",
            "window.location.assign",
            "intentRequest",
        ]:
            if token in contract_action_runtime:
                errors.append(f"actionViewContractActionRuntime.ts must remain pure; found: {token}")

    if navigation_context:
        for token in [
            "export function buildBusinessCategoryCreateNavQuery(",
            "current_business_category_code",
            "default_business_category_code",
            "ctx_source: 'business_category_create_picker'",
            "default_business_category_id",
        ]:
            if token not in navigation_context:
                errors.append(f"navigationContext.ts missing token: {token}")
        for token in [
            "router.push",
            "router.replace",
            "window.open",
            "window.location.assign",
            "intentRequest",
        ]:
            if token in navigation_context:
                errors.append(f"navigationContext.ts must remain pure; found: {token}")

    ci_token = "python3 scripts/verify/action_view_responsibility_map_guard.py"
    if ci_token not in ci:
        errors.append("ci.local.quick must run action_view_responsibility_map_guard.py")
    smoke_token = "node scripts/verify/action_view_route_runtime_smoke.js"
    if smoke_token not in ci:
        errors.append("ci.local.quick must run action_view_route_runtime_smoke.js")
    action_smoke_token = "node scripts/verify/action_view_contract_action_runtime_smoke.js"
    if action_smoke_token not in ci:
        errors.append("ci.local.quick must run action_view_contract_action_runtime_smoke.js")
    navigation_smoke_token = "node scripts/verify/navigation_context_smoke.js"
    if navigation_smoke_token not in ci:
        errors.append("ci.local.quick must run navigation_context_smoke.js")

    if errors:
        print("[action_view_responsibility_map_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[action_view_responsibility_map_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
