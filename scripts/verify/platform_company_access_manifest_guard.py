# -*- coding: utf-8 -*-
"""Guard platform company-access ownership in manifests and XML surfaces."""

from __future__ import annotations

import ast
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
PLATFORM_MODELS = {
    "sc.subscription.plan",
    "sc.subscription",
    "sc.entitlement",
    "sc.usage.counter",
    "sc.ops.job",
}
LEGACY_PLATFORM_BRIDGE_FILE = "security/sc_capability_groups.xml"


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

print(
    "PLATFORM_COMPANY_ACCESS_MANIFEST_GUARD=PASS "
    f"platform_files={len(PLATFORM_DATA_FILES)} xmlids={len(REQUIRED_PLATFORM_XMLIDS)} "
    f"models={len(PLATFORM_MODELS)}"
)
