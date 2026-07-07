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
    "`make verify.backend.contract.closure.mainline.summary.schema.guard`",
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
    "`make history.attachment.custody.probe.prod`",
    "`make legacy_attachment.custody_marker.backfill.prod`",
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
    "git tag -f",
    "git push --force",
    "git reset --hard",
    "ENV=prod make",
    "TODO",
    "TBD",
    "FIXME",
)

REQUIRED_SECTION_ORDER = (
    "## Required Before `gate-release-v2.0`",
    "## Required Before `v2.0.0-rc1`",
    "## Required Product Hardening Before Formal `v2.0.0`",
    "## Required Before Formal `v2.0.0`",
    "## Evidence Rules",
    "## Current Local Verification Status",
)

REQUIRED_TABLE_ROWS = {
    "## Required Before `gate-release-v2.0`": (
        ("System capability baseline", "`make verify.system.capability_baseline.report`", "PASS", "`artifacts/backend/system_capability_baseline_report.json`"),
        ("System capability baseline schema", "`make verify.system.capability_baseline.report.schema.guard`", "PASS", "`artifacts/backend/system_capability_baseline_report.json`"),
        ("Platform release policy runtime", "`make verify.platform.release_policy.runtime`", "PASS", "`artifacts/backend/platform_release_policy_runtime_probe.json`"),
        ("Platform release policy runtime schema", "`make verify.platform.release_policy.runtime.schema.guard`", "PASS", "`artifacts/backend/platform_release_policy_runtime_probe.json`"),
        ("Backend contract closure", "`make verify.backend.contract.closure.mainline`", "PASS", "`artifacts/backend/backend_contract_closure_mainline_summary.json`"),
        ("Backend contract closure summary schema", "`make verify.backend.contract.closure.mainline.summary.schema.guard`", "PASS", "`artifacts/backend/backend_contract_closure_mainline_summary.json`"),
        ("Backend contract closure snapshot schema", "`make verify.backend.contract.closure.snapshot.schema.guard`", "PASS", "`artifacts/backend/backend_contract_closure_snapshot.json`"),
        ("Restricted product mainline", "`make verify.restricted`", "PASS", "`artifacts/backend/delivery_mainline_run_summary.json`"),
        ("Restricted product mainline schema", "`make verify.product.delivery.mainline.summary.schema.guard`", "PASS", "`artifacts/backend/delivery_mainline_run_summary.json`"),
        ("Diff hygiene", "`git diff --check`", "PASS", "terminal output"),
    ),
    "## Required Before `v2.0.0-rc1`": (
        ("Release preflight", "`make verify.release.v2_0_0.preflight`", "PASS", "aggregate terminal output"),
        ("Action closure smoke", "`make verify.product.delivery.action_closure.smoke`", "PASS", "`artifacts/backend/product_delivery_action_closure_report.json`"),
        ("Action closure schema", "`make verify.product.delivery.action_closure.schema.guard`", "PASS", "`artifacts/backend/product_delivery_action_closure_report.json`"),
        ("Module capability smoke", "`make verify.product.delivery.module_capability.smoke`", "PASS", "`artifacts/backend/product_delivery_module9_smoke_report.json`"),
        ("Module capability schema", "`make verify.product.delivery.module_capability.schema.guard`", "PASS", "`artifacts/backend/product_delivery_module9_smoke_report.json`"),
        ("Intent alias snapshot", "`make verify.intent.canonical_alias.snapshot.guard`", "PASS", "`artifacts/backend/intent_canonical_alias_snapshot.json`"),
        ("Intent alias snapshot schema", "`make verify.intent.canonical_alias.snapshot.schema.guard`", "PASS", "`artifacts/backend/intent_canonical_alias_snapshot.json`"),
    ),
    "## Required Product Hardening Before Formal `v2.0.0`": (
        ("Product release readiness", "`make verify.release.v2_0_0.product_hardening`", "PASS", "`artifacts/backend/bundle_installation_report.json` and related product gate artifacts"),
        ("Bundle installation schema", "`make verify.bundle.installation.ready.schema.guard`", "PASS", "`artifacts/backend/bundle_installation_report.json`"),
        ("View richness hardening", "included in `make verify.release.v2_0_0.product_hardening`", "PASS", "`docs/product/view_richness_post_ga_report_v1.md`"),
        ("Platform performance smoke", "included in `make verify.release.v2_0_0.product_hardening`", "PASS", "`artifacts/backend/platform_performance_smoke.json`"),
        ("Platform performance schema", "`make verify.platform.performance.smoke.schema.guard`", "PASS", "`artifacts/backend/platform_performance_smoke.json`"),
    ),
    "## Required Before Formal `v2.0.0`": (
        ("Dev acceptance publish", "`make release.dev.acceptance.publish` with dev env vars", "PASS", "`artifacts/backend/dev_acceptance_release_probe.json`"),
        ("Dev acceptance schema", "`make verify.dev.acceptance.release.schema.guard`", "PASS", "`artifacts/backend/dev_acceptance_release_probe.json`"),
        ("Prod-sim acceptance", "governed prod-sim Makefile flow", "PASS", "prod-sim acceptance artifact path to be recorded"),
        ("Prod-sim acceptance schema", "`PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.prod.sim.acceptance.evidence.schema.guard`", "PASS", "`scbs_release_acceptance_strict_result_v1.json`, `scbs_release_acceptance_strict_v1.md`, and `scbs_no_legacy_replay_acceptance_result_v1.json` under the recorded run dir"),
        ("Release checklist signoff", "manual review", "PASS", "`docs/ops/release_checklist_v2.0.0.md`"),
        ("Release checklist guard", "`make verify.release.v2_0_0.checklist.guard`", "PASS", "`docs/ops/release_checklist_v2.0.0.md`"),
        ("Evidence manifest guard", "`make verify.release.v2_0_0.evidence_manifest.guard`", "PASS", "`docs/ops/releases/v2.0.0/evidence_manifest.md`"),
        ("Release control docs guard", "`make verify.release.v2_0_0.control_docs.guard`", "PASS", "`docs/ops/releases/v2.0.0/README.md`, `docs/ops/release_notes_v2.0.0.md`, `docs/ops/versioning.md`, `docs/ops/releases/README.md`, `docs/ops/releases/README.zh.md`, and `docs/ops/verify/README.md`"),
        ("Release governance guard", "`make verify.release.v2_0_0.governance.guard`", "PASS", "release-control docs, evidence manifest, and checklist guard terminal output"),
        ("Formal evidence schema guard", "`PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard`", "PASS", "governance, hardening, dev acceptance, and prod-sim acceptance evidence shape guard terminal output"),
    ),
}

