#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
USAGE_API = ROOT / "frontend/apps/web/src/api/usage.ts"
TELEMETRY_API = ROOT / "frontend/apps/web/src/api/telemetry.ts"
USAGE_HANDLER = ROOT / "addons/smart_construction_core/handlers/usage_track.py"
TELEMETRY_HANDLER = ROOT / "addons/smart_construction_core/handlers/telemetry_track.py"
REPORT_JSON = ROOT / "artifacts/backend/usage_product_clean_report.json"
REPORT_MD = ROOT / "docs/ops/audit/usage_product_clean_report.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def main() -> int:
    errors: list[str] = []
    usage_api = _read(USAGE_API)
    telemetry_api = _read(TELEMETRY_API)
    usage_handler = _read(USAGE_HANDLER)
    telemetry_handler = _read(TELEMETRY_HANDLER)

    if not usage_api:
        errors.append(f"missing file: {USAGE_API.relative_to(ROOT).as_posix()}")
    if not telemetry_api:
        errors.append(f"missing file: {TELEMETRY_API.relative_to(ROOT).as_posix()}")
    if not usage_handler:
        errors.append(f"missing file: {USAGE_HANDLER.relative_to(ROOT).as_posix()}")
    if not telemetry_handler:
        errors.append(f"missing file: {TELEMETRY_HANDLER.relative_to(ROOT).as_posix()}")

    usage_required_tokens = [
        "const PRODUCT_USAGE_EVENT_TYPES = new Set<string>(['scene_open', 'capability_open']);",
        "if (eventType.startsWith('workspace.')) {",
        "await trackTelemetryEvent(eventType, extra);",
        "if (!PRODUCT_USAGE_EVENT_TYPES.has(eventType)) {",
        "intent: 'usage.track'",
    ]
    for token in usage_required_tokens:
        if usage_api and token not in usage_api:
            errors.append(f"usage.ts missing token: {token}")

    telemetry_required_tokens = [
        "intent: 'telemetry.track'",
    ]
    for token in telemetry_required_tokens:
        if telemetry_api and token not in telemetry_api:
            errors.append(f"telemetry.ts missing token: {token}")

    handler_required_tokens = [
        "event_type == \"scene_open\"",
        "event_type == \"capability_open\"",
        "invalid usage params",
    ]
    for token in handler_required_tokens:
        if usage_handler and token not in usage_handler:
            errors.append(f"usage_track.py missing token: {token}")

    forbidden_usage_handler_tokens = [
        "workspace.",
        "telemetry.track",
    ]
    for token in forbidden_usage_handler_tokens:
        if usage_handler and token in usage_handler:
            errors.append(f"usage_track.py contains forbidden token: {token}")

    telemetry_handler_tokens = [
        "INTENT_TYPE = \"telemetry.track\"",
        "invalid telemetry params",
    ]
    for token in telemetry_handler_tokens:
        if telemetry_handler and token not in telemetry_handler:
            errors.append(f"telemetry_track.py missing token: {token}")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "error_count": len(errors),
            "usage_product_event_types": ["scene_open", "capability_open"],
            "workspace_routed_to_telemetry": usage_api.find("trackTelemetryEvent") >= 0,
        },
        "errors": errors,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Usage Product Clean Report",
        "",
        f"- ok: `{report['ok']}`",
        f"- error_count: `{report['summary']['error_count']}`",
        f"- usage_product_event_types: `{', '.join(report['summary']['usage_product_event_types'])}`",
        f"- workspace_routed_to_telemetry: `{report['summary']['workspace_routed_to_telemetry']}`",
    ]
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {err}" for err in errors])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[usage_product_clean_guard] FAIL")
        for err in errors:
            print(err)
        return 1
    print("[usage_product_clean_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
