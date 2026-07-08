#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "addons/smart_construction_custom"
INDUSTRY_MODULES = [
    ROOT / "addons/smart_construction_core",
    ROOT / "addons/smart_construction_scene",
    ROOT / "addons/smart_construction_bootstrap",
]
MANIFEST = MODULE / "__manifest__.py"
HOOKS = MODULE / "hooks.py"
PARTNER_LOCATION = MODULE / "models/partner_location.py"
USER_DATA_BASELINE_PY = MODULE / "models/user_data_baseline.py"
MODELS_INIT = MODULE / "models/__init__.py"
USER_DATA_BASELINE_XML = MODULE / "data/user_data_baseline.xml"
LEGACY_USER_MASTER_XML = MODULE / "data/user_master_v1.xml"
HISTORY_BUSINESS_BASELINE_MANIFEST = MODULE / "data/user_history_business_data_baseline_manifest_v1.json"
LOWCODE_CUSTOMER_CONFIG_BASELINE_MANIFEST = MODULE / "data/lowcode_customer_config_baseline_manifest_v1.json"
USER_DATA_REBASELINE_SOURCE_MANIFEST = MODULE / "data/user_data_rebaseline_source_manifest_v1.json"
USER_DATA_REBASELINE_REPLAY_PREFLIGHT = MODULE / "data/user_data_rebaseline_replay_asset_preflight_v1.json"
USER_MODULE_DATA_BASELINE_CONTRACT = MODULE / "data/user_module_data_baseline_contract_v1.json"
USER_PREFERENCES_XML = MODULE / "data/user_preferences.xml"
BUSINESS_CAPABILITY_BASELINE = ROOT / "docs/product/business_capability_productization_baseline_v1.json"
MIGRATION_ASSET_PACKAGE_LOCK = ROOT / "docs/migration_alignment/migration_asset_package_lock_v1.json"
MAKEFILE = ROOT / "Makefile"
HISTORY_BASELINE_RESTORE_SCRIPT = ROOT / "scripts/migration/user_module_history_business_baseline_restore.sh"


