#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CHECKLIST = ROOT / "docs" / "ops" / "release_checklist_v2.0.0.md"

REQUIRED_TOKENS = (
    "# Release Checklist - v2.0.0",
    "## Preconditions",
    "## Version And Tag Checks",
    "## Local / CI Gate",
    "## Product Hardening Gate",
    "## Dev Acceptance Gate",
    "## Prod-Sim Gate",
    "## Production Safety",
    "## Post-Release",
    "## Stop Conditions",
    "make verify.release.v2_0_0.preflight",
    "make verify.release.v2_0_0.product_hardening",
    "make verify.release.v2_0_0.governance.guard",
    "PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard",
    "make verify.release.v2_0_0.control_docs.guard",
    "make verify.release.v2_0_0.evidence_manifest.guard",
    "Versioning reviewed: `docs/ops/versioning.md`.",
    "Release indexes reviewed: `docs/ops/releases/README.md` and",
    "`docs/ops/releases/README.zh.md`.",
    "Verify catalog reviewed: `docs/ops/verify/README.md`.",
    "make release.dev.acceptance.publish",
    "PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.prod.sim.acceptance.evidence.schema.guard",
    "Recorded sample artifact directories may validate schema shape only",
    "not release signoff evidence.",
    "artifacts/backend/dev_acceptance_release_probe.json",
    "gate-release-v2.0",
    "v2.0.0-rc1",
    "v2.0.0",
    "sc_prod_sim",
    "sc_prod",
    "Production destructive reset is forbidden.",
    "Prod and prod-sim evidence are mixed.",
)

FORBIDDEN_TOKENS = (
    "git tag -f",
    "git push --force",
    "git reset --hard",
    "ENV=prod make",
)

REQUIRED_SECTION_ORDER = (
    "## Preconditions",
    "## Version And Tag Checks",
    "## Local / CI Gate",
    "## Contract And Startup Gate",
    "## Product Hardening Gate",
    "## Dev Acceptance Gate",
    "## Prod-Sim Gate",
    "## Production Safety",
    "## Post-Release",
    "## Stop Conditions",
)

REQUIRED_COMMAND_BLOCKS = (
    (
        "Required before RC:",
        (
            "make verify.release.v2_0_0.preflight",
            "git diff --check",
        ),
    ),
    (
        "Required before formal `v2.0.0`:",
        (
            "make verify.release.v2_0_0.product_hardening",
            "make verify.release.v2_0_0.governance.guard",
            "PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard",
            "make verify.release.v2_0_0.control_docs.guard",
            "make verify.release.v2_0_0.evidence_manifest.guard",
        ),
    ),
)


def _heading_order(text: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in text.splitlines() if line.startswith("## "))


def _contains_required_section_order(text: str, errors: list[str]) -> None:
    actual_order = _heading_order(text)
    if actual_order != REQUIRED_SECTION_ORDER:
        errors.append(
            "checklist section order mismatch: "
            f"expected={REQUIRED_SECTION_ORDER!r} actual={actual_order!r}"
        )


def _command_block_after(text: str, marker: str) -> tuple[str, ...] | None:
    marker_index = text.find(marker)
    if marker_index < 0:
        return None
    after_marker = text[marker_index + len(marker) :]
    fence_start = after_marker.find("```bash")
    if fence_start < 0:
        return None
    after_fence = after_marker[fence_start + len("```bash") :]
    fence_end = after_fence.find("```")
    if fence_end < 0:
        return None
    block = after_fence[:fence_end]
    return tuple(line.strip() for line in block.splitlines() if line.strip())


def _contains_required_command_blocks(text: str, errors: list[str]) -> None:
    for marker, expected_commands in REQUIRED_COMMAND_BLOCKS:
        actual_commands = _command_block_after(text, marker)
        if actual_commands is None:
            errors.append(f"checklist missing command block after marker: {marker}")
            continue
        if actual_commands != expected_commands:
            errors.append(
                "checklist command block mismatch: "
                f"{marker} expected={expected_commands!r} actual={actual_commands!r}"
            )


def main() -> int:
    errors: list[str] = []
    if not CHECKLIST.is_file():
        errors.append(f"missing checklist: {CHECKLIST.relative_to(ROOT).as_posix()}")
    else:
        text = CHECKLIST.read_text(encoding="utf-8")
        for token in REQUIRED_TOKENS:
            if token not in text:
                errors.append(f"checklist missing token: {token}")
        for token in FORBIDDEN_TOKENS:
            if token in text:
                errors.append(f"checklist contains forbidden token: {token}")
        _contains_required_section_order(text, errors)
        _contains_required_command_blocks(text, errors)

    if errors:
        print("[release_v2_0_0_checklist_guard] FAIL")
        for error in errors:
            print(error)
        return 2
    print("[release_v2_0_0_checklist_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
