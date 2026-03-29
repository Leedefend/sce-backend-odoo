#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


GENERIC_VIEW_SPECS: dict[str, tuple[str, ...]] = {
    "src/views/SceneView.vue": (
        "const pageGlobalActions = pageContract.globalActions;",
        ":disabled=\"status === 'loading' || action.disabled\"",
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/WorkbenchView.vue": (
        "const pageGlobalActions = pageContract.globalActions;",
        ":disabled=\"action.disabled\"",
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/PlaceholderView.vue": (
        "const pageGlobalActions = pageContract.globalActions;",
        ":disabled=\"action.disabled\"",
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/HomeView.vue": (
        "const pageGlobalActions = pageContract.globalActions;",
        ":disabled=\"action.disabled\"",
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/MyWorkView.vue": (
        "const pageGlobalActions = pageContract.globalActions;",
        ":disabled=\"action.disabled\"",
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/LoginView.vue": (
        "const pageGlobalActions = pageContract.globalActions;",
        ":disabled=\"loading || action.disabled\"",
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/MenuView.vue": (
        "const pageGlobalActions = pageContract.globalActions;",
        ":disabled=\"loading || action.disabled\"",
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/SceneHealthView.vue": (
        "const pageGlobalActions = pageContract.globalActions;",
        ":disabled=\"action.disabled\"",
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/ScenePackagesView.vue": (
        "const pageGlobalActions = pageContract.globalActions;",
        ":disabled=\"busy || action.disabled\"",
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/RecordView.vue": (
        "const pageGlobalActions = pageContract.globalActions;",
        ":disabled=\"status === 'loading' || status === 'saving' || action.disabled\"",
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/UsageAnalyticsView.vue": (
        "const pageGlobalActions = pageContract.globalActions;",
        ":disabled=\"loading || action.disabled\"",
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
}

ACTION_VIEW_SPEC: dict[str, tuple[str, ...]] = {
    "src/views/ActionView.vue": (
        "const pageGlobalActions = pageContract.globalActions;",
        "const displayHeaderActions = computed(() => {",
        ":disabled=\"action.enabled === false\"",
        ":title=\"action.hint || ''\"",
    ),
    "src/app/action_runtime/useActionViewHeaderRuntime.ts": (
        "isHeaderActionDisabled?: (actionKey: string) => boolean;",
        "onHeaderActionBlocked?: (actionKey: string) => void;",
        "options.isHeaderActionDisabled?.(",
        "options.onHeaderActionBlocked?.(",
    ),
}

GENERIC_VIEW_CONSISTENCY_SPECS: dict[str, tuple[str, ...]] = {
    "src/views/SceneView.vue": (
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/WorkbenchView.vue": (
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/PlaceholderView.vue": (
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/HomeView.vue": (
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/MyWorkView.vue": (
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/LoginView.vue": (
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/MenuView.vue": (
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/SceneHealthView.vue": (
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/ScenePackagesView.vue": (
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/RecordView.vue": (
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/UsageAnalyticsView.vue": (
        ":title=\"action.disabledReason || ''\"",
        "if (matched?.disabled) {",
    ),
    "src/views/ActionView.vue": (
        ":title=\"action.hint || ''\"",
        "onHeaderActionBlocked:",
        "batchMessage.value = matched?.hint || pageText('error_fallback', '操作暂不可用');",
    ),
}


def _check_file(root: Path, relative_path: str, tokens: tuple[str, ...]) -> dict[str, object]:
    path = root / relative_path
    if not path.exists():
        return {
            "path": relative_path,
            "exists": False,
            "covered": False,
            "missing_tokens": list(tokens),
        }

    content = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in content]
    return {
        "path": relative_path,
        "exists": True,
        "covered": not missing,
        "missing_tokens": missing,
    }


def evaluate_action_gating_coverage(frontend_dir: Path) -> dict[str, object]:
    targets: list[dict[str, object]] = []

    for relative_path, tokens in GENERIC_VIEW_SPECS.items():
        targets.append(_check_file(frontend_dir, relative_path, tokens))
    for relative_path, tokens in ACTION_VIEW_SPEC.items():
        targets.append(_check_file(frontend_dir, relative_path, tokens))

    view_targets = [item for item in targets if str(item["path"]).startswith("src/views/")]
    covered_views = [item for item in view_targets if item["covered"]]
    uncovered = [item for item in targets if not item["covered"]]

    payload: dict[str, object] = {
        "frontend_dir": str(frontend_dir),
        "status": "PASS" if not uncovered else "FAIL",
        "summary": {
            "view_targets": len(view_targets),
            "covered_views": len(covered_views),
            "supporting_targets": len(targets) - len(view_targets),
            "covered_targets": len([item for item in targets if item["covered"]]),
        },
        "targets": targets,
        "uncovered_targets": uncovered,
    }
    return payload


def evaluate_action_gating_consistency(frontend_dir: Path) -> dict[str, object]:
    targets = [_check_file(frontend_dir, relative_path, tokens) for relative_path, tokens in GENERIC_VIEW_CONSISTENCY_SPECS.items()]
    consistent = [item for item in targets if item["covered"]]
    inconsistent = [item for item in targets if not item["covered"]]
    return {
        "frontend_dir": str(frontend_dir),
        "mode": "consistency",
        "status": "PASS" if not inconsistent else "FAIL",
        "summary": {
            "targets": len(targets),
            "consistent_targets": len(consistent),
        },
        "targets": targets,
        "inconsistent_targets": inconsistent,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit frontend contract action-gating coverage.")
    parser.add_argument("--frontend-dir", default="frontend/apps/web", help="Frontend app directory.")
    parser.add_argument("--mode", choices=["coverage", "consistency"], default="coverage", help="Audit mode.")
    parser.add_argument("--expect-status", choices=["PASS", "FAIL"], help="Assert expected audit status.")
    parser.add_argument("--expect-covered-count", type=int, help="Assert expected covered view count.")
    parser.add_argument("--expect-consistent-count", type=int, help="Assert expected consistent target count.")
    args = parser.parse_args()

    frontend_dir = Path(args.frontend_dir).resolve()
    payload = (
        evaluate_action_gating_consistency(frontend_dir)
        if args.mode == "consistency"
        else evaluate_action_gating_coverage(frontend_dir)
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.expect_status and payload["status"] != args.expect_status:
        return 1
    if args.expect_covered_count is not None:
        actual = int(((payload.get("summary") or {}).get("covered_views")) or 0)
        if actual != args.expect_covered_count:
            return 1
    if args.expect_consistent_count is not None:
        actual = int(((payload.get("summary") or {}).get("consistent_targets")) or 0)
        if actual != args.expect_consistent_count:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
