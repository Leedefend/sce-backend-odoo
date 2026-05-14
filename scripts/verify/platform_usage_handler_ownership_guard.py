#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

PLATFORM_HANDLERS = {
    "usage.track": ROOT / "addons/smart_core/handlers/usage_track.py",
    "usage.report": ROOT / "addons/smart_core/handlers/usage_report.py",
    "usage.export.csv": ROOT / "addons/smart_core/handlers/usage_export_csv.py",
}
CONSTRUCTION_SHIMS = {
    "UsageTrackHandler": ROOT / "addons/smart_construction_core/handlers/usage_track.py",
    "UsageReportHandler": ROOT / "addons/smart_construction_core/handlers/usage_report.py",
    "UsageExportCsvHandler": ROOT / "addons/smart_construction_core/handlers/usage_export_csv.py",
}
CONSTRUCTION_EXTENSION = ROOT / "addons/smart_construction_core/core_extension.py"
SUDO_ALLOWLIST = ROOT / "scripts/verify/baselines/write_intent_sudo_allowlist.json"
USAGE_OWNERSHIP_DOCS = {
    "docs/audit/boundary/handler_inventory.md",
    "docs/audit/boundary/intent_semantic_classification.md",
    "docs/audit/boundary/module_dependency_graph.md",
    "docs/audit/boundary/core_extension_platform_intent_owner_mapping.md",
    "docs/ops/audit/intent_layered_catalog.md",
    "docs/ops/audit/intent_permission_matrix.md",
    "docs/ops/audit/intent_capability_matrix.md",
    "docs/ops/assessment/usage_track_serialization_issue_iteration_2026-03-14.md",
    "docs/ops/assessment/usage_track_serialization_issue_iteration_2026-03-14.en.md",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def main() -> int:
    errors: list[str] = []

    for intent, path in PLATFORM_HANDLERS.items():
        text = _read(path)
        if not text:
            errors.append(f"missing platform usage handler: {_rel(path)}")
            continue
        if f'INTENT_TYPE = "{intent}"' not in text:
            errors.append(f"{_rel(path)} missing INTENT_TYPE {intent}")

    extension = _read(CONSTRUCTION_EXTENSION)
    for token in [
        "UsageTrackHandler",
        "UsageReportHandler",
        "UsageExportCsvHandler",
        '"usage.track"',
        '"usage.report"',
        '"usage.export.csv"',
    ]:
        if token in extension:
            errors.append(f"{_rel(CONSTRUCTION_EXTENSION)} still contributes platform usage token: {token}")

    for handler_name, path in CONSTRUCTION_SHIMS.items():
        text = _read(path)
        if not text:
            errors.append(f"missing construction compatibility shim: {_rel(path)}")
            continue
        if "odoo.addons.smart_core.handlers." not in text:
            errors.append(f"{_rel(path)} does not delegate to smart_core handler")
        if f"class {handler_name}" in text:
            errors.append(f"{_rel(path)} still defines {handler_name} implementation")

    allowlist = _read(SUDO_ALLOWLIST)
    if "addons/smart_core/handlers/usage_track.py" not in allowlist:
        errors.append(f"{_rel(SUDO_ALLOWLIST)} must allowlist platform usage_track.py")
    if "addons/smart_construction_core/handlers/usage_track.py" in allowlist:
        errors.append(f"{_rel(SUDO_ALLOWLIST)} still allowlists construction usage_track.py")

    for rel_path in sorted(USAGE_OWNERSHIP_DOCS):
        path = ROOT / rel_path
        text = _read(path)
        if not text:
            errors.append(f"missing usage ownership doc: {rel_path}")
            continue
        if "smart_construction_core.handlers.usage_" in text:
            errors.append(f"{rel_path} still documents usage handler as construction implementation")
        for file_name in ("usage_track.py", "usage_report.py", "usage_export_csv.py"):
            stale_path = f"addons/smart_construction_core/handlers/{file_name}"
            if stale_path in text and "compatibility shim" not in text:
                errors.append(f"{rel_path} still references {stale_path} without compatibility-shim context")

    if errors:
        print("[platform_usage_handler_ownership_guard] FAIL")
        for err in errors:
            print(err)
        return 1
    print("[platform_usage_handler_ownership_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