def _parse_python(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _function_by_name(tree: ast.AST, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _call_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _call_names(node: ast.AST | None) -> list[str]:
    if node is None:
        return []
    return [_call_name(call) for call in ast.walk(node) if isinstance(call, ast.Call)]


def _manifest_data_files() -> list[str]:
    manifest = ast.literal_eval(MANIFEST.read_text(encoding="utf-8"))
    return [str(item) for item in manifest.get("data", [])]


def _xml_function_names(path: Path) -> list[str]:
    root = ET.parse(path).getroot()
    return [
        str(node.attrib.get("name") or "").strip()
        for node in root.iter("function")
        if str(node.attrib.get("model") or "").strip() == "sc.user.preference.initialization"
    ]


def _index(items: list[str], item: str) -> int:
    try:
        return items.index(item)
    except ValueError:
        return -1


def verify_manifest_boundary() -> list[str]:
    failures: list[str] = []
    data_files = _manifest_data_files()
    baseline = "data/user_data_baseline.xml"
    preferences = "data/user_preferences.xml"
    menu_preferences = "data/user_menu_preferences.xml"

    for item in [baseline, preferences, menu_preferences]:
        if item not in data_files:
            failures.append(f"smart_construction_custom manifest must include {item}")
    if "data/user_master_v1.xml" in data_files:
        failures.append("legacy user master payload must be loaded by the idempotent data baseline loader, not direct XML data")
    if "data/user_history_business_data_baseline_manifest_v1.json" in data_files:
        failures.append("history business baseline manifest must be read by the idempotent loader, not direct XML data")
    if "data/lowcode_customer_config_baseline_manifest_v1.json" in data_files:
        failures.append("low-code customer config baseline manifest must be guarded as a module contract, not direct XML data")

    baseline_index = _index(data_files, baseline)
    preference_index = _index(data_files, preferences)
    if baseline_index >= 0 and preference_index >= 0 and baseline_index > preference_index:
        failures.append("user data baseline must load before user preference contracts")

    return failures


def verify_lowcode_customer_config_baseline_manifest() -> list[str]:
    failures: list[str] = []
    if not LOWCODE_CUSTOMER_CONFIG_BASELINE_MANIFEST.exists():
        return ["user module must carry the low-code customer configuration baseline manifest"]
    payload = json.loads(LOWCODE_CUSTOMER_CONFIG_BASELINE_MANIFEST.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "lowcode_customer_config_baseline_manifest.v1":
        failures.append("low-code customer configuration baseline manifest schema_version mismatch")
    boundary = payload.get("module_boundary") if isinstance(payload.get("module_boundary"), dict) else {}
    if boundary.get("owner_module") != "smart_construction_custom":
        failures.append("low-code customer configuration baseline manifest must be owned by smart_construction_custom")
    promotion_rule = payload.get("promotion_rule") if isinstance(payload.get("promotion_rule"), dict) else {}
    promotion_text = json.dumps(promotion_rule, ensure_ascii=False)
    for token in ("tenant_runtime", "product_release", "smart_construction_custom"):
        if token not in promotion_text:
            failures.append(f"low-code customer configuration baseline promotion rule missing {token}")
    extraction = payload.get("extraction_assistant") if isinstance(payload.get("extraction_assistant"), dict) else {}
    expected_extraction = {
        "schema_version": "lowcode_customer_config_baseline_candidate.v1",
        "make_target": "make verify.lowcode_config.customer_baseline.candidate",
        "script": "scripts/verify/lowcode_customer_config_baseline_candidate.py",
        "artifact": "artifacts/backend/lowcode_customer_config_baseline_candidate.json",
        "module_asset_draft_schema_version": "lowcode_customer_config_module_asset_draft.v1",
        "module_asset_draft_make_target": "make verify.lowcode_config.customer_module_asset.draft",
        "module_asset_draft_script": "scripts/verify/lowcode_customer_config_module_asset_draft.py",
        "module_asset_draft_artifact": "artifacts/backend/lowcode_customer_config_module_asset_draft.json",
        "acceptance_decision_schema_version": "lowcode_customer_config_acceptance_decisions.v1",
        "acceptance_decision_template_make_target": "make verify.lowcode_config.customer_module_asset.acceptance_template",
        "acceptance_decision_template_script": "scripts/verify/lowcode_customer_config_acceptance_decision_template.py",
        "acceptance_decision_template_artifact": "artifacts/backend/lowcode_customer_config_acceptance_decisions_template.json",
        "accepted_module_asset_schema_version": "lowcode_customer_config_contracts.v1",
        "accepted_module_asset": "addons/smart_construction_custom/data/lowcode_customer_config_contracts_v1.json",
        "accepted_module_asset_replay_guard": "make verify.lowcode_config.customer_module_asset.replay.guard",
    }
    for key, expected in expected_extraction.items():
        if extraction.get(key) != expected:
            failures.append(f"low-code customer configuration baseline extraction assistant {key} mismatch")
    if not (ROOT / expected_extraction["script"]).exists():
        failures.append("low-code customer configuration baseline extraction assistant script is missing")
    draft_script = ROOT / expected_extraction["module_asset_draft_script"]
    if not draft_script.exists():
        failures.append("low-code customer configuration module asset draft script is missing")
    else:
        draft_text = draft_script.read_text(encoding="utf-8")
        for token in (
            "lowcode_customer_config_module_asset_draft.v1",
            "lowcode_customer_config_baseline_candidate.v1",
            "smart_construction_custom",
            "review_required",
            "not_applied_to_module",
            "proposed_assets",
        ):
            if token not in draft_text:
                failures.append(f"low-code customer configuration module asset draft script missing {token}")
    decision_template_script = ROOT / expected_extraction["acceptance_decision_template_script"]
    if not decision_template_script.exists():
        failures.append("low-code customer configuration acceptance decision template script is missing")
    else:
        decision_template_text = decision_template_script.read_text(encoding="utf-8")
        for token in (
            "lowcode_customer_config_acceptance_decisions.v1",
            "lowcode_customer_config_module_asset_draft.v1",
            "review_decision_template",
            "pending",
            "accepted",
            "rejected",
            "reviewer",
            "review_note",
        ):
            if token not in decision_template_text:
                failures.append(f"low-code customer configuration acceptance decision template script missing {token}")
    accepted_asset = ROOT / expected_extraction["accepted_module_asset"]
    if not accepted_asset.exists():
        failures.append("accepted low-code customer configuration module asset is missing")
    else:
        asset_payload = json.loads(accepted_asset.read_text(encoding="utf-8"))
        for key, expected in (
            ("schema_version", "lowcode_customer_config_contracts.v1"),
            ("source_draft_schema", "lowcode_customer_config_module_asset_draft.v1"),
            ("target_module", "smart_construction_custom"),
            ("artifact_status", "accepted_module_asset"),
        ):
            if asset_payload.get(key) != expected:
                failures.append(f"accepted low-code customer configuration module asset {key} mismatch")
    if not (ROOT / "scripts/verify/lowcode_customer_config_module_asset_replay_guard.py").exists():
        failures.append("accepted low-code customer configuration module asset replay guard is missing")
    surfaces = payload.get("replayable_surfaces") if isinstance(payload.get("replayable_surfaces"), list) else []
    surface_names = {str(item.get("surface") or "").strip() for item in surfaces if isinstance(item, dict)}
    for surface in ("menu_preferences", "form_preferences", "user_data_baseline"):
        if surface not in surface_names:
            failures.append(f"low-code customer configuration baseline missing replayable surface: {surface}")
    required_assets = payload.get("required_module_assets") if isinstance(payload.get("required_module_assets"), list) else []
    required_asset_set = {str(item) for item in required_assets}
    for required in (
        "addons/smart_construction_custom/models/user_preferences.py",
        "addons/smart_construction_custom/hooks.py",
        "addons/smart_construction_custom/data/user_preferences.xml",
        "addons/smart_construction_custom/data/user_menu_preferences.xml",
        "addons/smart_construction_custom/data/lowcode_customer_config_contracts_v1.json",
        "addons/smart_construction_custom/data/user_module_data_baseline_contract_v1.json",
    ):
        if required not in required_asset_set:
            failures.append(f"low-code customer configuration baseline missing required asset: {required}")
        elif not (ROOT / required).exists():
            failures.append(f"low-code customer configuration baseline references missing asset: {required}")
    required_guards = set(map(str, payload.get("required_guards") if isinstance(payload.get("required_guards"), list) else []))
    for guard in (
        "make verify.lowcode_config.boundary.guard",
        "make verify.lowcode_config.runtime_boundary.guard",
        "make verify.lowcode_config.customer_baseline.candidate",
        "make verify.lowcode_config.customer_module_asset.draft",
        "make verify.lowcode_config.customer_module_asset.acceptance_template",
        "make verify.lowcode_config.customer_module_asset.replay.guard",
        "make verify.business_config.snapshot",
    ):
        if guard not in required_guards:
            failures.append(f"low-code customer configuration baseline missing required guard: {guard}")
    return failures


def verify_history_business_data_baseline_manifest() -> list[str]:
    failures: list[str] = []
    if not HISTORY_BUSINESS_BASELINE_MANIFEST.exists():
        return ["user module must carry the locked user-visible history business data baseline manifest"]
    if not BUSINESS_CAPABILITY_BASELINE.exists():
        return ["product family baseline is missing"]
    if not MIGRATION_ASSET_PACKAGE_LOCK.exists():
        return ["migration asset package lock is missing"]
    if not HISTORY_BASELINE_RESTORE_SCRIPT.exists():
        return ["user module history business baseline restore script is missing"]

    payload = json.loads(HISTORY_BUSINESS_BASELINE_MANIFEST.read_text(encoding="utf-8"))
    product = json.loads(BUSINESS_CAPABILITY_BASELINE.read_text(encoding="utf-8"))
    lock = json.loads(MIGRATION_ASSET_PACKAGE_LOCK.read_text(encoding="utf-8"))
    standard = payload.get("completeness_standard") if isinstance(payload.get("completeness_standard"), dict) else {}
    external_lock = payload.get("external_payload_lock") if isinstance(payload.get("external_payload_lock"), dict) else {}
    legacy_catalog = payload.get("legacy_asset_catalog") if isinstance(payload.get("legacy_asset_catalog"), dict) else {}
    post_asset = payload.get("post_asset_closure") if isinstance(payload.get("post_asset_closure"), dict) else {}
    restore_entry = payload.get("restore_entry") if isinstance(payload.get("restore_entry"), dict) else {}
    families = payload.get("visible_business_families") if isinstance(payload.get("visible_business_families"), list) else []
    targets = post_asset.get("targets") if isinstance(post_asset.get("targets"), list) else []
    product_families = product.get("families") if isinstance(product.get("families"), list) else []
    product_keys = {str(item.get("key") or "").strip() for item in product_families if isinstance(item, dict)}
    manifest_keys = {str(item.get("key") or "").strip() for item in families if isinstance(item, dict)}

    if payload.get("manifest_id") != "scbs_user_visible_business_data_stable_baseline_v1":
        failures.append("history business baseline manifest_id must identify the stable user-visible baseline")
    if standard.get("basis") != "locked_user_visible_business_surface":
        failures.append("history business baseline must be based on the locked user-visible business surface")
    if not standard.get("not_complete_if_only_legacy_asset_catalog"):
        failures.append("history business baseline must explicitly reject legacy asset catalog only completion")
    if not standard.get("legacy_asset_package_count_is_not_completion_standard"):
        failures.append("history business baseline must state that the 23 legacy packages are not the completion standard")
    required_family_count = int((product.get("policy") or {}).get("required_family_count") or 0)
    if len(families) != required_family_count:
        failures.append(f"history business baseline family count mismatch: {len(families)} != {required_family_count}")
    if product_keys != manifest_keys:
        failures.append("history business baseline families must match product business capability baseline")
    if int(legacy_catalog.get("source_asset_package_count") or 0) < 23:
        failures.append("history business baseline must retain the original migration asset catalog as one source")
    if len(legacy_catalog.get("package_order") or []) < 23:
        failures.append("history business baseline legacy asset package_order is incomplete")
    if int(post_asset.get("target_count") or 0) < 70 or len(targets) < 70:
        failures.append("history business baseline must include post-asset replay/write/projection closure targets")
    if external_lock.get("path") != "docs/migration_alignment/migration_asset_package_lock_v1.json":
        failures.append("history business baseline must pin the external migration asset package lock")
    if external_lock.get("package_id") != lock.get("package_id") or external_lock.get("sha256") is None:
        failures.append("history business baseline external payload lock must match package lock identity and include sha256")
    if external_lock.get("payload_mode") != "packaged_artifacts":
        failures.append("history business baseline external payload must use packaged_artifacts mode")
    if external_lock.get("privacy_policy") != "private_authenticated_delivery_only":
        failures.append("history business baseline must keep private authenticated payload delivery policy")
    if restore_entry.get("make_target") != "user_module.history_business_baseline.restore":
        failures.append("history business baseline must expose user_module.history_business_baseline.restore")
    if restore_entry.get("script") != "scripts/migration/user_module_history_business_baseline_restore.sh":
        failures.append("history business baseline restore_entry must point to the restore script")
    if restore_entry.get("default_mode") != "rehearsal_only":
        failures.append("history business baseline restore must default to rehearsal_only")
    if restore_entry.get("apply_env") != "USER_MODULE_HISTORY_BASELINE_APPLY=1":
        failures.append("history business baseline restore must require explicit apply env")

    make_source = MAKEFILE.read_text(encoding="utf-8")
    if "user_module.history_business_baseline.restore:" not in make_source:
        failures.append("Makefile must publish user_module.history_business_baseline.restore")
    script_source = HISTORY_BASELINE_RESTORE_SCRIPT.read_text(encoding="utf-8")
    for snippet in [
        "migration.assets.fetch",
        "migration.assets.verify_all",
        "migration.assets.delivery_audit",
        "history.continuity.rehearse",
        "history.continuity.replay",
        "history.business.usable.init",
        "verify.user_module.data_baseline.runtime_audit",
        "USER_MODULE_HISTORY_BASELINE_APPLY",
    ]:
        if snippet not in script_source:
            failures.append(f"history baseline restore script must include {snippet}")

    required_targets = {
        "history.legacy_user_visible_surface.overlay.write",
        "history.daily_business_visible_surface.p0.write",
        "fresh_db.legacy_tax_deduction.replay.write",
        "fresh_db.legacy_self_funding.replay.write",
        "fresh_db.deduction_paid.projection.write",
        "fresh_db.arrival_confirmation.projection.write",
        "fresh_db.payment_execution.projection.write",
        "fresh_db.invoice_registration.projection.write",
        "fresh_db.fund_account_between.projection.write",
        "formal_entry_metadata.surface.write",
        "prod.sim.business.usable.init",
    }
    target_names = {str(item.get("target") or "").strip() for item in targets if isinstance(item, dict)}
    missing_targets = sorted(required_targets - target_names)
    if missing_targets:
        failures.append(f"history business baseline missing post-asset closure targets: {missing_targets}")
    unavailable_targets = sorted(
        str(item.get("target") or "").strip()
        for item in targets
        if isinstance(item, dict) and not item.get("available_in_makefile")
    )
    if unavailable_targets:
        failures.append(f"history business baseline references targets absent from Makefile: {unavailable_targets}")
    for family in families:
        if not isinstance(family, dict):
            failures.append("history business baseline contains non-object family")
            continue
        if not family.get("baseline_sources"):
            failures.append(f"history business family has no baseline_sources: {family.get('key')}")
    return failures


def verify_user_data_rebaseline_contract() -> list[str]:
    failures: list[str] = []
    for path in [
        USER_DATA_REBASELINE_SOURCE_MANIFEST,
        USER_DATA_REBASELINE_REPLAY_PREFLIGHT,
        USER_MODULE_DATA_BASELINE_CONTRACT,
    ]:
        if not path.exists():
            failures.append(f"user module must carry {path.relative_to(MODULE).as_posix()}")
    if failures:
        return failures

    source = json.loads(USER_DATA_REBASELINE_SOURCE_MANIFEST.read_text(encoding="utf-8"))
    preflight = json.loads(USER_DATA_REBASELINE_REPLAY_PREFLIGHT.read_text(encoding="utf-8"))
    contract = json.loads(USER_MODULE_DATA_BASELINE_CONTRACT.read_text(encoding="utf-8"))

    if source.get("status") != "PASS":
        failures.append("rebaseline source manifest must be PASS")
    policy = source.get("policy") if isinstance(source.get("policy"), dict) else {}
    if policy.get("attachment_policy") != "link_only_until_prod_attachment_ready":
        failures.append("rebaseline source manifest must keep link-only attachment policy")
    forbidden_inputs = set(policy.get("forbidden_inputs") or [])
    for required in ["obsolete_20260513_release_package", "manual_development_database_residue"]:
        if required not in forbidden_inputs:
            failures.append(f"rebaseline source manifest must forbid {required}")

    online_sources = source.get("online_sources") if isinstance(source.get("online_sources"), dict) else {}
    scbs55 = online_sources.get("scbs55") if isinstance(online_sources.get("scbs55"), dict) else {}
    scbsly = online_sources.get("scbsly_v2") if isinstance(online_sources.get("scbsly_v2"), dict) else {}
    if int(scbs55.get("surface_count") or 0) != 42:
        failures.append("SCBS55 source must keep 42 locked surfaces")
    if int(scbs55.get("total_row_count") or 0) < 140000:
        failures.append("SCBS55 source rows are below locked baseline")
    if int(scbsly.get("surface_count") or 0) != 32:
        failures.append("SCBSLY_V2 source must keep 32 locked surfaces")
    if int(scbsly.get("total_row_count") or 0) < 76000:
        failures.append("SCBSLY_V2 source rows are below locked baseline")

    structured_sources = source.get("structured_db_sources")
    structured_sources = structured_sources if isinstance(structured_sources, dict) else {}
    legacy_counts = structured_sources.get("legacy_counts") if isinstance(structured_sources.get("legacy_counts"), list) else []
    if len(legacy_counts) < 9:
        failures.append("rebaseline source manifest must include core legacy MSSQL counts")

    if preflight.get("status") != "PASS":
        failures.append("rebaseline replay asset preflight must be PASS")
    checks = preflight.get("checks") if isinstance(preflight.get("checks"), dict) else {}
    history_payloads = checks.get("history_payloads") if isinstance(checks.get("history_payloads"), dict) else {}
    if int(history_payloads.get("present") or 0) != 52 or int(history_payloads.get("required") or 0) != 52:
        failures.append("rebaseline replay preflight must lock history payloads at 52/52")
    core_assets = checks.get("core_replay_assets") if isinstance(checks.get("core_replay_assets"), list) else []
    if len(core_assets) != 7 or any(not item.get("exists") for item in core_assets if isinstance(item, dict)):
        failures.append("rebaseline replay preflight must lock core replay assets at 7/7")
    for key, expected in [("scbs55", 42), ("scbsly_v2", 32)]:
        link_check = checks.get(f"stable_online_dump_links_{key}")
        link_check = link_check if isinstance(link_check, dict) else {}
        if int(link_check.get("entries") or 0) != expected:
            failures.append(f"rebaseline replay preflight must lock {key} stable links at {expected}/{expected}")
        if link_check.get("broken_links"):
            failures.append(f"rebaseline replay preflight must not contain broken {key} links")

    if contract.get("version") != "user_module_data_baseline_contract.v1":
        failures.append("user module data baseline contract version mismatch")
    if contract.get("status") != "READY_FOR_USER_MODULE_PACKAGING":
        failures.append("user module data baseline contract must be ready for packaging")
    boundary = contract.get("module_boundary") if isinstance(contract.get("module_boundary"), dict) else {}
    if boundary.get("target_module") != "smart_construction_custom":
        failures.append("user module data baseline contract must target smart_construction_custom")
    attachment_policy = contract.get("attachment_policy") if isinstance(contract.get("attachment_policy"), dict) else {}
    if attachment_policy.get("mode") != "link_only":
        failures.append("user module data baseline contract must keep attachment policy link_only")
    standard = contract.get("installation_standard") if isinstance(contract.get("installation_standard"), dict) else {}
    acceptance = standard.get("fresh_database_acceptance") or []
    for required in [
        "source manifest status PASS",
        "replay asset preflight PASS",
        "SCBS55 online rows linked 42/42",
        "SCBSLY_V2 online rows linked 32/32",
        "history payloads present 52/52",
        "core replay assets present 7/7",
        "attachments remain link-only until production attachment source is prepared",
    ]:
        if required not in acceptance:
            failures.append(f"user module data baseline contract missing acceptance: {required}")
    return failures


def verify_xml_boundary() -> list[str]:
    failures: list[str] = []
    if not USER_DATA_BASELINE_XML.exists():
        failures.append("user data baseline XML must exist as an explicit P2 data carrier")
    else:
        source = USER_DATA_BASELINE_XML.read_text(encoding="utf-8")
        if 'noupdate="1"' in source or "noupdate='1'" in source:
            failures.append("user data baseline XML must be upgrade-replayable; noupdate=1 is forbidden")
        if _xml_function_names(USER_DATA_BASELINE_XML) != ["apply_user_data_baseline"]:
            failures.append("user data baseline XML may only call apply_user_data_baseline")

    if _xml_function_names(USER_PREFERENCES_XML) != ["apply_user_form_preferences"]:
        failures.append("user preference XML may only call apply_user_form_preferences")
    if not LEGACY_USER_MASTER_XML.exists():
        failures.append("user module must carry the real legacy user master payload")
    else:
        root = ET.parse(LEGACY_USER_MASTER_XML).getroot()
        user_records = [
            node
            for node in root.iter("record")
            if str(node.attrib.get("model") or "").strip() == "res.users"
        ]
        if len(user_records) < 100:
            failures.append(f"legacy user master payload is too small: {len(user_records)} < 100")
    return failures


def verify_hook_boundary() -> list[str]:
    failures: list[str] = []
    tree = _parse_python(HOOKS)
    post_init = _function_by_name(tree, "post_init_hook")
    calls = _call_names(post_init)
    if "apply_user_data_baseline" not in calls:
        failures.append("post_init_hook must call apply_user_data_baseline explicitly")
    if "apply_user_preferences" not in calls:
        failures.append("post_init_hook must call apply_user_preferences explicitly")
    if "apply_user_data_baseline" in calls and "apply_user_preferences" in calls:
        if calls.index("apply_user_data_baseline") > calls.index("apply_user_preferences"):
            failures.append("post_init_hook must apply user data baseline before user preferences")

    apply_user_data = _function_by_name(tree, "apply_user_data_baseline")
    if apply_user_data is None:
        failures.append("hooks.py must expose apply_user_data_baseline")
    else:
        if "apply_user_data_baseline" not in _call_names(apply_user_data):
            failures.append("hooks.apply_user_data_baseline must delegate to sc.user.preference.initialization")
    apply_user_preferences = _function_by_name(tree, "apply_user_preferences")
    preference_calls = _call_names(apply_user_preferences)
    for required in (
        "apply_user_menu_preferences",
        "apply_user_form_preferences",
        "apply_customer_lowcode_contract_assets",
        "backfill_lowcode_contract_source_status",
    ):
        if required not in preference_calls:
            failures.append(f"hooks.apply_user_preferences missing {required}")
    if all(name in preference_calls for name in ("apply_user_form_preferences", "apply_customer_lowcode_contract_assets")):
        if preference_calls.index("apply_customer_lowcode_contract_assets") < preference_calls.index("apply_user_form_preferences"):
            failures.append("hooks.apply_user_preferences must replay accepted low-code assets after default form preferences")
    return failures


def verify_partner_location_boundary() -> list[str]:
    failures: list[str] = []
    tree = _parse_python(PARTNER_LOCATION)
    apply_data = _function_by_name(tree, "apply_user_data_baseline")
    apply_location = _function_by_name(tree, "apply_partner_location_data_baseline")
    if apply_data is None:
        failures.append("partner location data must publish apply_user_data_baseline")
    elif "apply_partner_location_data_baseline" not in _call_names(apply_data):
        failures.append("apply_user_data_baseline must call apply_partner_location_data_baseline")

    if apply_location is None:
        failures.append("partner location data must publish apply_partner_location_data_baseline")
    else:
        calls = set(_call_names(apply_location))
        for required in ["_ensure_partner_city_data", "_backfill_partner_sc_city_ids"]:
            if required not in calls:
                failures.append(f"apply_partner_location_data_baseline must call {required}")

    apply_partner_form = _function_by_name(tree, "apply_partner_form_preferences")
    if apply_partner_form is not None:
        forbidden = {"_ensure_partner_city_data", "_backfill_partner_sc_city_ids"}
        found = sorted(forbidden.intersection(_call_names(apply_partner_form)))
        if found:
            failures.append(
                "apply_partner_form_preferences must not mutate user data baseline; "
                f"found calls {found}"
            )
    return failures


def verify_user_data_baseline_boundary() -> list[str]:
    failures: list[str] = []
    if not USER_DATA_BASELINE_PY.exists():
        return ["user module must provide models/user_data_baseline.py"]

    tree = _parse_python(USER_DATA_BASELINE_PY)
    required_functions = {
        "apply_user_data_baseline",
        "apply_legacy_user_master_data_baseline",
        "apply_partner_business_data_baseline",
        "apply_history_business_data_baseline_manifest",
        "apply_user_data_rebaseline_contract",
        "_load_user_data_baseline_json",
        "_find_existing_legacy_user",
        "_ensure_user_baseline_xmlid",
    }
    missing = sorted(name for name in required_functions if _function_by_name(tree, name) is None)
    if missing:
        failures.append(f"user data baseline missing required functions: {missing}")

    apply_data = _function_by_name(tree, "apply_user_data_baseline")
    calls = set(_call_names(apply_data))
    for required in [
        "apply_legacy_user_master_data_baseline",
        "apply_partner_business_data_baseline",
        "apply_history_business_data_baseline_manifest",
        "apply_user_data_rebaseline_contract",
    ]:
        if required not in calls:
            failures.append(f"apply_user_data_baseline must call {required}")

    source = USER_DATA_BASELINE_PY.read_text(encoding="utf-8")
    required_snippets = [
        '("smart_construction_custom", "migration_assets")',
        '("login", "=", login)',
        "no_reset_password=True",
        '"noupdate": True',
        "demote_no_fact=False",
        "locked_user_visible_business_surface",
        "not_complete_if_only_legacy_asset_catalog",
        "USER_DATA_REBASELINE_SOURCE_MANIFEST",
        "history_payloads_must_be_52_of_52",
        "contract_attachment_policy_must_be_link_only",
    ]
    for snippet in required_snippets:
        if snippet not in source:
            failures.append(f"user data baseline must keep idempotent/non-destructive rule: {snippet}")
    if ".create(vals)" not in source or ".write(vals)" not in source:
        failures.append("legacy user baseline loader must update existing users and create only missing users")
    init_source = MODELS_INIT.read_text(encoding="utf-8")
    if "user_data_baseline" not in init_source:
        failures.append("models/__init__.py must import user_data_baseline")
    return failures


def verify_industry_modules_do_not_carry_user_data() -> list[str]:
    failures: list[str] = []
    forbidden_names = {"user_master_v1.xml"}
    forbidden_text = ("legacy_user_sc_",)
    for module_path in INDUSTRY_MODULES:
        if not module_path.exists():
            continue
        for path in module_path.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT).as_posix()
            if path.name in forbidden_names:
                failures.append(f"P1 industry module must not carry P2 real-user payload file: {rel}")
                continue
            if path.suffix.lower() not in {".xml", ".csv", ".json", ".py", ".md"}:
                continue
            try:
                source = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if any(token in source for token in forbidden_text):
                failures.append(f"P1 industry module must not carry P2 real-user payload token in {rel}")
    return failures


def main() -> int:
    failures = (
        verify_manifest_boundary()
        + verify_lowcode_customer_config_baseline_manifest()
        + verify_history_business_data_baseline_manifest()
        + verify_user_data_rebaseline_contract()
        + verify_xml_boundary()
        + verify_hook_boundary()
        + verify_partner_location_boundary()
        + verify_user_data_baseline_boundary()
        + verify_industry_modules_do_not_carry_user_data()
    )
    if failures:
        print("[user_module_product_boundary_guard] FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("[user_module_product_boundary_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
