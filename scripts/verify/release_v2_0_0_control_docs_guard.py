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
    "Enforces RC and formal-release command blocks exactly.",
    "versioning/release-index review",
    "`make verify.release.v2_0_0.evidence_manifest.guard`",
    "evidence table rows/order",
    "controlled-doc artifact coverage",
    "`make verify.release.v2_0_0.control_docs.guard`",
    "release indexes, verification catalog, and Makefile target dependencies",
    "`PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard`",
    "Recorded sample artifact directories may validate schema shape only",
    "final release signoff requires the recorded prod-sim acceptance run directory",
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

VERSIONING_PROMOTION_ORDER = (
    "Merge reviewed release-prep work to `main`.",
    "Run `make verify.release.v2_0_0.preflight` on the reviewed release commit.",
    "Create `gate-release-v2.0` only after gate evidence passes.",
    "Run `make verify.release.v2_0_0.product_hardening` and close any blocker.",
    "Run `PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard` after prod-sim acceptance evidence is recorded.",
    "Create `v2.0.0-rc1` only after RC evidence passes.",
    "Create `v2.0.0` only after prod-sim acceptance and release checklist signoff.",
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

FORBIDDEN_TOKENS = (
    "Product delivery baseline: 9 modules",
    "reuse `v1.0.0`",
    "git tag -f",
    "git push --force",
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


def main() -> int:
    errors: list[str] = []
    _contains_all(CONTROL_README, README_TOKENS, errors)
    _contains_all(RELEASE_NOTES, NOTES_TOKENS, errors)
    _contains_all(VERSIONING, VERSIONING_TOKENS, errors)
    _contains_all(RELEASE_INDEX_EN, RELEASE_INDEX_EN_TOKENS, errors)
    _contains_all(RELEASE_INDEX_ZH, RELEASE_INDEX_ZH_TOKENS, errors)
    _contains_all(VERIFY_README, VERIFY_README_TOKENS, errors)
    _contains_readme_release_documents(errors)
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
