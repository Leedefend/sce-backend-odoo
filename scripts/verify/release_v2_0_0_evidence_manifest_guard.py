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
    "`make verify.release.v2_0_0.governance.guard`",
    "`PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard`",
    "Evidence from `sc_prod_sim` must not be presented as `sc_prod` evidence.",
    "Production deployment evidence is recorded separately after supervised",
    "Failed evidence is not overwritten without preserving the failure reason",
    "prod-sim acceptance artifact path to be recorded",
)

FORBIDDEN_TOKENS = (
    "v1.0.0` |",
    "artifacts/migration/prod_sim_fresh_replay_20260506T000602",
    "artifacts/migration/prod_sim_fresh_replay_20260505T230223",
    "sc_prod evidence",
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

    if errors:
        print("[release_v2_0_0_evidence_manifest_guard] FAIL")
        for error in errors:
            print(error)
        return 2
    print("[release_v2_0_0_evidence_manifest_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
