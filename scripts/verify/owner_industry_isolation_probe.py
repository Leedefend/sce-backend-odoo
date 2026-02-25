#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OWNER_ROOT = ROOT / "addons" / "smart_owner_core"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "owner_industry_isolation_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "owner_industry_isolation_report.json"

REQUIRED_FILES = [
    OWNER_ROOT / "__init__.py",
    OWNER_ROOT / "__manifest__.py",
    OWNER_ROOT / "core_extension.py",
    OWNER_ROOT / "handlers" / "__init__.py",
    OWNER_ROOT / "handlers" / "owner_payment_request.py",
    OWNER_ROOT / "services" / "__init__.py",
    OWNER_ROOT / "services" / "capability_registry_owner.py",
    OWNER_ROOT / "services" / "scene_registry_owner.py",
]

FORBIDDEN_IMPORT_TOKENS = (
    "odoo.addons.smart_core.handlers.system_init",
    "odoo.addons.smart_core.runtime.scene_runtime_orchestrator",
    "odoo.addons.smart_core.core.scene_runtime_orchestrator",
)


def _collect_imports(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except Exception:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(str(alias.name or ""))
        elif isinstance(node, ast.ImportFrom):
            base = str(node.module or "")
            imports.append(base)
    return imports


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    import_hits: dict[str, list[str]] = {}

    for req in REQUIRED_FILES:
        if not req.is_file():
            errors.append(f"missing required file: {req.relative_to(ROOT).as_posix()}")

    py_files = sorted(OWNER_ROOT.rglob("*.py")) if OWNER_ROOT.is_dir() else []
    for path in py_files:
        imports = _collect_imports(path)
        rel = path.relative_to(ROOT).as_posix()
        import_hits[rel] = imports
        for token in FORBIDDEN_IMPORT_TOKENS:
            if any(token in item for item in imports):
                errors.append(f"{rel}: forbidden import detected: {token}")

    core_extension_file = OWNER_ROOT / "core_extension.py"
    if core_extension_file.is_file():
        text = core_extension_file.read_text(encoding="utf-8")
        if "def smart_core_register" not in text:
            errors.append("core_extension.py missing smart_core_register")
        if "def smart_core_extend_system_init" not in text:
            errors.append("core_extension.py missing smart_core_extend_system_init")
    else:
        errors.append("core_extension.py missing")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "owner_file_count": len(py_files),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
        "imports": import_hits,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Owner Industry Isolation Report",
        "",
        f"- owner_file_count: {payload['summary']['owner_file_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        f"- warning_count: {payload['summary']['warning_count']}",
        "",
        "## Errors",
        "",
    ]
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
        print("[owner_industry_isolation_probe] FAIL")
        return 2
    print("[owner_industry_isolation_probe] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
