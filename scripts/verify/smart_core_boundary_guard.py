#!/usr/bin/env python3
"""Guard the addon-level smart_core platform boundary."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SMART_CORE = ROOT / "addons" / "smart_core"
DOC = ROOT / "docs" / "architecture" / "smart_core_boundary_v1.md"
MANIFEST = SMART_CORE / "__manifest__.py"
APP_CONFIG_DOC = SMART_CORE / "app_config_engine" / "docs" / "app_config_engine.md"
APP_CONFIG_GUARD = ROOT / "scripts" / "verify" / "app_config_engine_boundary_guard.py"
INDUSTRY_COMPAT = SMART_CORE / "utils" / "industry_compatibility.py"

REQUIRED_DIRS = {
    "controllers",
    "handlers",
    "core",
    "app_config_engine",
    "model",
    "models",
    "delivery",
    "governance",
    "orchestration",
    "runtime",
    "security",
    "identity",
    "adapters",
    "utils",
    "view",
    "data",
    "views",
    "tests",
}

REQUIRED_DOC_TOKENS = (
    "Platform Contract",
    "Directory Ownership",
    "Authority Layers",
    "Native Odoo Authority",
    "Business Configuration Authority",
    "Runtime Contract Authority",
    "Delivery Authority",
    "Extension Authority",
    "No Industry Defaults",
    "Extension Hook Authority",
    "Form/List/Search Productization Boundary",
    "Record Context Boundary",
    "`ui.business.config.contract`",
    "`ViewOrchestrator`",
    "`app_config_engine`",
    "`selected_record_context_id_from_context`",
    "`record_scope_policy`",
    "`current_record`",
    "`make verify.smart_core.boundary_guard`",
    "does not depend on `smart_construction_core`",
)

FORBIDDEN_PRODUCTION_TOKENS = (
    "smart_construction_core",
    "industry_compatibility",
    "legacy_construction",
    "construction_source",
    "construction.standard",
    "智慧施工管理平台",
    "用户验收",
    "用户数据验收",
    "用户核对菜单",
    "project.group_project_manager",
    "CONSTRUCTION_",
)

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _parse_manifest() -> dict:
    return ast.literal_eval(_read(MANIFEST))


def _industry_refs(source: str) -> set[str]:
    refs: set[str] = set()
    marker = "smart_construction_core."
    start = 0
    while True:
        idx = source.find(marker, start)
        if idx < 0:
            break
        end = idx
        while end < len(source) and (source[end].isalnum() or source[end] in "._"):
            end += 1
        refs.add(source[idx:end])
        start = end
    return refs


def _iter_production_python_files():
    for path in sorted(SMART_CORE.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if "/tests/" in rel or "/__pycache__/" in rel:
            continue
        yield path


def _legacy_context_entrypoint_violations(path: Path, source: str) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "addons/smart_core/core/project_context.py":
        return []
    violations: list[str] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        if "selected_project_id_from_context" not in line:
            continue
        if "as selected_record_context_id_from_context" in line:
            continue
        violations.append(f"{rel}:{lineno}: selected_project_id_from_context")
    return violations


def _legacy_scope_helper_violations(path: Path, source: str) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "addons/smart_core/core/project_context.py":
        return []
    allowed_fragments = (
        "project_scope_denied_response as record_scope_denied_response",
        "from ..core.project_context import record_in_project_scope",
        "from ..core.project_context import apply_project_scope_domain",
        "return record_in_project_scope(env_model, record_id, selected_record_context_id_from_context(params, context))",
        "return apply_project_scope_domain(env_model, domain, selected_record_context_id_from_context(params, context))",
    )
    guarded_names = (
        "project_scope_denied_response",
        "record_in_project_scope",
        "apply_project_scope_domain",
    )
    violations: list[str] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        if not any(name in line for name in guarded_names):
            continue
        if any(fragment in line for fragment in allowed_fragments):
            continue
        violations.append(f"{rel}:{lineno}: {line.strip()}")
    return violations


def _legacy_menu_scope_policy_violations(path: Path, source: str) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    allowed_files = {
        "addons/smart_core/core/delivery_menu_defaults.py",
        "addons/smart_core/delivery/menu_service.py",
        "addons/smart_core/app_config_engine/services/dispatchers/nav_dispatcher.py",
    }
    if rel in allowed_files:
        return []
    violations: list[str] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        if "project_scope_policy" in line:
            violations.append(f"{rel}:{lineno}: project_scope_policy")
    return violations


def main() -> int:
    errors: list[str] = []
    doc = _read(DOC)

    for token in REQUIRED_DOC_TOKENS:
        _require(errors, token in doc, f"smart_core boundary doc missing token: {token}")

    for dirname in REQUIRED_DIRS:
        _require(errors, (SMART_CORE / dirname).is_dir(), f"smart_core required directory missing: {dirname}")
        _require(errors, f"`{dirname}`" in doc, f"smart_core boundary doc missing directory row: {dirname}")

    manifest = _parse_manifest()
    depends = set(manifest.get("depends") or [])
    _require(errors, "smart_construction_core" not in depends, "smart_core manifest must not depend on smart_construction_core")
    _require(errors, {"base", "web"}.issubset(depends), "smart_core manifest must keep base/web platform dependencies")

    _require(errors, APP_CONFIG_DOC.exists(), "app_config_engine boundary document missing")
    _require(errors, APP_CONFIG_GUARD.exists(), "app_config_engine boundary guard missing")
    _require(errors, not INDUSTRY_COMPAT.exists(), "smart_core must not keep an industry compatibility layer")

    refs_by_file: dict[str, list[str]] = {}
    token_violations: list[str] = []
    legacy_context_violations: list[str] = []
    legacy_scope_violations: list[str] = []
    legacy_menu_scope_violations: list[str] = []
    for path in _iter_production_python_files():
        text = _read(path)
        rel = path.relative_to(ROOT).as_posix()
        for token in FORBIDDEN_PRODUCTION_TOKENS:
            if token in text:
                token_violations.append(f"{rel}: {token}")
        legacy_context_violations.extend(_legacy_context_entrypoint_violations(path, text))
        legacy_scope_violations.extend(_legacy_scope_helper_violations(path, text))
        legacy_menu_scope_violations.extend(_legacy_menu_scope_policy_violations(path, text))
        refs = sorted(_industry_refs(text))
        if refs:
            refs_by_file[rel] = refs
    unexpected: list[str] = []
    for rel, refs in refs_by_file.items():
        for ref in refs:
            unexpected.append(f"{rel}: {ref}")
    _require(
        errors,
        not unexpected,
        "direct smart_construction_core.* production references must move to extension hooks/config: %s"
        % "; ".join(unexpected),
    )
    _require(
        errors,
        not token_violations,
        "smart_core production code contains forbidden industry/default tokens: %s"
        % "; ".join(token_violations),
    )
    _require(
        errors,
        not legacy_context_violations,
        "smart_core production code must use selected_record_context_id_from_context; "
        "selected_project_id_from_context is only allowed as a compatibility alias: %s"
        % "; ".join(legacy_context_violations),
    )
    _require(
        errors,
        not legacy_scope_violations,
        "smart_core production code must use record/business scope helpers; legacy project scope helpers "
        "are only allowed in fallback aliases: %s" % "; ".join(legacy_scope_violations),
    )
    _require(
        errors,
        not legacy_menu_scope_violations,
        "smart_core production code must expose record_scope_policy as the primary menu scope contract; "
        "project_scope_policy is only allowed in menu/navigation compatibility bridges: %s"
        % "; ".join(legacy_menu_scope_violations),
    )

    if errors:
        print("[smart_core_boundary_guard] FAIL")
        for error in errors:
            print(error)
        return 2

    ref_count = sum(len(refs) for refs in refs_by_file.values())
    print(
        "[smart_core_boundary_guard] PASS "
        f"directories={len(REQUIRED_DIRS)} industry_default_files={len(refs_by_file)} "
        f"industry_default_refs={ref_count} centralized_compatibility_layer=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
