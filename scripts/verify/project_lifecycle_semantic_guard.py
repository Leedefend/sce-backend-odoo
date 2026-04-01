#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "tmp" / "project_lifecycle_semantic_guard_report.json"
OUT_MD = ROOT / "tmp" / "project_lifecycle_semantic_guard_report.md"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _contains_all(content: str, tokens: list[str]) -> bool:
    return all(token in content for token in tokens)


def main() -> None:
    checks: list[tuple[str, bool, str]] = []

    handler_targets = {
        "project_dashboard_enter.py": [
            "_fallback_lifecycle_hints",
            "\"PROJECT_NOT_FOUND\"",
            "\"lifecycle_hints\"",
        ],
        "project_execution_enter.py": [
            "_fallback_lifecycle_hints",
            "\"PROJECT_NOT_FOUND\"",
            "\"lifecycle_hints\"",
        ],
        "project_plan_bootstrap_enter.py": [
            "_missing_project_lifecycle_hints",
            "\"PROJECT_CONTEXT_MISSING\"",
            "\"lifecycle_hints\"",
        ],
        "project_initiation_enter.py": [
            "_build_lifecycle_hints",
            "\"MISSING_PARAMS\"",
            "\"PERMISSION_DENIED\"",
            "\"BUSINESS_RULE_FAILED\"",
            "\"lifecycle_hints\"",
        ],
        "project_execution_advance.py": [
            "_build_lifecycle_hints",
            "\"PROJECT_CONTEXT_MISSING\"",
            "\"PROJECT_NOT_FOUND\"",
            "\"result\": \"blocked\"",
            "\"lifecycle_hints\"",
        ],
        "project_connection_transition.py": [
            "_build_lifecycle_hints",
            "\"INVALID_TRANSITION_INPUT\"",
            "\"PROJECT_NOT_FOUND\"",
            "\"lifecycle_hints\"",
        ],
        "project_dashboard_block_fetch.py": [
            "_build_lifecycle_hints",
            "\"MISSING_PARAMS\"",
            "\"lifecycle_hints\"",
        ],
        "project_execution_block_fetch.py": [
            "_build_lifecycle_hints",
            "\"MISSING_PARAMS\"",
            "\"lifecycle_hints\"",
        ],
        "project_plan_bootstrap_block_fetch.py": [
            "_build_lifecycle_hints",
            "\"MISSING_PARAMS\"",
            "\"lifecycle_hints\"",
        ],
    }

    service_targets = {
        "project_entry_context_service.py": [
            "_build_lifecycle_guidance",
            "_build_options_guidance",
            "_build_diagnostics_summary",
            "\"suggested_action\"",
            "\"lifecycle_hints\"",
            "\"diagnostics_summary\"",
        ],
        "project_creation_service.py": [
            "post_create_bootstrap",
            "\"ready_for_management\"",
            "\"summary_message\"",
        ],
    }

    creation_handler_targets = {
        "project_initiation_enter.py": [
            "\"bootstrap_summary\"",
            "post_create_bootstrap",
        ],
    }

    handler_base = ROOT / "addons" / "smart_construction_core" / "handlers"
    for rel, tokens in handler_targets.items():
        path = handler_base / rel
        content = _read(path)
        checks.append((f"exists::{rel}", path.exists(), str(path)))
        checks.append((f"semantic_tokens::{rel}", _contains_all(content, tokens), ",".join(tokens)))

    service_base = ROOT / "addons" / "smart_construction_core" / "services"
    for rel, tokens in service_targets.items():
        path = service_base / rel
        content = _read(path)
        checks.append((f"exists::{rel}", path.exists(), str(path)))
        checks.append((f"semantic_tokens::{rel}", _contains_all(content, tokens), ",".join(tokens)))

    for rel, tokens in creation_handler_targets.items():
        path = handler_base / rel
        content = _read(path)
        checks.append((f"exists::{rel}", path.exists(), str(path)))
        checks.append((f"semantic_tokens::{rel}", _contains_all(content, tokens), ",".join(tokens)))

    passed = [item for item in checks if item[1]]
    failed = [item for item in checks if not item[1]]
    status = "pass" if not failed else "fail"
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "summary": {"total": len(checks), "passed": len(passed), "failed": len(failed)},
        "checks": [{"name": n, "ok": ok, "detail": d} for n, ok, d in checks],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# project lifecycle semantic guard report",
        "",
        f"- generated_at_utc: {report['generated_at_utc']}",
        f"- status: **{status.upper()}**",
        f"- checks: {len(passed)}/{len(checks)} passed",
        "",
        "## Check Results",
    ]
    for item in report["checks"]:
        mark = "PASS" if item["ok"] else "FAIL"
        lines.append(f"- [{mark}] {item['name']} ({item['detail']})")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if failed:
        print(f"[verify.project.lifecycle.semantic] FAIL ({len(failed)} checks)")
        raise SystemExit(1)

    print("[verify.project.lifecycle.semantic] PASS")
    print(f"[verify.project.lifecycle.semantic] report: {OUT_JSON}")


if __name__ == "__main__":
    main()
