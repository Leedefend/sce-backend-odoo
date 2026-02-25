#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "kernel_freeze_guard_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "kernel_freeze_guard_report.json"
KERNEL_SURFACE_DOC = ROOT / "docs" / "kernel_surface.md"

PROTECTED_PREFIXES = [
    "addons/smart_core/core/",
    "addons/smart_core/governance/",
    "addons/smart_core/runtime/",
    "addons/smart_core/controllers/intent_dispatcher.py",
    "addons/smart_core/handlers/system_init.py",
    "addons/smart_core/core/base_handler.py",
    "addons/smart_core/core/intent_router.py",
]


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    return (result.stdout or "").strip()


def _changed_files() -> list[str]:
    out = _run(["git", "diff", "--name-only", "origin/main...HEAD"])
    rows = [line.strip() for line in out.splitlines() if line.strip()]
    return sorted(set(rows))


def _is_protected(path: str) -> bool:
    for prefix in PROTECTED_PREFIXES:
        if path == prefix or path.startswith(prefix):
            return True
    return False


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if not KERNEL_SURFACE_DOC.is_file():
        errors.append("missing docs/kernel_surface.md")

    branch = _run(["git", "branch", "--show-current"])
    if not branch.startswith(("codex/", "feat/", "feature/", "experiment/")):
        errors.append(f"branch not allowed for freeze guard: {branch or '-'}")

    changed = _changed_files()
    protected_changes = [p for p in changed if _is_protected(p)]

    label = str(os.getenv("KERNEL_FREEZE_LABEL") or "").strip().lower()
    allow = str(os.getenv("KERNEL_FREEZE_ALLOW") or "0").strip() == "1"
    override_ok = allow or label == "kernel-approved"
    if protected_changes and not override_ok:
        errors.append("kernel protected paths changed without kernel-approved override")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "branch": branch,
            "changed_count": len(changed),
            "protected_change_count": len(protected_changes),
            "override": "enabled" if override_ok else "disabled",
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "protected_changes": protected_changes,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Kernel Freeze Guard Report",
        "",
        f"- branch: {branch}",
        f"- changed_count: {len(changed)}",
        f"- protected_change_count: {len(protected_changes)}",
        f"- override: {'enabled' if override_ok else 'disabled'}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## Protected Changes",
        "",
    ]
    if protected_changes:
        for item in protected_changes:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## Errors", ""])
    if errors:
        for item in errors:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        for item in warnings:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[kernel_freeze_guard] FAIL")
        return 2
    print("[kernel_freeze_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
