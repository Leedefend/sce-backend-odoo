#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "addons/smart_construction_core/core_extension.py"
CATALOG = ROOT / "addons/smart_construction_core/core_extension_policy_catalog.py"
CAPABILITIES = ROOT / "addons/smart_construction_core/core_extension_capabilities.py"
FORM_ACTIONS = ROOT / "addons/smart_construction_core/core_extension_form_actions.py"
INTENTS = ROOT / "addons/smart_construction_core/core_extension_intents.py"
SYSTEM_INIT = ROOT / "addons/smart_construction_core/core_extension_system_init.py"
WORKSPACE_FACTS = ROOT / "addons/smart_construction_core/core_extension_workspace_facts.py"
NAVIGATION_POLICY = ROOT / "addons/smart_construction_core/core_extension_navigation_policy.py"
CONTRACT_PROJECTION = ROOT / "addons/smart_construction_core/core_extension_contract_projection.py"
DOC = ROOT / "docs/engineering_convergence/core_extension_responsibility_map.md"
MAX_LINES = 1662


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

    if not CAPABILITIES.is_file():
        errors.append("core_extension_capabilities.py missing")
    else:
        capabilities_text = CAPABILITIES.read_text(encoding="utf-8")
        if "def build_capability_contribution_item(" not in capabilities_text:
            errors.append("capability helper module missing build_capability_contribution_item")
        forbidden_tokens = ("odoo.", "env[", ".search(", ".write(", "http", "requests.", "Path(")
        for token in forbidden_tokens:
            if token in capabilities_text:
                errors.append(f"capability helper module must remain pure; found token: {token}")

    if not FORM_ACTIONS.is_file():
        errors.append("core_extension_form_actions.py missing")
    else:
        form_actions_text = FORM_ACTIONS.read_text(encoding="utf-8")
        if "def build_payment_form_business_action_contract(" not in form_actions_text:
            errors.append("form action module missing build_payment_form_business_action_contract")
        forbidden_tokens = ("odoo.", "env[", ".search(", ".write(", "http", "requests.", "Path(")
        for token in forbidden_tokens:
            if token in form_actions_text:
                errors.append(f"form action module must remain pure; found token: {token}")

    if not INTENTS.is_file():
        errors.append("core_extension_intents.py missing")
    else:
        intents_text = INTENTS.read_text(encoding="utf-8")
        required_intent_tokens = [
            "def get_intent_handler_contributions():",
            "APPROVAL_POLICY_INTENTS",
            "ProjectExecutionAdvanceHandler = None",
            "CostTrackingRecordCreateHandler = None",
            "\"source_module\": \"smart_construction_core\"",
        ]
        for token in required_intent_tokens:
            if token not in intents_text:
                errors.append(f"intent helper module missing token: {token}")
        forbidden_tokens = ("env[", ".search(", ".write(", "registry[")
        for token in forbidden_tokens:
            if token in intents_text:
                errors.append(f"intent helper module must not perform registry/ORM mutation; found token: {token}")

    if not SYSTEM_INIT.is_file():
        errors.append("core_extension_system_init.py missing")
    else:
        system_init_text = SYSTEM_INIT.read_text(encoding="utf-8")
        if "def apply_system_init_profile_overrides(" not in system_init_text:
            errors.append("system init helper missing apply_system_init_profile_overrides")
        forbidden_tokens = ("odoo.", "env[", ".search(", ".write(", "http", "requests.", "Path(")
        for token in forbidden_tokens:
            if token in system_init_text:
                errors.append(f"system init helper must remain pure; found token: {token}")

    if not WORKSPACE_FACTS.is_file():
        errors.append("core_extension_workspace_facts.py missing")
    else:
        workspace_text = WORKSPACE_FACTS.read_text(encoding="utf-8")
        required_workspace_tokens = [
            "def _safe_search_read(",
            "def _model_has_field(",
            "def _build_task_action_rows(",
            "def _build_payment_action_rows(",
            "def _build_risk_action_rows(",
            "def _build_project_action_rows(",
            "def _build_role_entry_contract_rows(",
            "def _build_home_block_contract_rows(",
            "def _build_enterprise_enablement_contract(",
        ]
        for token in required_workspace_tokens:
            if token not in workspace_text:
                errors.append(f"workspace facts module missing token: {token}")
        forbidden_tokens = (".write(", "requests.", "registry[")
        for token in forbidden_tokens:
            if token in workspace_text:
                errors.append(f"workspace facts module must not mutate records/registry; found token: {token}")

    if not NAVIGATION_POLICY.is_file():
        errors.append("core_extension_navigation_policy.py missing")
    else:
        navigation_text = NAVIGATION_POLICY.read_text(encoding="utf-8")
        required_navigation_tokens = [
            "def smart_core_business_config_admin_group_xmlids(",
            "def smart_core_relation_entry_policy(",
            "def smart_core_menu_delivery_token_policy(",
            "def smart_core_resolve_release_actor_role_codes(",
            "def smart_core_app_shell_contract(",
            "def smart_core_scene_entry_orchestrator_specs(",
            "def smart_core_user_data_acceptance_nav_contract(",
        ]
        for token in required_navigation_tokens:
            if token not in navigation_text:
                errors.append(f"navigation policy module missing token: {token}")
        forbidden_tokens = (".write(",)
        for token in forbidden_tokens:
            if token in navigation_text:
                errors.append(f"navigation policy module must not mutate records/registry; found token: {token}")

    if not CONTRACT_PROJECTION.is_file():
        errors.append("core_extension_contract_projection.py missing")
    else:
        projection_text = CONTRACT_PROJECTION.read_text(encoding="utf-8")
        required_projection_tokens = [
            "def smart_core_finalize_unified_page_contract_v2(",
            "def smart_core_normalize_projected_contract_data(",
            "def smart_core_normalize_unified_page_contract_v2(",
            "def _sc_normalize_construction_diary_form(",
            "def _sc_general_contract_tax_contract(",
            "def _sc_normalize_general_contract_company_form(",
            "def _sc_inject_workflow_contract(",
        ]
        for token in required_projection_tokens:
            if token not in projection_text:
                errors.append(f"contract projection module missing token: {token}")
        forbidden_tokens = (".write(",)
        for token in forbidden_tokens:
            if token in projection_text:
                errors.append(f"contract projection module must not write records/registry; found token: {token}")

    if not DOC.is_file():
        errors.append("core_extension responsibility map missing")
    else:
        text = DOC.read_text(encoding="utf-8")
        required_tokens = [
            "Target file: `addons/smart_construction_core/core_extension.py`",
            "Current line budget: `<=1662`.",
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
            "Stage 2 Capability Payload Builder",
            "`core_extension_capabilities.py` owns the pure capability contribution payload",
            "the facade hooks still own registry loading",
            "`core_extension.py` is locked at `<=3955` lines",
            "Stage 3 Form Action Builder",
            "`core_extension_form_actions.py` owns pure normalization",
            "`smart_core_form_business_actions` keeps model filtering",
            "`core_extension.py` is locked at `<=3875` lines",
            "Stage 4 Intent Handler Contributions",
            "`core_extension_intents.py` owns import-tolerant construction intent handler",
            "`smart_core_register` remains in the facade",
            "`core_extension.py` is locked at `<=3675` lines",
            "Stage 5 System Init Profile Overrides",
            "`core_extension_system_init.py` owns pure workspace keyword",
            "`smart_core_extend_system_init` keeps input validation",
            "`core_extension.py` is locked at `<=3471` lines",
            "Stage 6 Workspace Fact Builders",
            "`core_extension_workspace_facts.py` owns safe workspace ORM reads",
            "`get_system_init_fact_contributions` remains in the facade",
            "`core_extension.py` is locked at `<=3020` lines",
            "Stage 7 Navigation Policy Hooks",
            "`core_extension_navigation_policy.py` owns business config refs",
            "`core_extension.py` imports those public hook names directly",
            "`core_extension.py` is locked at `<=2371` lines",
            "Stage 8 Contract Projection Hooks",
            "`core_extension_contract_projection.py` owns construction-specific v2 contract",
            "`core_extension.py` imports the three public hook names directly",
            "`core_extension.py` is locked at `<=1662` lines",
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
