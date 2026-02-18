#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts/verify/baselines/boundary_import_guard.json"
ARTIFACT_JSON = ROOT / "artifacts/backend/boundary_import_guard_report.json"
ARTIFACT_MD = ROOT / "artifacts/backend/boundary_import_guard_report.md"

IMPORT_RE = re.compile(
    r"(?:from\s+odoo\.addons\.(?P<from_mod>[a-zA-Z0-9_]+)\s+import)"
    r"|(?:import\s+odoo\.addons\.(?P<import_mod>[a-zA-Z0-9_]+))"
)


def _iter_py_files(base: Path):
    for path in base.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if "/tests/" in rel or "/docs/" in rel or "/migrations/" in rel:
            continue
        yield path


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _to_str_set(items) -> set[str]:
    out: set[str] = set()
    for item in items if isinstance(items, list) else []:
        value = str(item or "").strip()
        if value:
            out.add(value)
    return out


def _parse_manifest_depends(module_name: str) -> list[str]:
    path = ROOT / "addons" / module_name / "__manifest__.py"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    left = text.find("{")
    right = text.rfind("}")
    if left < 0 or right <= left:
        return []
    try:
        payload = ast.literal_eval(text[left : right + 1])
    except Exception:
        return []
    if not isinstance(payload, dict):
        return []
    depends = payload.get("depends")
    return sorted(_to_str_set(depends))


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    source_roots = [str(item).strip() for item in baseline.get("source_roots", []) if str(item).strip()]
    import_policy_raw = baseline.get("forbidden_imports", {})
    manifest_policy_raw = baseline.get("forbidden_manifest_depends", {})
    required_manifest_depends_raw = baseline.get("required_manifest_depends", {})
    tracked_modules = [str(item).strip() for item in baseline.get("tracked_modules", []) if str(item).strip()]

    if not source_roots or not isinstance(import_policy_raw, dict) or not isinstance(manifest_policy_raw, dict):
        print("[boundary_import_guard] FAIL")
        print("invalid or missing policy baseline: scripts/verify/baselines/boundary_import_guard.json")
        return 1

    policy: dict[str, set[str]] = {
        root: _to_str_set(import_policy_raw.get(root))
        for root in source_roots
    }
    forbidden_manifest_depends: dict[str, set[str]] = {
        module: _to_str_set(depends)
        for module, depends in manifest_policy_raw.items()
        if str(module).strip()
    }
    required_manifest_depends: dict[str, set[str]] = {
        module: _to_str_set(depends)
        for module, depends in required_manifest_depends_raw.items()
        if str(module).strip()
    }

    violations: list[str] = []
    warnings: list[str] = []
    import_hit_count = 0
    manifest_hit_count = 0

    for src_root, forbidden in policy.items():
        base = ROOT / src_root
        if not base.is_dir():
            warnings.append(f"missing source root: {src_root}")
            continue
        for file_path in _iter_py_files(base):
            rel = file_path.relative_to(ROOT).as_posix()
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            for m in IMPORT_RE.finditer(text):
                mod = m.group("from_mod") or m.group("import_mod")
                if mod in forbidden:
                    import_hit_count += 1
                    violations.append(f"{rel}: forbidden import -> odoo.addons.{mod}")

    modules_for_manifest = sorted(set(tracked_modules) | set(forbidden_manifest_depends.keys()) | set(required_manifest_depends.keys()))
    manifest_observed: dict[str, list[str]] = {}
    for module in modules_for_manifest:
        depends = _parse_manifest_depends(module)
        if not depends:
            warnings.append(f"manifest depends missing or empty: addons/{module}/__manifest__.py")
        manifest_observed[module] = depends
        forbidden_depends = forbidden_manifest_depends.get(module) or set()
        required_depends = required_manifest_depends.get(module) or set()
        for dep in sorted(set(depends) & forbidden_depends):
            manifest_hit_count += 1
            violations.append(f"addons/{module}/__manifest__.py: forbidden depends -> {dep}")
        for dep in sorted(required_depends - set(depends)):
            violations.append(f"addons/{module}/__manifest__.py: required depends missing -> {dep}")

    payload = {
        "ok": len(violations) == 0,
        "summary": {
            "source_root_count": len(source_roots),
            "tracked_module_count": len(modules_for_manifest),
            "import_violation_count": import_hit_count,
            "manifest_violation_count": manifest_hit_count,
            "warning_count": len(warnings),
            "violation_count": len(violations),
        },
        "manifest_depends": manifest_observed,
        "violations": violations,
        "warnings": warnings,
    }
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Boundary Import Guard Report",
        "",
        f"- status: {'PASS' if payload['ok'] else 'FAIL'}",
        f"- source_root_count: {payload['summary']['source_root_count']}",
        f"- tracked_module_count: {payload['summary']['tracked_module_count']}",
        f"- import_violation_count: {payload['summary']['import_violation_count']}",
        f"- manifest_violation_count: {payload['summary']['manifest_violation_count']}",
        f"- warning_count: {payload['summary']['warning_count']}",
        f"- violation_count: {payload['summary']['violation_count']}",
    ]
    if warnings:
        lines.extend(["", "## Warnings", ""])
        for item in warnings[:100]:
            lines.append(f"- {item}")
    if violations:
        lines.extend(["", "## Violations", ""])
        for item in violations[:200]:
            lines.append(f"- {item}")
    ARTIFACT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(ARTIFACT_JSON))
    print(str(ARTIFACT_MD))

    if violations:
        print("[boundary_import_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[boundary_import_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
