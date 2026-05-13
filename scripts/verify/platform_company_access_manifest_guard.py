# -*- coding: utf-8 -*-
"""Guard platform company-access ownership in manifests and XML surfaces."""

from __future__ import annotations

import ast
import csv
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]

PLATFORM_DATA_FILES = {
    "data/sc_subscription_default.xml",
    "views/platform_company_access_views.xml",
}
FORBIDDEN_CONSTRUCTION_FILES = {
    "data/sc_subscription_default.xml",
    "views/support/subscription_views.xml",
}
REQUIRED_PLATFORM_XMLIDS = {
    "menu_smart_core_platform_root",
    "menu_smart_core_company_access_root",
    "menu_sc_subscription_plan",
    "menu_sc_subscription",
    "menu_sc_entitlement",
    "menu_sc_usage_counter",
    "menu_sc_ops_job",
    "action_sc_subscription_plan",
    "action_sc_subscription",
    "action_sc_entitlement",
    "action_sc_usage_counter",
    "action_sc_ops_job",
}
LEGACY_PLATFORM_UI_XMLIDS = {
    "menu_smart_core_platform_root",
    "menu_smart_core_company_access_root",
    "menu_sc_subscription_plan",
    "menu_sc_subscription",
    "menu_sc_entitlement",
    "menu_sc_usage_counter",
    "menu_sc_ops_job",
    "view_sc_subscription_plan_tree",
    "view_sc_subscription_plan_form",
    "view_sc_subscription_tree",
    "view_sc_subscription_form",
    "view_sc_entitlement_tree",
    "view_sc_entitlement_form",
    "view_sc_usage_counter_tree",
    "view_sc_usage_counter_form",
    "view_sc_ops_job_tree",
    "view_sc_ops_job_form",
    "action_sc_subscription_plan",
    "action_sc_subscription",
    "action_sc_entitlement",
    "action_sc_usage_counter",
    "action_sc_ops_job",
}
PLATFORM_MODELS = {
    "sc.subscription.plan",
    "sc.subscription",
    "sc.entitlement",
    "sc.usage.counter",
    "sc.ops.job",
}
PLATFORM_MODEL_XML_REFS = {
    "smart_core.model_sc_subscription_plan",
    "smart_core.model_sc_subscription",
    "smart_core.model_sc_entitlement",
    "smart_core.model_sc_usage_counter",
    "smart_core.model_sc_ops_job",
}
LEGACY_PLATFORM_BRIDGE_FILE = "security/sc_capability_groups.xml"
PLATFORM_ADMIN_HELPER = "addons/smart_construction_core/services/platform_admin.py"
FORBIDDEN_LEGACY_ADMIN_CHECKS = {
    "addons/smart_construction_core/controllers/scene_controller.py",
    "addons/smart_construction_core/controllers/scene_template_controller.py",
    "addons/smart_construction_core/controllers/ops_controller.py",
    "addons/smart_construction_core/controllers/pack_controller.py",
    "addons/smart_construction_core/controllers/capability_catalog_controller.py",
    "addons/smart_construction_core/models/support/history_todo.py",
    "addons/smart_construction_core/models/support/sc_workflow.py",
    "addons/smart_construction_custom/models/security_policy.py",
}


def _manifest_data(module: str) -> list[str]:
    path = ROOT / "addons" / module / "__manifest__.py"
    payload = ast.literal_eval(path.read_text(encoding="utf-8"))
    return list(payload.get("data") or [])


def _xml_ids(path: Path) -> set[str]:
    root = ET.parse(path).getroot()
    ids: set[str] = set()
    for node in root.iter():
        xmlid = node.attrib.get("id")
        if xmlid:
            ids.add(xmlid)
    return ids


def _xml_model_refs(path: Path) -> set[str]:
    root = ET.parse(path).getroot()
    refs: set[str] = set()
    for node in root.iter():
        if node.tag == "field" and node.attrib.get("name") == "model" and node.text:
            refs.add(node.text.strip())
        if node.attrib.get("model") == "ir.actions.act_window":
            for field in node:
                if field.tag == "field" and field.attrib.get("name") == "res_model" and field.text:
                    refs.add(field.text.strip())
    return refs


