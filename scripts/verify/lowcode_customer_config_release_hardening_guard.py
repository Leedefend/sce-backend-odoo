#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = ROOT / "Makefile"
CHECKLIST = ROOT / "docs" / "ops" / "release_checklist_v2.0.0.md"
EVIDENCE_MANIFEST = ROOT / "docs" / "ops" / "releases" / "v2.0.0" / "evidence_manifest.md"
CUSTOMER_MANIFEST = ROOT / "addons" / "smart_construction_custom" / "data" / "lowcode_customer_config_baseline_manifest_v1.json"

PIPELINE_TARGET = "verify.lowcode_config.customer_module_asset.pipeline"
RELEASE_HARDENING_GUARD_TARGET = "verify.lowcode_config.customer_module_asset.release_hardening.guard"
RELEASE_READY_TARGET = "verify.product.release.ready"

REQUIRED_PIPELINE_DEPS = {
    "verify.lowcode_config.customer_module_asset.acceptance_apply.dry_run",
    "verify.lowcode_config.customer_module_asset.replay.guard",
}
REQUIRED_MANIFEST_TARGETS = {
    "make verify.lowcode_config.customer_baseline.candidate",
    "make verify.lowcode_config.customer_module_asset.draft",
    "make verify.lowcode_config.customer_module_asset.acceptance_template",
    "make verify.lowcode_config.customer_module_asset.acceptance_apply.dry_run",
    "make verify.lowcode_config.customer_module_asset.pipeline",
    "make verify.lowcode_config.customer_module_asset.release_hardening.guard",
    "make verify.lowcode_config.customer_module_asset.replay.guard",
}
REQUIRED_MANIFEST_KEYS = {
    "module_asset_draft_make_target": "make verify.lowcode_config.customer_module_asset.draft",
    "acceptance_decision_template_make_target": "make verify.lowcode_config.customer_module_asset.acceptance_template",
    "acceptance_apply_dry_run_make_target": "make verify.lowcode_config.customer_module_asset.acceptance_apply.dry_run",
    "accepted_module_asset_replay_guard": "make verify.lowcode_config.customer_module_asset.replay.guard",
    "customer_module_asset_pipeline_make_target": "make verify.lowcode_config.customer_module_asset.pipeline",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _target_deps(makefile_text: str, target: str) -> set[str]:
    lines = makefile_text.splitlines()
    prefix = f"{target}:"
    for index, line in enumerate(lines):
        if not line.startswith(prefix):
            continue
        collected = [line[len(prefix):].rstrip()]
        cursor = index
        while collected[-1].endswith("\\") and cursor + 1 < len(lines):
            cursor += 1
            collected[-1] = collected[-1][:-1]
            collected.append(lines[cursor].strip().rstrip())
        return {item for item in " ".join(collected).split() if item}
    return set()


def _check_makefile(errors: list[str]) -> None:
    text = _read(MAKEFILE)
    release_deps = _target_deps(text, RELEASE_READY_TARGET)
    if PIPELINE_TARGET not in release_deps:
        errors.append(f"{RELEASE_READY_TARGET} must depend on {PIPELINE_TARGET}")
    if RELEASE_HARDENING_GUARD_TARGET not in release_deps:
        errors.append(f"{RELEASE_READY_TARGET} must depend on {RELEASE_HARDENING_GUARD_TARGET}")

    pipeline_deps = _target_deps(text, PIPELINE_TARGET)
    missing_pipeline_deps = sorted(REQUIRED_PIPELINE_DEPS - pipeline_deps)
    if missing_pipeline_deps:
        errors.append(f"{PIPELINE_TARGET} missing deps: {', '.join(missing_pipeline_deps)}")


def _check_release_docs(errors: list[str]) -> None:
    checklist = _read(CHECKLIST)
    if f"`{PIPELINE_TARGET}`" not in checklist:
        errors.append("release checklist must list the customer low-code asset pipeline")
    if f"`{RELEASE_HARDENING_GUARD_TARGET}`" not in checklist:
        errors.append("release checklist must list the customer low-code release hardening guard")

    evidence = _read(EVIDENCE_MANIFEST)
    for token in (
        f"via `{PIPELINE_TARGET}`",
        f"`{RELEASE_HARDENING_GUARD_TARGET}`",
        "customer low-code",
        "asset candidate, draft, decision template, dry-run apply, safety tests, and",
        "replay guard",
    ):
        if token not in evidence:
            errors.append(f"evidence manifest missing token: {token}")


def _check_customer_manifest(errors: list[str]) -> None:
    payload = json.loads(CUSTOMER_MANIFEST.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "lowcode_customer_config_baseline_manifest.v1":
        errors.append("customer low-code baseline manifest schema_version mismatch")
    if payload.get("status") != "guarded":
        errors.append("customer low-code baseline manifest must stay guarded")

    assistant = payload.get("extraction_assistant")
    if not isinstance(assistant, dict):
        errors.append("customer low-code baseline manifest extraction_assistant must be an object")
        assistant = {}
    for key, expected in REQUIRED_MANIFEST_KEYS.items():
        if assistant.get(key) != expected:
            errors.append(f"customer low-code baseline manifest {key} must be {expected}")

    required_guards = payload.get("required_guards")
    if not isinstance(required_guards, list):
        errors.append("customer low-code baseline manifest required_guards must be a list")
        required_guards = []
    missing_targets = sorted(REQUIRED_MANIFEST_TARGETS - set(required_guards))
    if missing_targets:
        errors.append(f"customer low-code baseline manifest missing required guards: {', '.join(missing_targets)}")


def main() -> int:
    errors: list[str] = []
    _check_makefile(errors)
    _check_release_docs(errors)
    _check_customer_manifest(errors)
    if errors:
        print("[lowcode_customer_config_release_hardening_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[lowcode_customer_config_release_hardening_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
