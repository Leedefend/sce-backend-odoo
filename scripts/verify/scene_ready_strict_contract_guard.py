#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "addons/smart_core/core/scene_ready_contract_builder.py"
RUNTIME_CHAIN_TEST = ROOT / "addons/smart_core/tests/test_scene_runtime_contract_chain.py"
REPORT_JSON = ROOT / "artifacts/backend/scene_ready_strict_contract_guard_report.json"
REPORT_MD = ROOT / "docs/ops/audits/scene_ready_strict_contract_guard_report.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _check_tokens(text: str, tokens: list[str]) -> list[str]:
    return [token for token in tokens if token not in text]


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    builder_text = _read(BUILDER)
    test_text = _read(RUNTIME_CHAIN_TEST)
    errors: list[str] = []

    if not builder_text:
        errors.append(f"missing file: {BUILDER.relative_to(ROOT).as_posix()}")
    if not test_text:
        errors.append(f"missing file: {RUNTIME_CHAIN_TEST.relative_to(ROOT).as_posix()}")

    required_builder_tokens = [
        "def _strict_contract_missing_paths",
        'compiled["contract_guard"] = contract_guard',
        'meta_payload["contract_guard"] = contract_guard',
        '"missing": missing_before',
        '"defaults_applied": defaults_applied',
        '"contract_ready": len(missing_before) == 0',
        'meta_payload["runtime_policy"] = meta_runtime_policy',
    ]
    required_test_tokens = [
        "def test_pilot_core_scenes_materialize_strict_contract_fields",
        "def test_scene_ready_respects_declared_runtime_policy_and_tier",
        "def test_strict_scene_emits_contract_guard_for_missing_semantic_contract",
        "def test_non_pilot_scene_without_declared_policy_stays_non_strict",
    ]

    missing_builder = _check_tokens(builder_text, required_builder_tokens)
    missing_tests = _check_tokens(test_text, required_test_tokens)

    if missing_builder:
        errors.extend([f"builder token missing: {token}" for token in missing_builder])
    if missing_tests:
        errors.extend([f"test token missing: {token}" for token in missing_tests])

    report = {
        "guard": "scene_ready_strict_contract_guard",
        "ok": not errors,
        "builder": BUILDER.relative_to(ROOT).as_posix(),
        "runtime_chain_test": RUNTIME_CHAIN_TEST.relative_to(ROOT).as_posix(),
        "required_builder_tokens": required_builder_tokens,
        "required_test_tokens": required_test_tokens,
        "missing_builder_tokens": missing_builder,
        "missing_test_tokens": missing_tests,
        "errors": errors,
    }
    _write(REPORT_JSON, json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    lines = [
        "# Scene Ready Strict Contract Guard Report",
        "",
        f"- status: {'PASS' if not errors else 'FAIL'}",
        f"- builder: `{report['builder']}`",
        f"- runtime_chain_test: `{report['runtime_chain_test']}`",
        f"- missing_builder_tokens: {len(missing_builder)}",
        f"- missing_test_tokens: {len(missing_tests)}",
    ]
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {item}" for item in errors])
    _write(REPORT_MD, "\n".join(lines) + "\n")

    if errors:
        print("[FAIL] scene_ready_strict_contract_guard")
        for item in errors:
            print(f" - {item}")
        print(f"report: {REPORT_JSON.relative_to(ROOT).as_posix()}")
        return 2

    print("[PASS] scene_ready_strict_contract_guard")
    print(f"report: {REPORT_JSON.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

