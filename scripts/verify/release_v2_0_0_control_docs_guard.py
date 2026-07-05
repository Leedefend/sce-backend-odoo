#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = ROOT / "Makefile"
CONTROL_README = ROOT / "docs" / "ops" / "releases" / "v2.0.0" / "README.md"
RELEASE_NOTES = ROOT / "docs" / "ops" / "release_notes_v2.0.0.md"
VERSIONING = ROOT / "docs" / "ops" / "versioning.md"
RELEASE_INDEX_EN = ROOT / "docs" / "ops" / "releases" / "README.md"
RELEASE_INDEX_ZH = ROOT / "docs" / "ops" / "releases" / "README.zh.md"
VERIFY_README = ROOT / "docs" / "ops" / "verify" / "README.md"

README_TOKENS = (
    "# v2.0.0 Release Control",
    "- Version: `v2.0.0`",
    "- Planned gate tag: `gate-release-v2.0`",
    "- Planned RC tag: `v2.0.0-rc1`",
    "- Planned final tag: `v2.0.0`",
    "- Module: versioning, release index, release checklist, release notes, release evidence manifest, verify catalog",
    "- Versioning: `docs/ops/versioning.md`",
    "- Release index: `docs/ops/releases/README.md`",
    "- Release index (zh): `docs/ops/releases/README.zh.md`",
    "- Verify catalog: `docs/ops/verify/README.md`",
    "make verify.release.v2_0_0.preflight",
    "make verify.release.v2_0_0.product_hardening",
    "make verify.release.v2_0_0.governance.guard",
    "PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard",
    "Run prod-sim acceptance.",
    "Create `v2.0.0` after formal release signoff.",
    "Recorded sample artifact directories may validate schema shape only",
    "release signoff requires the recorded prod-sim acceptance run directory",
    "remove `verify.release.v2_0_0.preflight` from `Makefile`",
    "remove `verify.release.v2_0_0.product_hardening` from `Makefile`",
    "remove `verify.release.v2_0_0.governance.guard` from `Makefile`",
    "remove `verify.release.v2_0_0.formal_evidence.schema.guard` from `Makefile`",
    "restore `docs/ops/versioning.md` edits",
    "restore `docs/ops/releases/README.md` edits",
    "restore `docs/ops/releases/README.zh.md` edits",
    "restore `docs/ops/verify/README.md` edits",
    "Runtime rollback is outside this governance batch",
)

NOTES_TOKENS = (
    "# Release Notes - v2.0.0",
    "`v2.0.0` is the active formal release line",
    "Product delivery baseline: 10 modules and 22 scoped scenes.",
    "Startup contract: `login -> system.init -> ui.contract`.",
    "Role authority: `role_surface.role_code`.",
    "Route authority: backend-provided `default_route`.",
    "make verify.release.v2_0_0.preflight",
    "make verify.release.v2_0_0.product_hardening",
    "make verify.release.v2_0_0.governance.guard",
    "PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard",
    "ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo",
    "Release governance docs: release-control README, release notes, versioning,",
    "release indexes, evidence manifest, checklist, and verify catalog.",
    "Recorded sample artifact directories may validate evidence schema shape",
    "are not release signoff evidence.",
    "Production deployment is not part of this release-note batch.",
    "RC tags are immutable once published.",
)

VERSIONING_TOKENS = (
    "# Tag & Release Naming Convention v1.0",
    "Never reuse a tag name.",
    "## 8) v2.0.0 Formal Release Line",
    "`v1.0.0` tag name already exists remotely and must not be reused",
    "gate baseline: `gate-release-v2.0`",
    "release candidates: `v2.0.0-rc1`, `v2.0.0-rc2` only when blocker fixes require a new candidate",
    "formal release: `v2.0.0`",
    "make verify.release.v2_0_0.preflight",
    "make verify.release.v2_0_0.product_hardening",
    "PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard",
    "Recorded sample artifact directories may validate schema shape only",
    "release signoff requires the recorded prod-sim acceptance run directory",
    "Production deployment is not implied by creating `v2.0.0`",
)

RELEASE_INDEX_EN_TOKENS = (
    "# Releases Index (Authoritative)",
    "## Planned Formal Release",
    "- v2.0.0 (planned tag: `v2.0.0`)",
    "Notes: `docs/ops/release_notes_v2.0.0.md`",
    "Checklist: `docs/ops/release_checklist_v2.0.0.md`",
    "Evidence: `docs/ops/releases/v2.0.0/evidence_manifest.md`",
    "Verify Catalog: `docs/ops/verify/README.md`",
    "Verify: `make verify.release.v2_0_0.preflight`",
    "Governance Verify: `make verify.release.v2_0_0.governance.guard`",
    "Formal Evidence Verify: `PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard`",
    "Evidence Boundary: recorded sample artifacts are not release signoff evidence",
    "GitHub Release: required after formal tag",
)

