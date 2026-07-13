#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "addons/smart_construction_core/core_extension.py"
CATALOG = ROOT / "addons/smart_construction_core/core_extension_policy_catalog.py"
DOC = ROOT / "docs/engineering_convergence/core_extension_responsibility_map.md"
MAX_LINES = 4146


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def main() -> int:
    errors: list[str] = []
    if not TARGET.is_file():
        errors.append("core_extension.py missing")
    elif _line_count(TARGET) > MAX_LINES:
        errors.append(f"core_extension.py line budget exceeded: {_line_count(TARGET)} > {MAX_LINES}")
    elif "from odoo.addons.smart_construction_core.core_extension_policy_catalog import (" not in TARGET.read_text(
        encoding="utf-8"
    ):
        errors.append("core_extension.py must import the policy catalog facade names")

    if not CATALOG.is_file():
        errors.append("core_extension_policy_catalog.py missing")
    else:
        catalog_text = CATALOG.read_text(encoding="utf-8")
        required_catalog_tokens = [
            "ROLE_SURFACE_OVERRIDES = {",
            "ROLE_GROUPS_EXPLICIT = {",
            "NAV_MENU_SCENE_MAP = {",
            "NAV_ACTION_SCENE_MAP = {",
            "FILE_ATTACHMENT_ALLOWED_MODEL_EXACT = {",
            "FILE_UPLOAD_ALLOWED_MODELS =",
            "FILE_DOWNLOAD_ALLOWED_MODELS =",
            "LEGACY_VISIBLE_BUSINESS_COLUMN_LABELS_BY_MODEL = {",
            "MODEL_CODE_MAPPING = {",
            "CRITICAL_SCENE_TARGET_OVERRIDES = {",
            "INDUSTRY_CREATE_FIELD_FALLBACKS = {",
            "USER_CONFIRMED_FORMAL_LIST_ACTION_XMLIDS = {",
            "API_DATA_WRITE_ALLOWLIST = {",
            "API_DATA_MUTATION_POLICIES = {",
            "DRAFT_DELETE_ALLOWED_STATES =",
        ]
        for token in required_catalog_tokens:
            if token not in catalog_text:
                errors.append(f"policy catalog missing token: {token}")
        forbidden_tokens = ("env[", ".search(", ".write(", "http", "requests.", "Path(")
        for token in forbidden_tokens:
            if token in catalog_text:
                errors.append(f"policy catalog must remain static; found token: {token}")

    if not DOC.is_file():
        errors.append("core_extension responsibility map missing")
    else:
        text = DOC.read_text(encoding="utf-8")
        required_tokens = [
            "Target file: `addons/smart_construction_core/core_extension.py`",
            "Current line budget: `<=4146`.",
            "`core_extension.py` is the construction-industry contribution facade",
            "`smart_core_register(registry)`",
            "`smart_core_extend_system_init(data, env, user)`",
            "`smart_core_finalize_projected_contract_data(env, data, context)`",
            "no extraction in this stage",
            "Stage 1a Catalog Extraction",
            "`core_extension_policy_catalog.py` owns role surface overrides",
            "`core_extension.py` is locked at `<=4251` lines",
            "Stage 1b Catalog Expansion",
            "`core_extension_policy_catalog.py` also owns legacy visible business column",
            "API data unlink policy tables remain in the facade",
            "`core_extension.py` is locked at `<=4162` lines",
            "Stage 1c API Catalog Extraction",
            "`core_extension_policy_catalog.py` owns API write allowlists",
            "`core_extension.py` is locked at `<=4146` lines",
            "future PRs from this branch should include multiple commits",
            "open only when",
        ]
        for token in required_tokens:
            if token not in text:
                errors.append(f"responsibility map missing token: {token}")

    if errors:
        print("[core_extension_responsibility_map_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[core_extension_responsibility_map_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
