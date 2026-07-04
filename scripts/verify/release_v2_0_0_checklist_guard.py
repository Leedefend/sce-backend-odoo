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
    (
        "For `sc_demo` acceptance:",
        (
            "ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo \\",
            "ACCEPTANCE_BACKUP_DIR=<uploaded_backup_dir> \\",
            "ACCEPTANCE_BASE_URL=http://127.0.0.1:18081 \\",
            "make release.dev.acceptance.publish",
        ),
    ),
)

REQUIRED_SECTION_LISTS = (
    (
        "## Preconditions",
        (
            "Working tree is clean at release cut time.",
            "Release commit is merged to `main`.",
            "`main` is fast-forwarded and reviewed.",
            "Release notes reviewed: `docs/ops/release_notes_v2.0.0.md`.",
            "Evidence manifest reviewed: `docs/ops/releases/v2.0.0/evidence_manifest.md`.",
            "Versioning reviewed: `docs/ops/versioning.md`.",
            "Release indexes reviewed: `docs/ops/releases/README.md` and",
            "Verify catalog reviewed: `docs/ops/verify/README.md`.",
            "No production command is executed from a dirty worktree.",
        ),
    ),
    (
        "## Version And Tag Checks",
        (
            "Gate tag planned: `gate-release-v2.0`.",
            "RC tag planned: `v2.0.0-rc1`.",
            "Formal tag planned: `v2.0.0`.",
            "Tags are created only after the corresponding gate evidence is attached.",
            "A tag name must never be reused.",
            "GitHub Release is required for `gate-release-v2.0` and `v2.0.0`.",
        ),
    ),
    (
        "The preflight target expands to:",
        (
            "`make verify.system.capability_baseline.report`",
            "`make verify.backend.contract.closure.mainline`",
            "`make verify.restricted`",
        ),
    ),
    (
        "## Contract And Startup Gate",
        (
            "`login -> system.init -> ui.contract` must remain unchanged.",
            "`role_surface.role_code` remains the role source of truth.",
            "`default_route` must come from the backend contract.",
            "Public intents must not be renamed.",
            "Intent canonical/alias snapshot must pass.",
            "Contract closure mainline must pass.",
        ),
    ),
    (
        "## Product Hardening Gate",
        (
            "`make verify.release.v2_0_0.product_hardening` must pass before formal tag.",
            "If `verify.bundle.installation.ready` fails, update or repair the bundle",
            "If `verify.platform.performance.smoke` fails on `system.init` payload size,",
            "Product hardening failures must not be hidden by the governance preflight.",
        ),
    ),
    (
        "Required evidence:",
        (
            "`artifacts/backend/dev_acceptance_release_probe.json`",
            "uploaded package checksum validation",
            "served frontend bundle DB/env verification",
            "`/api/v1/intent?db=sc_demo` OPTIONS/GET behavior",
            "optional real-user login and `system.init` result when credentials are provided",
        ),
    ),
    (
        "## Prod-Sim Gate",
        (
            "`sc_prod_sim` upgrade or replay path is executed only through Makefile targets.",
            "Prod-sim acceptance evidence is validated with",
            "Recorded sample artifact directories may validate schema shape only; they are",
            "Frontend static assets are rebuilt for the intended target DB/env.",
            "Real-user acceptance uses named business users, not only service smoke users.",
            "Prod-sim evidence is kept separate from production evidence.",
        ),
    ),
    (
        "## Production Safety",
        (
            "Follow `docs/ops/production_deployment_runbook_v1.md`.",
            "Follow `docs/ops/prod_command_policy.md`.",
            "`ENV=prod` and `.env.prod` are not allowed in Codex autonomous development.",
            "Production database is `sc_prod`.",
            "Production destructive reset is forbidden.",
            "Any production module upgrade requires `PROD_DANGER=1` and an allowed Makefile target.",
        ),
    ),
    (
        "## Post-Release",
        (
            "Confirm `git rev-parse v2.0.0` equals the intended `main` commit.",
            "Publish GitHub Release for `v2.0.0`.",
            "Attach or link evidence from `docs/ops/releases/v2.0.0/evidence_manifest.md`.",
            "Record deployment acceptance separately if production deployment follows.",
        ),
    ),
    (
        "## Stop Conditions",
        (
            "Any required gate fails.",
            "Snapshot drift is not explained.",
            "Public intent rename or semantic drift is detected.",
            "Prod and prod-sim evidence are mixed.",
            "The release commit is not clean or not on `main`.",
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


def _top_level_bullets_after_heading(text: str, heading: str) -> tuple[str, ...] | None:
    lines = text.splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        return None
    items: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        if line.startswith("- "):
            items.append(line[2:].strip())
    return tuple(items)


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


def _contains_required_section_lists(text: str, errors: list[str]) -> None:
    for heading, expected_items in REQUIRED_SECTION_LISTS:
        actual_items = _top_level_bullets_after_heading(text, heading)
        if actual_items is None:
            errors.append(f"checklist missing section list: {heading}")
            continue
        if actual_items != expected_items:
            errors.append(
                "checklist section list mismatch: "
                f"{heading} expected={expected_items!r} actual={actual_items!r}"
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
        _contains_required_section_lists(text, errors)

    if errors:
        print("[release_v2_0_0_checklist_guard] FAIL")
        for error in errors:
            print(error)
        return 2
    print("[release_v2_0_0_checklist_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
