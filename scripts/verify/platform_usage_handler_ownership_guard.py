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

    if errors:
        print("[platform_usage_handler_ownership_guard] FAIL")
        for err in errors:
            print(err)
        return 1
    print("[platform_usage_handler_ownership_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
