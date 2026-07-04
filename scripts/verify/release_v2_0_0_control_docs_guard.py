#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CONTROL_README = ROOT / "docs" / "ops" / "releases" / "v2.0.0" / "README.md"
RELEASE_NOTES = ROOT / "docs" / "ops" / "release_notes_v2.0.0.md"
VERSIONING = ROOT / "docs" / "ops" / "versioning.md"

README_TOKENS = (
    "# v2.0.0 Release Control",
    "- Version: `v2.0.0`",
    "- Planned gate tag: `gate-release-v2.0`",
    "- Planned RC tag: `v2.0.0-rc1`",
    "- Planned final tag: `v2.0.0`",
    "make verify.release.v2_0_0.preflight",
    "make verify.release.v2_0_0.product_hardening",
    "Run prod-sim acceptance.",
    "Create `v2.0.0` after formal release signoff.",
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
    "ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo",
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
    "Production deployment is not implied by creating `v2.0.0`",
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


def main() -> int:
    errors: list[str] = []
    _contains_all(CONTROL_README, README_TOKENS, errors)
    _contains_all(RELEASE_NOTES, NOTES_TOKENS, errors)
    _contains_all(VERSIONING, VERSIONING_TOKENS, errors)
    if errors:
        print("[release_v2_0_0_control_docs_guard] FAIL")
        for error in errors:
            print(error)
        return 2
    print("[release_v2_0_0_control_docs_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
