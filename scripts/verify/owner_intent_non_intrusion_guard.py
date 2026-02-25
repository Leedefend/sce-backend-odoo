#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OWNER_HANDLER = ROOT / "addons" / "smart_owner_core" / "handlers" / "owner_payment_request.py"
CORE_EXTENSION = ROOT / "addons" / "smart_owner_core" / "core_extension.py"
BASE_HANDLER = ROOT / "addons" / "smart_core" / "core" / "base_handler.py"
API_DATA_WRITE = ROOT / "addons" / "smart_core" / "handlers" / "api_data_write.py"
API_DATA_UNLINK = ROOT / "addons" / "smart_core" / "handlers" / "api_data_unlink.py"
API_DATA_BATCH = ROOT / "addons" / "smart_core" / "handlers" / "api_data_batch.py"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "owner_intent_non_intrusion_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "owner_intent_non_intrusion_report.json"

REQUIRED_OWNER_INTENTS = {"owner.payment.request.submit", "owner.payment.request.approve"}


def _collect_intents_from_file(path: Path) -> set[str]:
    out: set[str] = set()
    if not path.is_file():
        return out
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except Exception:
        return out
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name) or target.id != "INTENT_TYPE":
                continue
            value = node.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                text = value.value.strip()
                if text:
                    out.add(text)
    return out


def _contains_token(path: Path, token: str) -> bool:
    if not path.is_file():
        return False
    return token in path.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    owner_intents = _collect_intents_from_file(OWNER_HANDLER)
    missing = sorted(REQUIRED_OWNER_INTENTS - owner_intents)
    if missing:
        errors.append(f"owner handler missing intents: {', '.join(missing)}")

    extension_text = CORE_EXTENSION.read_text(encoding="utf-8") if CORE_EXTENSION.is_file() else ""
    for intent in sorted(REQUIRED_OWNER_INTENTS):
        if intent not in extension_text:
            errors.append(f"owner core_extension not registering intent: {intent}")

    forbidden_files = [
        BASE_HANDLER,
        API_DATA_WRITE,
        API_DATA_UNLINK,
        API_DATA_BATCH,
    ]
    for file_path in forbidden_files:
        for intent in REQUIRED_OWNER_INTENTS:
            if _contains_token(file_path, intent):
                errors.append(
                    f"forbidden intrusion: {file_path.relative_to(ROOT).as_posix()} contains {intent}"
                )

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "owner_intent_count": len(owner_intents),
            "required_owner_intent_count": len(REQUIRED_OWNER_INTENTS),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "owner_intents": sorted(owner_intents),
        "required_owner_intents": sorted(REQUIRED_OWNER_INTENTS),
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Owner Intent Non-Intrusion Report",
        "",
        f"- owner_intent_count: {payload['summary']['owner_intent_count']}",
        f"- required_owner_intent_count: {payload['summary']['required_owner_intent_count']}",
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
        print("[owner_intent_non_intrusion_guard] FAIL")
        return 2
    print("[owner_intent_non_intrusion_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