RELEASE_INDEX_ZH_TOKENS = (
    "# 版本发布索引",
    "## 计划正式发布",
    "- v2.0.0（计划 tag：`v2.0.0`）",
    "Release Notes：`docs/ops/release_notes_v2.0.0.md`",
    "Release Checklist：`docs/ops/release_checklist_v2.0.0.md`",
    "Evidence：`docs/ops/releases/v2.0.0/evidence_manifest.md`",
    "Verify Catalog：`docs/ops/verify/README.md`",
    "Verify：`make verify.release.v2_0_0.preflight`",
    "Governance Verify：`make verify.release.v2_0_0.governance.guard`",
    "Formal Evidence Verify：`PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard`",
    "Evidence Boundary：历史样本证据不可作为发布签发证据",
    "GitHub Release：正式 tag 后必须发布",
)

VERIFY_README_TOKENS = (
    "`make verify.release.v2_0_0.checklist.guard`",
    "controlled-doc review",
    "sections in the expected order",
    "key safety, evidence, preflight expansion lists, and hardening expansion prose locked by section",
    "Enforces RC, formal-release, and dev-acceptance command blocks exactly.",
    "versioning/release-index review",
    "`make verify.release.v2_0_0.evidence_manifest.guard`",
    "evidence table row content/order",
    "current local verification status and nested artifact/shape-guard structure",
    "controlled-doc artifact coverage",
    "evidence rules structure",
    "`make verify.release.v2_0_0.control_docs.guard`",
    "release indexes, verification catalog, and Makefile target phony declarations, dependencies, and guard recipes",
    "Enforces release-control section order, status, scope, boundary and gate command blocks, release document list, rollback list, release-index planned entries, release-notes section order, intent, scope, tag plan, production boundary, known limits, acceptance command blocks, versioning section order, tag type, no-history-rewrite, tag pre-check, formal release line, and promotion order shape",
    "`PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard`",
    "Recorded sample artifact directories may validate schema shape only",
    "final release signoff requires the recorded prod-sim acceptance run directory",
)

README_STATUS_ITEMS = (
    "Version: `v2.0.0`",
    "Status: planned",
    "Release type: formal release",
    "Planned gate tag: `gate-release-v2.0`",
    "Planned RC tag: `v2.0.0-rc1`",
    "Planned final tag: `v2.0.0`",
    "Governance date: 2026-05-12",
)

README_SECTION_ORDER = (
    "## Status",
    "## Layer Target / Module / Reason",
    "## Release Boundaries",
    "## Required Gates",
    "## Release Documents",
    "## Promotion Order",
    "## Rollback",
)

README_LAYER_TARGET_ITEMS = (
    "Layer Target: Ops / Release Governance",
    "Module: versioning, release index, release checklist, release notes, release evidence manifest, verify catalog",
    "Reason: establish the active formal release line before RC and production",
)

README_RELEASE_DOCUMENTS = (
    "Versioning: `docs/ops/versioning.md`",
    "Release index: `docs/ops/releases/README.md`",
    "Release index (zh): `docs/ops/releases/README.zh.md`",
    "Verify catalog: `docs/ops/verify/README.md`",
    "Release notes: `docs/ops/release_notes_v2.0.0.md`",
    "Release checklist: `docs/ops/release_checklist_v2.0.0.md`",
    "Evidence manifest: `docs/ops/releases/v2.0.0/evidence_manifest.md`",
)

README_BOUNDARY_EXCLUSIONS = (
    "create Git tags",
    "deploy production",
    "reset or replace databases",
    "change public intent semantics",
    "change frontend runtime behavior",
)

README_ROLLBACK_ITEMS = (
    "remove `docs/ops/releases/v2.0.0/`",
    "remove `docs/ops/release_notes_v2.0.0.md`",
    "remove `docs/ops/release_checklist_v2.0.0.md`",
    "remove `verify.release.v2_0_0.preflight` from `Makefile`",
    "remove `verify.release.v2_0_0.product_hardening` from `Makefile`",
    "remove `verify.release.v2_0_0.governance.guard` from `Makefile`",
    "remove `verify.release.v2_0_0.formal_evidence.schema.guard` from `Makefile`",
    "restore `docs/ops/versioning.md` edits",
    "restore `docs/ops/releases/README.md` edits",
    "restore `docs/ops/releases/README.zh.md` edits",
    "restore `docs/ops/verify/README.md` edits",
)

README_REQUIRED_GATES_COMMANDS = (
    "make verify.release.v2_0_0.preflight",
    "git diff --check",
)

README_SUPPORTING_GATES_COMMANDS = (
    "make verify.system.capability_baseline.report",
    "make verify.backend.contract.closure.mainline",
    "make verify.restricted",
)

README_HARDENING_GATE_COMMANDS = (
    "make verify.release.v2_0_0.product_hardening",
)

README_PROMOTION_ORDER = (
    "Finish release governance on a feature branch.",
    "Merge reviewed release governance and code changes to `main`.",
    "Run release preflight on `main`.",
    "Create `gate-release-v2.0` after gate evidence passes.",
    "Close product hardening gate.",
    "Run `make verify.release.v2_0_0.governance.guard`.",
    "Run prod-sim acceptance.",
    "Run `PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard`.",
    "Create `v2.0.0-rc1` after RC evidence passes.",
    "Create `v2.0.0` after formal release signoff.",
)

