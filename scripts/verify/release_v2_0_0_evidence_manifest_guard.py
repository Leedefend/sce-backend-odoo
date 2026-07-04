#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "ops" / "releases" / "v2.0.0" / "evidence_manifest.md"

REQUIRED_TOKENS = (
    "# v2.0.0 Evidence Manifest",
    "## Required Before `gate-release-v2.0`",
    "## Required Before `v2.0.0-rc1`",
    "## Required Product Hardening Before Formal `v2.0.0`",
    "## Required Before Formal `v2.0.0`",
    "## Evidence Rules",
    "## Current Local Verification Status",
    "`make verify.system.capability_baseline.report.schema.guard`",
    "`make verify.platform.release_policy.runtime.schema.guard`",
    "`make verify.product.delivery.mainline.summary.schema.guard`",
    "`make verify.product.delivery.action_closure.schema.guard`",
    "`make verify.product.delivery.module_capability.schema.guard`",
    "`make verify.intent.canonical_alias.snapshot.schema.guard`",
    "`make verify.bundle.installation.ready.schema.guard`",
    "`make verify.platform.performance.smoke.schema.guard`",
    "`make verify.dev.acceptance.release.schema.guard`",
    "`PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.prod.sim.acceptance.evidence.schema.guard`",
    "`make verify.release.v2_0_0.checklist.guard`",
    "`make verify.release.v2_0_0.evidence_manifest.guard`",
    "`make verify.release.v2_0_0.control_docs.guard`",
    "`docs/ops/versioning.md`",
    "`docs/ops/releases/README.md`",
    "`docs/ops/releases/README.zh.md`",
    "`docs/ops/verify/README.md`",
    "`make verify.release.v2_0_0.governance.guard`",
    "`PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard`",
    "Evidence from `sc_prod_sim` must not be presented as `sc_prod` evidence.",
    "Production deployment evidence is recorded separately after supervised",
    "Failed evidence is not overwritten without preserving the failure reason",
    "prod-sim acceptance artifact path to be recorded",
    "Schema-only guard runs may use recorded artifact directories to verify evidence",
    "recorded sample artifacts are not release signoff evidence",
    "before creating final `v2.0.0`, rerun",
    "against the recorded prod-sim acceptance run directory for that release",
)

FORBIDDEN_TOKENS = (
    "v1.0.0` |",
    "artifacts/migration/prod_sim_fresh_replay_20260506T000602",
    "artifacts/migration/prod_sim_fresh_replay_20260505T230223",
    "sc_prod evidence",
)

REQUIRED_TABLE_EVIDENCE = {
    "## Required Before `gate-release-v2.0`": (
        "System capability baseline",
        "System capability baseline schema",
        "Platform release policy runtime",
        "Platform release policy runtime schema",
        "Backend contract closure",
        "Backend contract closure snapshot schema",
        "Restricted product mainline",
        "Restricted product mainline schema",
        "Diff hygiene",
    ),
    "## Required Before `v2.0.0-rc1`": (
        "Release preflight",
        "Action closure smoke",
        "Action closure schema",
        "Module capability smoke",
        "Module capability schema",
        "Intent alias snapshot",
        "Intent alias snapshot schema",
    ),
    "## Required Product Hardening Before Formal `v2.0.0`": (
        "Product release readiness",
        "Bundle installation schema",
        "View richness hardening",
        "Platform performance smoke",
        "Platform performance schema",
    ),
    "## Required Before Formal `v2.0.0`": (
        "Dev acceptance publish",
        "Dev acceptance schema",
        "Prod-sim acceptance",
        "Prod-sim acceptance schema",
        "Release checklist signoff",
        "Release checklist guard",
        "Evidence manifest guard",
        "Release control docs guard",
        "Release governance guard",
        "Formal evidence schema guard",
    ),
}

REQUIRED_LOCAL_STATUS_ITEMS = (
    "Command: `make verify.release.v2_0_0.product_hardening`",
    "Status: blocked in the current local `sc_demo` dev verification environment",
    "Current blocker evidence:",
    "Evidence shape guard:",
    "Current blocker facts on `sc_demo`:",
    "Latest passing sub-gate in this batch:",
    "Closed sub-gates: `verify.bundle.installation.ready` and",
    "Release hardening also includes",
    "Artifacts:",
    "Evidence shape guards:",
    "Schema-only guard runs may use recorded artifact directories to verify evidence",
    "Note: before creating `gate-release-v2.0` or `v2.0.0-rc1`, rerun required",
    "Note: before creating final `v2.0.0`, rerun",
)


def _table_evidence_for_section(text: str, heading: str) -> tuple[str, ...] | None:
    lines = text.splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        return None

    table_rows: list[str] = []
    in_table = False
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        if line.startswith("|"):
            in_table = True
            table_rows.append(line)
        elif in_table and line.strip():
            break

    evidence: list[str] = []
    for row in table_rows:
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if not cells or cells[0] in {"Evidence", "---"}:
            continue
        evidence.append(cells[0])
    return tuple(evidence)


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


def _contains_required_table_evidence(text: str, errors: list[str]) -> None:
    for heading, expected_evidence in REQUIRED_TABLE_EVIDENCE.items():
        actual_evidence = _table_evidence_for_section(text, heading)
        if actual_evidence is None:
            errors.append(f"manifest missing section table: {heading}")
            continue
        if actual_evidence != expected_evidence:
            errors.append(
                "manifest evidence table mismatch: "
                f"{heading} expected={expected_evidence!r} actual={actual_evidence!r}"
            )


def _contains_required_local_status_items(text: str, errors: list[str]) -> None:
    actual_items = _top_level_bullets_after_heading(text, "## Current Local Verification Status")
    if actual_items is None:
        errors.append("manifest missing section: ## Current Local Verification Status")
        return
    if actual_items != REQUIRED_LOCAL_STATUS_ITEMS:
        errors.append(
            "manifest local verification status items mismatch: "
            f"expected={REQUIRED_LOCAL_STATUS_ITEMS!r} actual={actual_items!r}"
        )


def main() -> int:
    errors: list[str] = []
    if not MANIFEST.is_file():
        errors.append(f"missing manifest: {MANIFEST.relative_to(ROOT).as_posix()}")
    else:
        text = MANIFEST.read_text(encoding="utf-8")
        for token in REQUIRED_TOKENS:
            if token not in text:
                errors.append(f"manifest missing token: {token}")
        for token in FORBIDDEN_TOKENS:
            if token in text:
                errors.append(f"manifest contains forbidden token: {token}")
        if text.count("| Evidence | Command | Required Result | Artifact |") != 4:
            errors.append("manifest must contain four evidence tables")
        _contains_required_table_evidence(text, errors)
        _contains_required_local_status_items(text, errors)

    if errors:
        print("[release_v2_0_0_evidence_manifest_guard] FAIL")
        for error in errors:
            print(error)
        return 2
    print("[release_v2_0_0_evidence_manifest_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
