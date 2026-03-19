#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List


ROOT = Path(__file__).resolve().parents[2]
ACTION_VIEW = ROOT / "frontend/apps/web/src/views/ActionView.vue"
REPORT_JSON = ROOT / "artifacts/backend/frontend_actionview_scene_specialcase_guard_report.json"
REPORT_MD = ROOT / "docs/ops/audit/frontend_actionview_scene_specialcase_guard_report.md"

RUNTIME_IMPORT_PATTERN = re.compile(r"from '../app/runtime/([^']+)';")


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _check_required_tokens(path: Path, text: str, tokens: List[str], errors: List[str]) -> None:
    if not text:
        errors.append(f"missing file: {path.relative_to(ROOT)}")
        return
    for token in tokens:
        if token not in text:
            errors.append(f"missing required token in {path.relative_to(ROOT)}: {token}")


def _check_forbidden_tokens(path: Path, text: str, tokens: List[str], errors: List[str]) -> None:
    if not text:
        return
    for token in tokens:
        if token in text:
            errors.append(f"forbidden token present in {path.relative_to(ROOT)}: {token}")


def main() -> int:
    errors: List[str] = []
    action_view_text = _read(ACTION_VIEW)

    required_action_view_tokens = [
        "let loadPageInvoker: () => Promise<void> = async () => {};",
        "function requestLoadPage(): Promise<void>",
        "let clearSelectionInvoker: () => void = () => {};",
        "function clearSelection(): void",
        "const {",
        "loadPage,",
        "} = useActionViewLoadFacadeRuntime({",
        "loadPageInvoker = loadPage;",
        "clearSelection: selectionRuntimeClearSelection,",
        "clearSelectionInvoker = selectionRuntimeClearSelection;",
        "load: requestLoadPage,",
        "clearSelection,",
        "useActionViewSelectionRuntime({",
    ]

    forbidden_action_view_tokens = [
        "from '../app/assemblers/action/useActionView",
        "function handleSearch(",
        "function handleSort(",
        "function handleFilter(",
    ]

    _check_required_tokens(ACTION_VIEW, action_view_text, required_action_view_tokens, errors)
    _check_forbidden_tokens(ACTION_VIEW, action_view_text, forbidden_action_view_tokens, errors)

    runtime_modules = sorted(set(RUNTIME_IMPORT_PATTERN.findall(action_view_text)))
    runtime_files = [ROOT / f"frontend/apps/web/src/app/runtime/{module}.ts" for module in runtime_modules]

    if not runtime_modules:
        errors.append("missing runtime imports in frontend/apps/web/src/views/ActionView.vue")

    for runtime_file in runtime_files:
        if not runtime_file.is_file():
            errors.append(f"missing file: {runtime_file.relative_to(ROOT)}")

    files = [ACTION_VIEW, *runtime_files]
    payload = {
        "ok": not errors,
        "check": "verify.frontend.actionview.scene_specialcase.guard",
        "files": [str(path.relative_to(ROOT)) for path in files],
        "errors": errors,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Frontend ActionView Scene Specialcase Guard Report",
        "",
        f"- ok: {str(payload['ok']).lower()}",
        f"- check: {payload['check']}",
        "- files:",
    ]
    for path in payload["files"]:
        lines.append(f"  - {path}")
    if errors:
        lines.append("- errors:")
        for err in errors:
            lines.append(f"  - {err}")
    else:
        lines.append("- errors: []")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if errors:
        print("[verify.frontend.actionview.scene_specialcase.guard] FAIL")
        for err in errors:
            print(f" - {err}")
        return 2

    print("[verify.frontend.actionview.scene_specialcase.guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
