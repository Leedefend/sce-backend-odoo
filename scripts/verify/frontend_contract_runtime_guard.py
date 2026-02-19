#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
WEB_SRC = ROOT / "frontend/apps/web/src"
PATTERNS = [
    "intent: 'load_view'",
    'intent: "load_view"',
    "resolveView(",
    "viewResolver",
    "fallback_fields",
    "pickColumns(",
    "actionMeta.value?.view_modes?.[0]",
    "/s/projects.list",
    "legacy_list_without_action",
    "config/scenesCore",
    "config/scenes'",
    'config/scenes"',
    "path: '/projects'",
    "path: '/projects/:id'",
    "appendQuery('/projects'",
    "appendQuery(`/projects/",
    "pending_approval",
    "project_intake",
    "cost_watchlist",
]

ACTION_VIEW_ONLY_PATTERNS = [
    "(action.view_modes?.[0] ?? 'tree')",
]

SESSION_STORE_ONLY_PATTERNS = [
    "menuTree?: NavNode[]",
    "menu_tree?: NavNode[]",
    "menus?: NavNode[]",
    "sections?: NavNode[]",
    "loadNavFallback(",
]

SCENE_VIEW_ONLY_PATTERNS = [
    "findActionNodeByModel(",
]

ACTION_CONTEXT_ONLY_PATTERNS = [
    "meta.view_modes",
]

CONTRACT_RECORD_RUNTIME_PATTERNS = [
    "...Object.keys(fields)",
]


def iter_files():
    if not WEB_SRC.is_dir():
        return
    for ext in ("*.ts", "*.tsx", "*.js", "*.jsx", "*.vue"):
        yield from WEB_SRC.rglob(ext)


def main() -> int:
    violations: list[str] = []
    scanned = 0
    for path in iter_files():
        scanned += 1
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in PATTERNS:
            if pattern in text:
                violations.append(f"{rel}: forbidden legacy view runtime token: {pattern}")
        if rel.endswith("views/ActionView.vue"):
            for pattern in ACTION_VIEW_ONLY_PATTERNS:
                if pattern in text:
                    violations.append(f"{rel}: forbidden ActionView preset token: {pattern}")
        if rel.endswith("stores/session.ts"):
            for pattern in SESSION_STORE_ONLY_PATTERNS:
                if pattern in text:
                    violations.append(f"{rel}: forbidden session fallback token: {pattern}")
        if rel.endswith("views/SceneView.vue"):
            for pattern in SCENE_VIEW_ONLY_PATTERNS:
                if pattern in text:
                    violations.append(f"{rel}: forbidden scene fallback token: {pattern}")
        if rel.endswith("app/actionContext.ts"):
            for pattern in ACTION_CONTEXT_ONLY_PATTERNS:
                if pattern in text:
                    violations.append(f"{rel}: forbidden action-context fallback token: {pattern}")
        if rel.endswith("app/contractRecordRuntime.ts"):
            for pattern in CONTRACT_RECORD_RUNTIME_PATTERNS:
                if pattern in text:
                    violations.append(f"{rel}: forbidden record-runtime fallback token: {pattern}")

    if violations:
        print("[frontend_contract_runtime_guard] FAIL")
        for line in violations:
            print(line)
        return 1

    print("[frontend_contract_runtime_guard] PASS")
    print(f"scanned_files={scanned}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