REQUIRED_LOCAL_STATUS_ITEMS = (
    "Command: `make verify.release.v2_0_0.product_hardening`",
    "Status: PASS in the current local `sc_demo` dev verification environment",
    "Demo-data release gate:",
    "Demo-data closure facts on `sc_demo`:",
    "Previous blocker preserved:",
    "Latest passing sub-gate in this batch:",
    "Closed hardening target:",
    "Release hardening also includes",
    "Artifacts:",
    "Evidence shape guards:",
    "Schema-only guard runs may use recorded artifact directories to verify evidence",
    "Note: before creating `gate-release-v2.0` or `v2.0.0-rc1`, rerun required",
    "Note: before creating final `v2.0.0`, rerun",
)

REQUIRED_LOCAL_STATUS_NESTED_ITEMS = (
    (
        "Artifacts:",
        (
            "`artifacts/backend/bundle_installation_report.json`",
            "`artifacts/backend/platform_performance_smoke.json`",
            "`artifacts/backend/non_demo_data_contamination_guard.json`",
        ),
    ),
    (
        "Evidence shape guards:",
        (
            "`make verify.product.no_demo_data.schema.guard`",
            "`make verify.bundle.installation.ready.schema.guard`",
            "`make verify.platform.performance.smoke.schema.guard`",
        ),
    ),
)

