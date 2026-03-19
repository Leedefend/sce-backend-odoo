#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
WORKBENCH_VIEW = ROOT / "frontend/apps/web/src/views/WorkbenchView.vue"
ACTION_VIEW = ROOT / "frontend/apps/web/src/views/ActionView.vue"
ACTION_SURFACE_CONTRACT = ROOT / "frontend/apps/web/src/app/contracts/actionViewSurfaceContract.ts"
ACTION_PAGE_DISPLAY_RUNTIME = ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewPageDisplayStateRuntime.ts"
SCENE_VIEW = ROOT / "frontend/apps/web/src/views/SceneView.vue"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _fail(errors: list[str]) -> int:
    print("[frontend_contract_text_hardcode_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    errors: list[str] = []

    checks: list[tuple[Path, list[str], list[str]]] = [
        (
            WORKBENCH_VIEW,
            [
                "const pageText = pageContract.text;",
                "pageText('message_act_unsupported_type'",
                "pageText('message_capability_missing'",
            ],
            [
                "当前动作类型暂未在门户壳层支持。",
                "当前账号尚未开通该能力。",
            ],
        ),
        (
            ACTION_VIEW,
            [
                "const pageText = pageContract.text;",
                "const { t } = useActionViewTextRuntime({ pageText });",
                "useActionViewPageDisplayStateRuntime({",
                "emptyReasonText",
            ],
            [
                "当前视图暂无数据",
                "建议切换到我的工作或风险驾驶舱继续处理。",
                "可能因为暂无业务数据、当前角色权限受限，或数据尚未生成。",
            ],
        ),
        (
            ACTION_SURFACE_CONTRACT,
            [
                "options.pageText('empty_title_default'",
                "options.pageText('empty_hint_default'",
            ],
            [
                "当前视图暂无数据",
                "建议切换到我的工作或风险驾驶舱继续处理。",
            ],
        ),
        (
            ACTION_PAGE_DISPLAY_RUNTIME,
            [
                "options.t('empty_reason_default'",
            ],
            [
                "可能因为暂无业务数据、当前角色权限受限，或数据尚未生成。",
            ],
        ),
        (
            SCENE_VIEW,
            [
                "const pageText = pageContract.text;",
                "pageText('error_scene_target_unsupported'",
            ],
            [
                "scene target unsupported",
            ],
        ),
    ]

    for path, required_tokens, forbidden_literals in checks:
        text = _read(path)
        rel = path.relative_to(ROOT).as_posix()
        if not text:
            errors.append(f"missing file: {rel}")
            continue
        for token in required_tokens:
            if token not in text:
                errors.append(f"{rel} missing token: {token}")
        for literal in forbidden_literals:
            if literal in text:
                errors.append(f"{rel} contains forbidden hardcoded literal: {literal}")

    if errors:
        return _fail(errors)

    print("[frontend_contract_text_hardcode_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