NOTES_SECTION_ORDER = (
    "## Release Intent",
    "## Scope",
    "## Tag Plan",
    "## Verification",
    "## Known Limits",
)

VERSIONING_SECTION_ORDER = (
    "## 1) Tag Types",
    "## 2) Naming Formats (Regex)",
    "## 3) When to Tag",
    "## 4) GitHub Release Requirements",
    "## 5) Version Progression Rules",
    "## 6) No History Rewrite",
    "## 7) Tag Pre-Check List (Process)",
    "## 8) v2.0.0 Formal Release Line",
)

VERSIONING_FORMAL_RELEASE_ITEMS = (
    "gate baseline: `gate-release-v2.0`",
    "release candidates: `v2.0.0-rc1`, `v2.0.0-rc2` only when blocker fixes require a new candidate",
    "formal release: `v2.0.0`",
)

VERSIONING_TAG_TYPE_ITEMS = (
    "phase: capability milestone for a phase or stage (e.g. P1/P2).",
    "gate: runtime or policy gate baseline (guard rails).",
    "release: production/stable release for general delivery.",
    "infra: infrastructure or environment baseline.",
    "exp: experiment or temporary spike.",
)

VERSIONING_NO_HISTORY_REWRITE_ITEMS = (
    "Historical tags remain untouched.",
    "This document only constrains new tags from this point forward.",
)

VERSIONING_TAG_PRECHECK_ITEMS = (
    "Type: phase / gate / release / infra / exp",
    "Anchored on main",
    "Requires GitHub Release? (gate/release required)",
    "Validation commands PASS",
    "Release index updated (docs/ops/releases/README.md)",
)

VERSIONING_PROMOTION_ORDER = (
    "Merge reviewed release-prep work to `main`.",
    "Run `make verify.release.v2_0_0.preflight` on the reviewed release commit.",
    "Create `gate-release-v2.0` only after gate evidence passes.",
    "Run `make verify.release.v2_0_0.product_hardening` and close any blocker.",
    "Run `PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard` after prod-sim acceptance evidence is recorded.",
    "Create `v2.0.0-rc1` only after RC evidence passes.",
    "Create `v2.0.0` only after prod-sim acceptance and release checklist signoff.",
)

NOTES_MINIMUM_VERIFICATION_COMMANDS = (
    "make verify.release.v2_0_0.preflight",
    "make verify.release.v2_0_0.product_hardening",
    "make verify.release.v2_0_0.governance.guard",
    "PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard",
    "make verify.system.capability_baseline.report",
    "make verify.restricted",
    "make verify.backend.contract.closure.mainline",
)

NOTES_ENV_ACCEPTANCE_COMMANDS = (
    "ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo \\",
    "ACCEPTANCE_BACKUP_DIR=<uploaded_backup_dir> \\",
    "ACCEPTANCE_BASE_URL=http://127.0.0.1:18081 \\",
    "make release.dev.acceptance.publish",
)

NOTES_SCOPE_ITEMS = (
    "Product delivery baseline: 10 modules and 22 scoped scenes.",
    "Startup contract: `login -> system.init -> ui.contract`.",
    "Role authority: `role_surface.role_code`.",
    "Route authority: backend-provided `default_route`.",
    "Frontend acceptance: served static bundle must match the target DB and app env.",
    "Dev acceptance path: uploaded backup validation, static rebuild, API lock, and",
    "Release gate: one-command preflight through `make verify.release.v2_0_0.preflight`.",
    "Release governance docs: release-control README, release notes, versioning,",
)

NOTES_TEXT_SNIPPETS = (
    (
        "`v2.0.0` is the active formal release line for the construction management\n"
        "system. It promotes the current product-delivery posture from iterative\n"
        "acceptance into a governed release candidate flow."
    ),
    (
        "The earlier `v1.0.0` tag name already exists in the remote repository and must\n"
        "not be reused. This line therefore intentionally advances the formal release\n"
        "track to `v2.0.0`."
    ),
    (
        "Tags must be created only after the release checklist is complete and `main`\n"
        "matches the reviewed release commit."
    ),
    (
        "Production deployment is not part of this release-note batch. Production must\n"
        "follow `docs/ops/production_deployment_runbook_v1.md` and\n"
        "`docs/ops/prod_command_policy.md`."
    ),
)

NOTES_TAG_PLAN_ITEMS = (
    "Gate baseline: `gate-release-v2.0`",
    "Release candidates: `v2.0.0-rc1`, then `v2.0.0-rc2` only if blocker fixes are required.",
    "Formal release: `v2.0.0`",
)

NOTES_KNOWN_LIMITS_ITEMS = (
    "`v2.0.0` release governance does not authorize production data replacement.",
    "`make verify.release.v2_0_0.product_hardening` is a formal-release hardening",
    "Strict live checks may require a live-enabled runner; local restricted evidence",
    "Recorded sample artifact directories may validate evidence schema shape, but",
    "RC tags are immutable once published. Any blocker fix requires a new commit and",
)