REQUIRED_EVIDENCE_RULES = (
    "Evidence from `sc_prod_sim` must not be presented as `sc_prod` evidence.",
    "Production deployment evidence is recorded separately after supervised",
    "If production deployment includes migrated or legacy attachments, production",
    "If the attachment custody probe reports a marker gap, snapshot affected",
    "Snapshot changes must include the command that produced them.",
    "Failed evidence is not overwritten without preserving the failure reason in an",
)


def _table_rows_for_section(text: str, heading: str) -> tuple[tuple[str, str, str, str], ...] | None:
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

    rows: list[tuple[str, str, str, str]] = []
    for row in table_rows:
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if not cells or cells[0] in {"Evidence", "---"}:
            continue
        if len(cells) != 4:
            return ()
        rows.append((cells[0], cells[1], cells[2], cells[3]))
    return tuple(rows)


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


def _heading_order(text: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in text.splitlines() if line.startswith("## "))


def _nested_bullets_after_top_level_item(
    text: str,
    heading: str,
    item: str,
) -> tuple[str, ...] | None:
    lines = text.splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        return None

    target = f"- {item}"
    in_target = False
    nested_items: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        if in_target:
            if line.startswith("- "):
                break
            stripped = line.strip()
            if stripped.startswith("- "):
                nested_items.append(stripped[2:].strip())
        elif line == target:
            in_target = True

    if not in_target:
        return None
    return tuple(nested_items)


def _contains_required_table_rows(text: str, errors: list[str]) -> None:
    for heading, expected_rows in REQUIRED_TABLE_ROWS.items():
        actual_rows = _table_rows_for_section(text, heading)
        if actual_rows is None:
            errors.append(f"manifest missing section table: {heading}")
            continue
        if actual_rows != expected_rows:
            errors.append(
                "manifest evidence table rows mismatch: "
                f"{heading} expected={expected_rows!r} actual={actual_rows!r}"
            )


def _contains_required_section_order(text: str, errors: list[str]) -> None:
    actual_order = _heading_order(text)
    if actual_order != REQUIRED_SECTION_ORDER:
        errors.append(
            "manifest section order mismatch: "
            f"expected={REQUIRED_SECTION_ORDER!r} actual={actual_order!r}"
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


def _contains_required_local_status_nested_items(text: str, errors: list[str]) -> None:
    heading = "## Current Local Verification Status"
    for item, expected_items in REQUIRED_LOCAL_STATUS_NESTED_ITEMS:
        actual_items = _nested_bullets_after_top_level_item(text, heading, item)
        if actual_items is None:
            errors.append(f"manifest missing local verification status item: {item}")
            continue
        if actual_items != expected_items:
            errors.append(
                "manifest local verification status nested items mismatch: "
                f"{item} expected={expected_items!r} actual={actual_items!r}"
            )


def _contains_required_evidence_rules(text: str, errors: list[str]) -> None:
    actual_items = _top_level_bullets_after_heading(text, "## Evidence Rules")
    if actual_items is None:
        errors.append("manifest missing section: ## Evidence Rules")
        return
    if actual_items != REQUIRED_EVIDENCE_RULES:
        errors.append(
            "manifest evidence rules mismatch: "
            f"expected={REQUIRED_EVIDENCE_RULES!r} actual={actual_items!r}"
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
        _contains_required_section_order(text, errors)
        _contains_required_table_rows(text, errors)
        _contains_required_evidence_rules(text, errors)
        _contains_required_local_status_items(text, errors)
        _contains_required_local_status_nested_items(text, errors)

    if errors:
        print("[release_v2_0_0_evidence_manifest_guard] FAIL")
        for error in errors:
            print(error)
        return 2
    print("[release_v2_0_0_evidence_manifest_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