def _csv_model_refs(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return {row.get("model_id:id", "").strip() for row in csv.DictReader(fh) if row.get("model_id:id")}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


smart_core_data = set(_manifest_data("smart_core"))
construction_data = set(_manifest_data("smart_construction_core"))

missing = sorted(PLATFORM_DATA_FILES - smart_core_data)
assert_true(not missing, f"smart_core manifest missing platform files: {missing}")

forbidden = sorted(FORBIDDEN_CONSTRUCTION_FILES & construction_data)
assert_true(not forbidden, f"construction manifest still owns platform files: {forbidden}")

construction_security = ROOT / "addons" / "smart_construction_core" / LEGACY_PLATFORM_BRIDGE_FILE
construction_security_text = construction_security.read_text(encoding="utf-8")
assert_true(
    "ref('smart_core.group_smart_core_admin')" in construction_security_text,
    "legacy construction platform admin group must imply smart_core.group_smart_core_admin",
)

platform_view = ROOT / "addons" / "smart_core" / "views" / "platform_company_access_views.xml"
xmlids = _xml_ids(platform_view)
missing_xmlids = sorted(REQUIRED_PLATFORM_XMLIDS - xmlids)
assert_true(not missing_xmlids, f"platform view missing XML ids: {missing_xmlids}")

platform_model_refs = _xml_model_refs(platform_view)
missing_model_refs = sorted(PLATFORM_MODELS - platform_model_refs)
assert_true(not missing_model_refs, f"platform view missing model surfaces: {missing_model_refs}")

legacy_view = ROOT / "addons" / "smart_construction_core" / "views" / "support" / "subscription_views.xml"
if legacy_view.exists():
    legacy_refs = PLATFORM_MODELS & _xml_model_refs(legacy_view)
    assert_true(
        not legacy_refs,
        f"construction subscription view still defines platform model surfaces: {sorted(legacy_refs)}",
    )

legacy_seed = ROOT / "addons" / "smart_construction_core" / "data" / "sc_subscription_default.xml"
assert_true(not legacy_seed.exists(), "construction module still carries platform subscription seed file")

construction_acl = ROOT / "addons" / "smart_construction_core" / "security" / "ir.model.access.csv"
legacy_acl_refs = PLATFORM_MODEL_XML_REFS & _csv_model_refs(construction_acl)
assert_true(not legacy_acl_refs, f"construction ACL still owns platform model refs: {sorted(legacy_acl_refs)}")

platform_seed = (ROOT / "addons" / "smart_core" / "data" / "sc_subscription_default.xml").read_text(encoding="utf-8")
assert_true(
    "ensure_platform_access_ownership" in platform_seed,
    "smart_core platform seed must clean legacy construction ACL ownership",
)

subscription_model_text = (ROOT / "addons" / "smart_core" / "models" / "subscription.py").read_text(encoding="utf-8")
missing_cleanup_xmlids = sorted(xmlid for xmlid in LEGACY_PLATFORM_UI_XMLIDS if xmlid not in subscription_model_text)
assert_true(
    not missing_cleanup_xmlids,
    f"smart_core ownership cleanup missing legacy UI XML ids: {missing_cleanup_xmlids}",
)

helper_text = (ROOT / PLATFORM_ADMIN_HELPER).read_text(encoding="utf-8")
assert_true(
    'PLATFORM_ADMIN_GROUP = "smart_core.group_smart_core_admin"' in helper_text,
    "platform admin helper must use smart_core.group_smart_core_admin as canonical platform authority",
)

for rel_path in sorted(FORBIDDEN_LEGACY_ADMIN_CHECKS):
    text = (ROOT / rel_path).read_text(encoding="utf-8")
    assert_true(
        'has_group("smart_construction_core.group_sc_cap_config_admin")' not in text
        and "has_group('smart_construction_core.group_sc_cap_config_admin')" not in text,
        f"{rel_path}: must use platform_admin helper instead of direct legacy platform group check",
    )
    assert_true("_has_admin" not in text, f"{rel_path}: must use named platform_admin helper, not _has_admin")
    assert_true("CONFIG_GROUP" not in text, f"{rel_path}: must use named platform_admin helper, not CONFIG_GROUP")

print(
    "PLATFORM_COMPANY_ACCESS_MANIFEST_GUARD=PASS "
    f"platform_files={len(PLATFORM_DATA_FILES)} xmlids={len(REQUIRED_PLATFORM_XMLIDS)} "
    f"models={len(PLATFORM_MODELS)}"
)