RELEASE_INDEX_EN_PLANNED_ITEMS = (
    "v2.0.0 (planned tag: `v2.0.0`)",
    "Type: release",
    "Status: planned",
    "Notes: `docs/ops/release_notes_v2.0.0.md`",
    "Checklist: `docs/ops/release_checklist_v2.0.0.md`",
    "Evidence: `docs/ops/releases/v2.0.0/evidence_manifest.md`",
    "Verify Catalog: `docs/ops/verify/README.md`",
    "Verify: `make verify.release.v2_0_0.preflight`",
    "Governance Verify: `make verify.release.v2_0_0.governance.guard`",
    "Formal Evidence Verify: `PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard`",
    "Evidence Boundary: recorded sample artifacts are not release signoff evidence",
    "GitHub Release: required after formal tag",
)

RELEASE_INDEX_ZH_PLANNED_ITEMS = (
    "v2.0.0（计划 tag：`v2.0.0`）",
    "类型：release",
    "状态：planned",
    "Release Notes：`docs/ops/release_notes_v2.0.0.md`",
    "Release Checklist：`docs/ops/release_checklist_v2.0.0.md`",
    "Evidence：`docs/ops/releases/v2.0.0/evidence_manifest.md`",
    "Verify Catalog：`docs/ops/verify/README.md`",
    "Verify：`make verify.release.v2_0_0.preflight`",
    "Governance Verify：`make verify.release.v2_0_0.governance.guard`",
    "Formal Evidence Verify：`PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard`",
    "Evidence Boundary：历史样本证据不可作为发布签发证据",
    "GitHub Release：正式 tag 后必须发布",
)

MAKEFILE_PHONY_TARGETS = (
    "verify.release.v2_0_0.preflight",
    "verify.release.v2_0_0.product_hardening",
    "verify.release.v2_0_0.checklist.guard",
    "verify.release.v2_0_0.evidence_manifest.guard",
    "verify.release.v2_0_0.control_docs.guard",
    "verify.release.v2_0_0.governance.guard",
    "verify.release.v2_0_0.formal_evidence.schema.guard",
)

MAKEFILE_TARGET_PREREQS = (
    (
        "verify.release.v2_0_0.preflight",
        (
            "guard.prod.forbid",
            "verify.system.capability_baseline.report",
            "verify.platform.release_policy.runtime",
            "verify.backend.contract.closure.mainline",
            "verify.restricted",
        ),
    ),
    (
        "verify.release.v2_0_0.product_hardening",
        (
            "guard.prod.forbid",
            "verify.product.release.ready",
        ),
    ),
    (
        "verify.release.v2_0_0.governance.guard",
        (
            "guard.prod.forbid",
            "verify.release.v2_0_0.control_docs.guard",
            "verify.release.v2_0_0.evidence_manifest.guard",
            "verify.release.v2_0_0.checklist.guard",
        ),
    ),
    (
        "verify.release.v2_0_0.formal_evidence.schema.guard",
        (
            "guard.prod.forbid",
            "verify.release.v2_0_0.governance.guard",
            "verify.bundle.installation.ready.schema.guard",
            "verify.platform.performance.smoke.schema.guard",
            "verify.dev.acceptance.release.schema.guard",
            "verify.prod.sim.acceptance.evidence.schema.guard",
        ),
    ),
)

MAKEFILE_TARGET_RECIPES = (
    (
        "verify.release.v2_0_0.preflight",
        (
            '@echo "[OK] verify.release.v2_0_0.preflight done"',
        ),
    ),
    (
        "verify.release.v2_0_0.product_hardening",
        (
            '@echo "[OK] verify.release.v2_0_0.product_hardening done"',
        ),
    ),
    (
        "verify.release.v2_0_0.checklist.guard",
        (
            "@python3 -m py_compile scripts/verify/release_v2_0_0_checklist_guard.py",
            "@python3 scripts/verify/release_v2_0_0_checklist_guard.py",
        ),
    ),
    (
        "verify.release.v2_0_0.evidence_manifest.guard",
        (
            "@python3 -m py_compile scripts/verify/release_v2_0_0_evidence_manifest_guard.py",
            "@python3 scripts/verify/release_v2_0_0_evidence_manifest_guard.py",
        ),
    ),
    (
        "verify.release.v2_0_0.control_docs.guard",
        (
            "@python3 -m py_compile scripts/verify/release_v2_0_0_control_docs_guard.py",
            "@python3 scripts/verify/release_v2_0_0_control_docs_guard.py",
        ),
    ),
    (
        "verify.release.v2_0_0.governance.guard",
        (
            '@echo "[OK] verify.release.v2_0_0.governance.guard done"',
        ),
    ),
    (
        "verify.release.v2_0_0.formal_evidence.schema.guard",
        (
            '@echo "[OK] verify.release.v2_0_0.formal_evidence.schema.guard done"',
        ),
    ),
)

FORBIDDEN_TOKENS = (
    "Product delivery baseline: 9 modules",
    "reuse `v1.0.0`",
    "git tag -f",
    "git push --force",
    "git reset --hard",
    "ENV=prod make",
    "TODO",
    "TBD",
    "FIXME",
    "Production deployment is part of this release-note batch.",
)


