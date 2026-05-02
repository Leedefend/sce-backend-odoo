#!/usr/bin/env python3
"""Guard that Lite transformers are only connected through approved opt-in entries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
NEEDLES = (
    "unified_page_contract_lite_adapter",
    "build_lite_contract",
    "build_lite_patch",
    "unified_page_contract_lite_source_normalizer",
    "normalize_lite_contract_source",
    "unified_page_contract_lite_patch_normalizer",
    "normalize_lite_patch_source",
    "unified_page_contract_lite_preview",
    "with_lite_preview_if_requested",
)
EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "artifacts",
    "node_modules",
    "venv",
    ".venv",
}
TEXT_SUFFIXES = {
    ".cfg",
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".rst",
    ".scss",
    ".ts",
    ".tsx",
    ".txt",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
}
ALLOWED_EXACT = {
    "Makefile",
    "addons/smart_core/core/unified_page_contract_lite_adapter.py",
    "addons/smart_core/core/unified_page_contract_lite_source_normalizer.py",
    "addons/smart_core/core/unified_page_contract_lite_patch_normalizer.py",
    "addons/smart_core/core/unified_page_contract_lite_preview.py",
    "addons/smart_core/handlers/api_onchange.py",
    "addons/smart_core/handlers/load_contract.py",
    "scripts/verify/unified_page_contract_lite_adapter_guard.py",
    "scripts/verify/unified_page_contract_lite_runtime_boundary_guard.py",
    "scripts/verify/unified_page_contract_lite_source_normalizer_guard.py",
    "scripts/verify/unified_page_contract_lite_patch_normalizer_guard.py",
    "scripts/verify/unified_page_contract_lite_pipeline_guard.py",
    "scripts/verify/unified_page_contract_lite_phase1_readiness_guard.py",
    "scripts/verify/unified_page_contract_lite_integration_plan_guard.py",
    "scripts/verify/unified_page_contract_lite_api_onchange_preview_guard.py",
    "scripts/verify/unified_page_contract_lite_api_onchange_preview_behavior_guard.py",
    "docs/ops/iterations/delivery_context_switch_log_v1.md",
}
ALLOWED_PREFIXES = (
    "docs/architecture/unified_page_contract_lite/",
)
RUNTIME_FORBIDDEN_PREFIXES = (
    "addons/smart_core/handlers/",
    "addons/smart_core/controllers/",
    "addons/smart_core/models/",
    "frontend/",
)


def is_text_candidate(path: Path) -> bool:
    if path.name in {"Makefile"}:
        return True
    return path.suffix in TEXT_SUFFIXES


def iter_files(root: Path):
    for path in root.rglob("*"):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file() and is_text_candidate(path):
            yield path


def is_allowed_reference(relative_path: str) -> bool:
    if relative_path in ALLOWED_EXACT:
        return True
    return any(relative_path.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def classify_reference(relative_path: str) -> str:
    if is_allowed_reference(relative_path):
        return "allowed"
    if any(relative_path.startswith(prefix) for prefix in RUNTIME_FORBIDDEN_PREFIXES):
        return "runtime_forbidden"
    return "unexpected"


def find_references() -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    for path in iter_files(ROOT):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        matched = sorted({needle for needle in NEEDLES if needle in text})
        if not matched:
            continue
        relative_path = path.relative_to(ROOT).as_posix()
        references.append(
            {
                "path": relative_path,
                "needles": matched,
                "classification": classify_reference(relative_path),
            }
        )
    return sorted(references, key=lambda item: item["path"])


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()

    references = find_references()
    violations = [
        reference
        for reference in references
        if reference["classification"] in {"runtime_forbidden", "unexpected"}
    ]
    report = {
        "ok": not violations,
        "policy": "Lite adapter and normalizers must remain offline until an explicit runtime integration batch",
        "needles": list(NEEDLES),
        "reference_count": len(references),
        "violation_count": len(violations),
        "references": references,
        "violations": violations,
    }
    if args.report:
        write_report(args.report, report)

    if violations:
        print("Unified Semantic Page Contract Lite runtime boundary guard failed:")
        for violation in violations:
            print(f"- {violation['classification']}: {violation['path']} -> {', '.join(violation['needles'])}")
        if args.report:
            print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite runtime boundary guard passed")
    print(f"- references scanned: {len(references)}")
    if args.report:
        print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
