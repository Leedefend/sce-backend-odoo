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
    "make release.dev.acceptance.publish",
    "PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.prod.sim.acceptance.evidence.schema.guard",
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

    if errors:
        print("[release_v2_0_0_checklist_guard] FAIL")
        for error in errors:
            print(error)
        return 2
    print("[release_v2_0_0_checklist_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