def _contains_all(path: Path, tokens: tuple[str, ...], errors: list[str]) -> None:
    if not path.is_file():
        errors.append(f"missing doc: {path.relative_to(ROOT).as_posix()}")
        return
    text = path.read_text(encoding="utf-8")
    for token in tokens:
        if token not in text:
            errors.append(f"{path.relative_to(ROOT).as_posix()} missing token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in text:
            errors.append(f"{path.relative_to(ROOT).as_posix()} contains forbidden token: {token}")


def _makefile_prereqs(text: str, target: str) -> tuple[str, ...] | None:
    prefix = f"{target}:"
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith(prefix):
            continue
        chunks = [line[len(prefix):].strip()]
        cursor = index
        while chunks[-1].endswith("\\"):
            chunks[-1] = chunks[-1][:-1].strip()
            cursor += 1
            if cursor >= len(lines):
                return ()
            chunks.append(lines[cursor].strip())
        prereq_text = " ".join(chunk for chunk in chunks if chunk)
        return tuple(prereq_text.split())
    return None


def _makefile_phony_targets(text: str) -> tuple[str, ...]:
    targets: list[str] = []
    for line in text.splitlines():
        if line.startswith(".PHONY:"):
            targets.extend(line[len(".PHONY:") :].strip().split())
    return tuple(targets)


def _makefile_recipe(text: str, target: str) -> tuple[str, ...] | None:
    prefix = f"{target}:"
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith(prefix):
            continue
        cursor = index
        while lines[cursor].rstrip().endswith("\\"):
            cursor += 1
            if cursor >= len(lines):
                return ()
        recipe: list[str] = []
        for recipe_line in lines[cursor + 1 :]:
            if not recipe_line.startswith("\t"):
                break
            recipe.append(recipe_line.strip())
        return tuple(recipe)
    return None


def _list_items_after_heading(text: str, heading: str) -> tuple[str, ...] | None:
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


def _all_bullet_items_after_heading(text: str, heading: str) -> tuple[str, ...] | None:
    lines = text.splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        return None
    items: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return tuple(items)


def _heading_order(text: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in text.splitlines() if line.startswith("## "))


def _ordered_items_after_marker(text: str, marker: str) -> tuple[str, ...] | None:
    lines = text.splitlines()
    try:
        start = lines.index(marker)
    except ValueError:
        return None
    items: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        stripped = line.strip()
        if not stripped:
            continue
        prefix, sep, value = stripped.partition(". ")
        if sep and prefix.isdigit():
            items.append(value.strip())
        elif items:
            break
    return tuple(items)


def _command_block_after_marker(text: str, marker: str) -> tuple[str, ...] | None:
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


def _contains_readme_release_documents(errors: list[str]) -> None:
    if not CONTROL_README.is_file():
        errors.append(f"missing release-control README: {CONTROL_README.relative_to(ROOT).as_posix()}")
        return
    text = CONTROL_README.read_text(encoding="utf-8")
    actual_documents = _list_items_after_heading(text, "## Release Documents")
    if actual_documents is None:
        errors.append("release-control README missing section: ## Release Documents")
        return
    if actual_documents != README_RELEASE_DOCUMENTS:
        errors.append(
            "release-control README documents mismatch: "
            f"expected={README_RELEASE_DOCUMENTS!r} actual={actual_documents!r}"
        )


def _contains_readme_section_order(errors: list[str]) -> None:
    if not CONTROL_README.is_file():
        errors.append(f"missing release-control README: {CONTROL_README.relative_to(ROOT).as_posix()}")
        return
    text = CONTROL_README.read_text(encoding="utf-8")
    actual_order = _heading_order(text)
    if actual_order != README_SECTION_ORDER:
        errors.append(
            "release-control README section order mismatch: "
            f"expected={README_SECTION_ORDER!r} actual={actual_order!r}"
        )


def _contains_readme_section_list(
    heading: str,
    expected_items: tuple[str, ...],
    errors: list[str],
) -> None:
    if not CONTROL_README.is_file():
        errors.append(f"missing release-control README: {CONTROL_README.relative_to(ROOT).as_posix()}")
        return
    text = CONTROL_README.read_text(encoding="utf-8")
    actual_items = _list_items_after_heading(text, heading)
    if actual_items is None:
        errors.append(f"release-control README missing section: {heading}")
        return
    if actual_items != expected_items:
        errors.append(
            "release-control README section items mismatch: "
            f"{heading} expected={expected_items!r} actual={actual_items!r}"
        )


def _contains_readme_boundaries(errors: list[str]) -> None:
    if not CONTROL_README.is_file():
        errors.append(f"missing release-control README: {CONTROL_README.relative_to(ROOT).as_posix()}")
        return
    text = CONTROL_README.read_text(encoding="utf-8")
    actual_boundaries = _list_items_after_heading(text, "It does not:")
    if actual_boundaries is None:
        errors.append("release-control README missing boundary marker: It does not:")
        return
    if actual_boundaries != README_BOUNDARY_EXCLUSIONS:
        errors.append(
            "release-control README boundary exclusions mismatch: "
            f"expected={README_BOUNDARY_EXCLUSIONS!r} actual={actual_boundaries!r}"
        )


def _contains_readme_gate_commands(errors: list[str]) -> None:
    if not CONTROL_README.is_file():
        errors.append(f"missing release-control README: {CONTROL_README.relative_to(ROOT).as_posix()}")
        return
    text = CONTROL_README.read_text(encoding="utf-8")
    expected_blocks = (
        ("## Required Gates", README_REQUIRED_GATES_COMMANDS),
        ("Supporting gates:", README_SUPPORTING_GATES_COMMANDS),
        ("Formal-release hardening gate:", README_HARDENING_GATE_COMMANDS),
    )
    for marker, expected_commands in expected_blocks:
        actual_commands = _command_block_after_marker(text, marker)
        if actual_commands is None:
            errors.append(f"release-control README missing gate command block after marker: {marker}")
            continue
        if actual_commands != expected_commands:
            errors.append(
                "release-control README gate command block mismatch: "
                f"{marker} expected={expected_commands!r} actual={actual_commands!r}"
            )


def _contains_readme_rollback_items(errors: list[str]) -> None:
    if not CONTROL_README.is_file():
        errors.append(f"missing release-control README: {CONTROL_README.relative_to(ROOT).as_posix()}")
        return
    text = CONTROL_README.read_text(encoding="utf-8")
    actual_items = _list_items_after_heading(text, "## Rollback")
    if actual_items is None:
        errors.append("release-control README missing section: ## Rollback")
        return
    if actual_items != README_ROLLBACK_ITEMS:
        errors.append(
            "release-control README rollback items mismatch: "
            f"expected={README_ROLLBACK_ITEMS!r} actual={actual_items!r}"
        )


def _contains_notes_minimum_verification(errors: list[str]) -> None:
    if not RELEASE_NOTES.is_file():
        errors.append(f"missing release notes: {RELEASE_NOTES.relative_to(ROOT).as_posix()}")
        return
    text = RELEASE_NOTES.read_text(encoding="utf-8")
    actual_commands = _command_block_after_marker(text, "Minimum pre-release verification:")
    if actual_commands is None:
        errors.append("release notes missing minimum pre-release verification command block")
        return
    if actual_commands != NOTES_MINIMUM_VERIFICATION_COMMANDS:
        errors.append(
            "release notes minimum verification mismatch: "
            f"expected={NOTES_MINIMUM_VERIFICATION_COMMANDS!r} actual={actual_commands!r}"
        )


def _contains_notes_section_order(errors: list[str]) -> None:
    if not RELEASE_NOTES.is_file():
        errors.append(f"missing release notes: {RELEASE_NOTES.relative_to(ROOT).as_posix()}")
        return
    text = RELEASE_NOTES.read_text(encoding="utf-8")
    actual_order = _heading_order(text)
    if actual_order != NOTES_SECTION_ORDER:
        errors.append(
            "release notes section order mismatch: "
            f"expected={NOTES_SECTION_ORDER!r} actual={actual_order!r}"
        )


def _contains_notes_env_acceptance(errors: list[str]) -> None:
    if not RELEASE_NOTES.is_file():
        errors.append(f"missing release notes: {RELEASE_NOTES.relative_to(ROOT).as_posix()}")
        return
    text = RELEASE_NOTES.read_text(encoding="utf-8")
    actual_commands = _command_block_after_marker(text, "Environment-specific acceptance:")
    if actual_commands is None:
        errors.append("release notes missing environment-specific acceptance command block")
        return
    if actual_commands != NOTES_ENV_ACCEPTANCE_COMMANDS:
        errors.append(
            "release notes environment-specific acceptance mismatch: "
            f"expected={NOTES_ENV_ACCEPTANCE_COMMANDS!r} actual={actual_commands!r}"
        )


def _contains_notes_scope_items(errors: list[str]) -> None:
    if not RELEASE_NOTES.is_file():
        errors.append(f"missing release notes: {RELEASE_NOTES.relative_to(ROOT).as_posix()}")
        return
    text = RELEASE_NOTES.read_text(encoding="utf-8")
    actual_items = _list_items_after_heading(text, "## Scope")
    if actual_items is None:
        errors.append("release notes missing section: ## Scope")
        return
    if actual_items != NOTES_SCOPE_ITEMS:
        errors.append(
            "release notes scope items mismatch: "
            f"expected={NOTES_SCOPE_ITEMS!r} actual={actual_items!r}"
        )


def _contains_notes_text_snippets(errors: list[str]) -> None:
    if not RELEASE_NOTES.is_file():
        errors.append(f"missing release notes: {RELEASE_NOTES.relative_to(ROOT).as_posix()}")
        return
    text = RELEASE_NOTES.read_text(encoding="utf-8")
    for snippet in NOTES_TEXT_SNIPPETS:
        if snippet not in text:
            errors.append(f"release notes missing required text snippet: {snippet}")


def _contains_notes_tag_plan(errors: list[str]) -> None:
    if not RELEASE_NOTES.is_file():
        errors.append(f"missing release notes: {RELEASE_NOTES.relative_to(ROOT).as_posix()}")
        return
    text = RELEASE_NOTES.read_text(encoding="utf-8")
    actual_items = _list_items_after_heading(text, "## Tag Plan")
    if actual_items is None:
        errors.append("release notes missing section: ## Tag Plan")
        return
    if actual_items != NOTES_TAG_PLAN_ITEMS:
        errors.append(
            "release notes tag plan mismatch: "
            f"expected={NOTES_TAG_PLAN_ITEMS!r} actual={actual_items!r}"
        )


def _contains_notes_known_limits(errors: list[str]) -> None:
    if not RELEASE_NOTES.is_file():
        errors.append(f"missing release notes: {RELEASE_NOTES.relative_to(ROOT).as_posix()}")
        return
    text = RELEASE_NOTES.read_text(encoding="utf-8")
    actual_items = _list_items_after_heading(text, "## Known Limits")
    if actual_items is None:
        errors.append("release notes missing section: ## Known Limits")
        return
    if actual_items != NOTES_KNOWN_LIMITS_ITEMS:
        errors.append(
            "release notes known limits mismatch: "
            f"expected={NOTES_KNOWN_LIMITS_ITEMS!r} actual={actual_items!r}"
        )


def _contains_release_index_planned_items(
    path: Path,
    heading: str,
    expected_items: tuple[str, ...],
    errors: list[str],
) -> None:
    if not path.is_file():
        errors.append(f"missing release index: {path.relative_to(ROOT).as_posix()}")
        return
    text = path.read_text(encoding="utf-8")
    actual_items = _all_bullet_items_after_heading(text, heading)
    if actual_items is None:
        errors.append(f"{path.relative_to(ROOT).as_posix()} missing section: {heading}")
        return
    if actual_items != expected_items:
        errors.append(
            f"{path.relative_to(ROOT).as_posix()} planned release items mismatch: "
            f"expected={expected_items!r} actual={actual_items!r}"
        )


def _contains_versioning_formal_release_items(errors: list[str]) -> None:
    if not VERSIONING.is_file():
        errors.append(f"missing versioning doc: {VERSIONING.relative_to(ROOT).as_posix()}")
        return
    text = VERSIONING.read_text(encoding="utf-8")
    actual_items = _list_items_after_heading(text, "## 8) v2.0.0 Formal Release Line")
    if actual_items is None:
        errors.append("versioning doc missing section: ## 8) v2.0.0 Formal Release Line")
        return
    if actual_items != VERSIONING_FORMAL_RELEASE_ITEMS:
        errors.append(
            "versioning formal release items mismatch: "
            f"expected={VERSIONING_FORMAL_RELEASE_ITEMS!r} actual={actual_items!r}"
        )


def _contains_versioning_section_order(errors: list[str]) -> None:
    if not VERSIONING.is_file():
        errors.append(f"missing versioning doc: {VERSIONING.relative_to(ROOT).as_posix()}")
        return
    text = VERSIONING.read_text(encoding="utf-8")
    actual_order = _heading_order(text)
    if actual_order != VERSIONING_SECTION_ORDER:
        errors.append(
            "versioning section order mismatch: "
            f"expected={VERSIONING_SECTION_ORDER!r} actual={actual_order!r}"
        )


def _contains_versioning_tag_type_items(errors: list[str]) -> None:
    if not VERSIONING.is_file():
        errors.append(f"missing versioning doc: {VERSIONING.relative_to(ROOT).as_posix()}")
        return
    text = VERSIONING.read_text(encoding="utf-8")
    actual_items = _list_items_after_heading(text, "## 1) Tag Types")
    if actual_items is None:
        errors.append("versioning doc missing section: ## 1) Tag Types")
        return
    if actual_items != VERSIONING_TAG_TYPE_ITEMS:
        errors.append(
            "versioning tag type items mismatch: "
            f"expected={VERSIONING_TAG_TYPE_ITEMS!r} actual={actual_items!r}"
        )


def _contains_versioning_no_history_rewrite_items(errors: list[str]) -> None:
    if not VERSIONING.is_file():
        errors.append(f"missing versioning doc: {VERSIONING.relative_to(ROOT).as_posix()}")
        return
    text = VERSIONING.read_text(encoding="utf-8")
    actual_items = _list_items_after_heading(text, "## 6) No History Rewrite")
    if actual_items is None:
        errors.append("versioning doc missing section: ## 6) No History Rewrite")
        return
    if actual_items != VERSIONING_NO_HISTORY_REWRITE_ITEMS:
        errors.append(
            "versioning no-history-rewrite items mismatch: "
            f"expected={VERSIONING_NO_HISTORY_REWRITE_ITEMS!r} actual={actual_items!r}"
        )


def _contains_versioning_tag_precheck_items(errors: list[str]) -> None:
    if not VERSIONING.is_file():
        errors.append(f"missing versioning doc: {VERSIONING.relative_to(ROOT).as_posix()}")
        return
    text = VERSIONING.read_text(encoding="utf-8")
    actual_items = _list_items_after_heading(text, "## 7) Tag Pre-Check List (Process)")
    if actual_items is None:
        errors.append("versioning doc missing section: ## 7) Tag Pre-Check List (Process)")
        return
    if actual_items != VERSIONING_TAG_PRECHECK_ITEMS:
        errors.append(
            "versioning tag pre-check items mismatch: "
            f"expected={VERSIONING_TAG_PRECHECK_ITEMS!r} actual={actual_items!r}"
        )


def _contains_promotion_order(path: Path, marker: str, expected_order: tuple[str, ...], errors: list[str]) -> None:
    if not path.is_file():
        errors.append(f"missing promotion-order doc: {path.relative_to(ROOT).as_posix()}")
        return
    text = path.read_text(encoding="utf-8")
    actual_order = _ordered_items_after_marker(text, marker)
    if actual_order is None:
        errors.append(f"{path.relative_to(ROOT).as_posix()} missing promotion marker: {marker}")
        return
    if actual_order != expected_order:
        errors.append(
            f"{path.relative_to(ROOT).as_posix()} promotion order mismatch: "
            f"expected={expected_order!r} actual={actual_order!r}"
        )


def _contains_makefile_targets(errors: list[str]) -> None:
    if not MAKEFILE.is_file():
        errors.append(f"missing Makefile: {MAKEFILE.relative_to(ROOT).as_posix()}")
        return
    text = MAKEFILE.read_text(encoding="utf-8")
    phony_targets = _makefile_phony_targets(text)
    for target in MAKEFILE_PHONY_TARGETS:
        if target not in phony_targets:
            errors.append(f"Makefile missing .PHONY target: {target}")
    for target, expected_prereqs in MAKEFILE_TARGET_PREREQS:
        actual_prereqs = _makefile_prereqs(text, target)
        if actual_prereqs is None:
            errors.append(f"Makefile missing target: {target}")
            continue
        if actual_prereqs != expected_prereqs:
            errors.append(
                "Makefile target prereqs mismatch: "
                f"{target} expected={expected_prereqs!r} actual={actual_prereqs!r}"
            )
    for target, expected_recipe in MAKEFILE_TARGET_RECIPES:
        actual_recipe = _makefile_recipe(text, target)
        if actual_recipe is None:
            errors.append(f"Makefile missing target: {target}")
            continue
        if actual_recipe != expected_recipe:
            errors.append(
                "Makefile target recipe mismatch: "
                f"{target} expected={expected_recipe!r} actual={actual_recipe!r}"
            )


def main() -> int:
    errors: list[str] = []
    _contains_all(CONTROL_README, README_TOKENS, errors)
    _contains_all(RELEASE_NOTES, NOTES_TOKENS, errors)
    _contains_all(VERSIONING, VERSIONING_TOKENS, errors)
    _contains_all(RELEASE_INDEX_EN, RELEASE_INDEX_EN_TOKENS, errors)
    _contains_all(RELEASE_INDEX_ZH, RELEASE_INDEX_ZH_TOKENS, errors)
    _contains_all(VERIFY_README, VERIFY_README_TOKENS, errors)
    _contains_readme_section_order(errors)
    _contains_readme_section_list("## Status", README_STATUS_ITEMS, errors)
    _contains_readme_section_list("## Layer Target / Module / Reason", README_LAYER_TARGET_ITEMS, errors)
    _contains_readme_release_documents(errors)
    _contains_readme_boundaries(errors)
    _contains_readme_gate_commands(errors)
    _contains_readme_rollback_items(errors)
    _contains_notes_section_order(errors)
    _contains_notes_minimum_verification(errors)
    _contains_notes_env_acceptance(errors)
    _contains_notes_scope_items(errors)
    _contains_notes_text_snippets(errors)
    _contains_notes_tag_plan(errors)
    _contains_notes_known_limits(errors)
    _contains_release_index_planned_items(
        RELEASE_INDEX_EN,
        "## Planned Formal Release",
        RELEASE_INDEX_EN_PLANNED_ITEMS,
        errors,
    )
    _contains_release_index_planned_items(
        RELEASE_INDEX_ZH,
        "## 计划正式发布",
        RELEASE_INDEX_ZH_PLANNED_ITEMS,
        errors,
    )
    _contains_versioning_section_order(errors)
    _contains_versioning_tag_type_items(errors)
    _contains_versioning_no_history_rewrite_items(errors)
    _contains_versioning_tag_precheck_items(errors)
    _contains_versioning_formal_release_items(errors)
    _contains_promotion_order(CONTROL_README, "## Promotion Order", README_PROMOTION_ORDER, errors)
    _contains_promotion_order(VERSIONING, "Promotion order:", VERSIONING_PROMOTION_ORDER, errors)
    _contains_makefile_targets(errors)
    if errors:
        print("[release_v2_0_0_control_docs_guard] FAIL")
        for error in errors:
            print(error)
        return 2
    print("[release_v2_0_0_control_docs_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
