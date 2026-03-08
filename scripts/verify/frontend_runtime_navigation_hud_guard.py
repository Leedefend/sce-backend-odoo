#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_SHELL = ROOT / "frontend/apps/web/src/layouts/AppShell.vue"
NAV_REGISTRY = ROOT / "frontend/apps/web/src/app/navigationRegistry.ts"
REPORT_JSON = ROOT / "artifacts/backend/frontend_runtime_navigation_hud_report.json"
REPORT_MD = ROOT / "docs/ops/audit/frontend_runtime_navigation_hud_report.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _missing(text: str, tokens: list[str]) -> list[str]:
    return [token for token in tokens if token not in text]


def main() -> int:
    shell_text = _read(APP_SHELL)
    registry_text = _read(NAV_REGISTRY)
    errors: list[str] = []

    if not shell_text:
        errors.append(f"missing file: {APP_SHELL.relative_to(ROOT).as_posix()}")
    if not registry_text:
        errors.append(f"missing file: {NAV_REGISTRY.relative_to(ROOT).as_posix()}")

    shell_tokens = [
        "buildRuntimeNavigationRegistry(",
        "entry_source",
        "nav_entry_total",
        "nav_scene_entries",
        "nav_cap_entries",
    ]
    registry_tokens = [
        "export type NavigationEntrySource = 'scene' | 'capability';",
        "export interface RuntimeNavigationEntry",
        "export interface RuntimeNavigationRegistry",
        "export function buildRuntimeNavigationRegistry(",
        "registryKey: `nav.scene::${sceneKey}`",
        "registryKey: `nav.capability::${key}`",
    ]

    shell_missing = _missing(shell_text, shell_tokens)
    registry_missing = _missing(registry_text, registry_tokens)
    errors.extend([f"AppShell.vue missing token: {token}" for token in shell_missing])
    errors.extend([f"navigationRegistry.ts missing token: {token}" for token in registry_missing])

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "checked_files": 2,
            "shell_tokens_expected": len(shell_tokens),
            "shell_tokens_found": len(shell_tokens) - len(shell_missing),
            "registry_tokens_expected": len(registry_tokens),
            "registry_tokens_found": len(registry_tokens) - len(registry_missing),
        },
        "errors": errors,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Frontend Runtime Navigation HUD Guard Report",
        "",
        f"- ok: `{report['ok']}`",
        f"- checked_files: `{report['summary']['checked_files']}`",
        f"- shell_tokens_found: `{report['summary']['shell_tokens_found']}/{report['summary']['shell_tokens_expected']}`",
        f"- registry_tokens_found: `{report['summary']['registry_tokens_found']}/{report['summary']['registry_tokens_expected']}`",
    ]
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {error}" for error in errors])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[frontend_runtime_navigation_hud_guard] FAIL")
        return 1
    print("[frontend_runtime_navigation_hud_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
