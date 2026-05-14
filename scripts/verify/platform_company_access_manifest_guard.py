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
    "menu_sc_login_route",
    "menu_sc_usage_counter",
    "menu_sc_ops_job",
    "menu_smart_core_release_root",
    "menu_sc_product_policy",
    "menu_sc_scene_snapshot",
    "menu_sc_edition_release_snapshot",
    "menu_sc_release_action",
    "action_sc_subscription_plan",
    "action_sc_subscription",
    "action_sc_entitlement",
    "action_sc_login_route",
    "action_sc_usage_counter",
    "action_sc_ops_job",
    "action_sc_product_policy",
    "action_sc_scene_snapshot",
    "action_sc_edition_release_snapshot",
    "action_sc_release_action",
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
    "sc.login.route",
    "sc.usage.counter",
    "sc.ops.job",
    "sc.product.policy",
    "sc.scene.snapshot",
    "sc.edition.release.snapshot",
    "sc.release.action",
}
PLATFORM_MODEL_XML_REFS = {
    "smart_core.model_sc_subscription_plan",
    "smart_core.model_sc_subscription",
    "smart_core.model_sc_entitlement",
    "smart_core.model_sc_login_route",
    "smart_core.model_sc_usage_counter",
    "smart_core.model_sc_ops_job",
    "smart_core.model_sc_product_policy",
    "smart_core.model_sc_scene_snapshot",
    "smart_core.model_sc_edition_release_snapshot",
    "smart_core.model_sc_release_action",
}
LEGACY_PLATFORM_BRIDGE_FILE = "security/sc_capability_groups.xml"
PLATFORM_ADMIN_HELPER = "addons/smart_core/security/platform_admin.py"
LEGACY_PLATFORM_ADMIN_HELPER = "addons/smart_construction_core/services/platform_admin.py"
PLATFORM_OPS_CONTROLLER = "addons/smart_core/controllers/platform_ops_controller.py"
CONSTRUCTION_OPS_CONTROLLER = "addons/smart_construction_core/controllers/ops_controller.py"
RELEASE_APPROVAL_POLICY_SERVICE = "addons/smart_core/delivery/release_approval_policy_service.py"
BOUNDARY_ROUTE_DOCS = {
    "docs/audit/boundary/http_route_inventory.md",
    "docs/audit/boundary/http_route_classification.md",
    "docs/audit/boundary/duplicate_controller_surface.md",
    "docs/audit/boundary/platform_entry_occupation.md",
    "docs/audit/boundary/boundary_object_master_table.md",
    "docs/audit/boundary/runtime_priority_matrix.md",
}
MIGRATED_PLATFORM_OPS_ROUTES = {
    "/api/ops/tenants",
    "/api/ops/subscription/set",
    "/api/ops/job/status",
}
SCENE_ORCHESTRATION_VIEW = "addons/smart_construction_core/views/support/scene_orchestration_views.xml"
SCENE_GOVERNANCE_VIEW = "addons/smart_construction_scene/views/scene_governance_views.xml"
CANONICAL_PLATFORM_ADMIN_GROUP = "smart_core.group_smart_core_admin"
LEGACY_PLATFORM_ADMIN_GROUP = "smart_construction_core.group_sc_cap_config_admin"
SCENE_ORCHESTRATION_ADMIN_ACLS = {
    "access_sc_capability_admin",
    "access_sc_capability_group_admin",
    "access_sc_scene_admin",
    "access_sc_scene_tile_admin",
    "access_sc_scene_version_admin",
    "access_sc_scene_validation_admin",
    "access_sc_scene_audit_admin",
    "access_sc_capability_audit_admin",
    "access_sc_pack_registry_admin",
    "access_sc_pack_installation_admin",
}
SCENE_GOVERNANCE_ADMIN_ACLS = {
    "access_sc_scene_governance_log_admin",
    "access_sc_scene_company_channel_admin",
    "access_sc_scene_governance_wizard_admin",
    "access_sc_scene_package_installation_admin",
}
CONSTRUCTION_PLATFORM_ADMIN_ACLS = {
    "access_sc_workflow_def_admin",
    "access_sc_workflow_node_admin",
    "access_sc_workflow_instance_admin",
    "access_sc_workflow_workitem_admin",
    "access_sc_workflow_log_admin",
}
CONSTRUCTION_PLATFORM_SURFACE_FILES = {
    "addons/smart_construction_core/views/menu_root.xml",
    "addons/smart_construction_core/views/menu_centers.xml",
    "addons/smart_construction_core/views/menu.xml",
    "addons/smart_construction_core/views/core/workflow_views.xml",
    "addons/smart_construction_core/security/action_groups_patch.xml",
    "addons/smart_construction_core/views/res_groups_menu_views.xml",
    "addons/smart_construction_core/views/support/runtime_user_management_views.xml",
}
CONSTRUCTION_PLATFORM_SURFACE_XMLIDS = {
    "menu_sc_project_manage",
    "menu_sc_config_center",
    "menu_sc_workflow_root",
    "menu_sc_workflow_def",
    "menu_sc_workflow_instance",
    "menu_sc_workflow_workitem",
    "menu_sc_workflow_log",
    "action_sc_project_manage",
    "action_sc_workflow_def",
    "action_sc_workflow_instance",
    "action_sc_workflow_workitem",
    "action_sc_workflow_log",
    "base.menu_action_res_groups",
    "base.action_res_groups",
    "action_sc_runtime_user_management",
    "menu_sc_runtime_user_management",
}
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
FORBIDDEN_DIRECT_SYSTEM_ADMIN_CHECKS = {
    "addons/smart_core/app_config_engine/services/dispatchers/nav_dispatcher.py",
    "addons/smart_core/controllers/intent_dispatcher.py",
    "addons/smart_core/controllers/platform_menu_api.py",
    "addons/smart_core/core/base_handler.py",
    "addons/smart_core/core/request_diagnostics.py",
    "addons/smart_core/handlers/usage_track.py",
    "addons/smart_construction_core/handlers/app_catalog.py",
    "addons/smart_construction_core/handlers/app_open.py",
    "addons/smart_construction_core/handlers/my_work_complete.py",
    "addons/smart_construction_core/handlers/payment_request_approval.py",
    "addons/smart_construction_core/handlers/payment_request_execute.py",
    "addons/smart_construction_core/handlers/risk_action_execute.py",
    "addons/smart_construction_core/models/support/scene_orchestration.py",
    "addons/smart_construction_portal/services/portal_contract_service.py",
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


def _xml_group_surfaces(path: Path, xmlids: set[str]) -> dict[str, str]:
    root = ET.parse(path).getroot()
    surfaces: dict[str, str] = {}
    for node in root.iter():
        xmlid = node.attrib.get("id")
        if xmlid not in xmlids:
            continue
        groups = node.attrib.get("groups")
        if groups:
            surfaces[xmlid] = groups
            continue
        for field in node:
            if field.tag == "field" and field.attrib.get("name") == "groups_id":
                surfaces[xmlid] = field.attrib.get("eval") or (field.text or "")
                break
    return surfaces


def _csv_model_refs(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return {row.get("model_id:id", "").strip() for row in csv.DictReader(fh) if row.get("model_id:id")}


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


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
legacy_helper_text = (ROOT / LEGACY_PLATFORM_ADMIN_HELPER).read_text(encoding="utf-8")
assert_true(
    "odoo.addons.smart_core.security.platform_admin" in legacy_helper_text,
    "legacy construction platform_admin helper must delegate to smart_core.security.platform_admin",
)
platform_ops_text = (ROOT / PLATFORM_OPS_CONTROLLER).read_text(encoding="utf-8")
construction_ops_text = (ROOT / CONSTRUCTION_OPS_CONTROLLER).read_text(encoding="utf-8")
for route in sorted(MIGRATED_PLATFORM_OPS_ROUTES):
    assert_true(route in platform_ops_text, f"{PLATFORM_OPS_CONTROLLER}: missing platform route {route}")
    assert_true(route not in construction_ops_text, f"{CONSTRUCTION_OPS_CONTROLLER}: must not own platform route {route}")
for rel_path in sorted(BOUNDARY_ROUTE_DOCS):
    text = (ROOT / rel_path).read_text(encoding="utf-8")
    for route in sorted(MIGRATED_PLATFORM_OPS_ROUTES):
        stale_fragment = f"ops_controller.py` | `{route}"
        assert_true(
            stale_fragment not in text,
            f"{rel_path}: migrated platform ops route still documented under construction ops controller: {route}",
        )
        if route in text:
            assert_true(
                "platform_ops_controller.py" in text,
                f"{rel_path}: migrated platform ops route must document smart_core platform_ops_controller ownership: {route}",
            )

system_init_builder_text = (ROOT / "addons/smart_core/core/system_init_payload_builder.py").read_text(encoding="utf-8")
construction_extension_text = (ROOT / "addons/smart_construction_core/core_extension.py").read_text(encoding="utf-8")
formal_entry_metadata_text = (ROOT / "addons/smart_construction_core/models/support/formal_entry_metadata_extensions.py").read_text(encoding="utf-8")
assert_true(
    "attach_platform_company_access_facts" in system_init_builder_text,
    "smart_core system_init payload builder must attach platform company access facts",
)
assert_true(
    'env.get("sc.entitlement")' not in construction_extension_text
    and 'env.get("sc.usage.counter")' not in construction_extension_text,
    "construction extension must not contribute platform entitlement/usage facts",
)
assert_true(
    '"sc.ops.job"' not in formal_entry_metadata_text,
    "construction formal entry metadata extensions must not extend platform sc.ops.job",
)
scene_orchestration_view_text = (ROOT / SCENE_ORCHESTRATION_VIEW).read_text(encoding="utf-8")
assert_true(
    LEGACY_PLATFORM_ADMIN_GROUP not in scene_orchestration_view_text,
    f"{SCENE_ORCHESTRATION_VIEW}: scene/capability admin UI must use {CANONICAL_PLATFORM_ADMIN_GROUP}",
)
assert_true(
    CANONICAL_PLATFORM_ADMIN_GROUP in scene_orchestration_view_text,
    f"{SCENE_ORCHESTRATION_VIEW}: missing canonical platform admin group",
)
construction_acl_rows = _csv_rows(construction_acl)
scene_acl_group_gaps = [
    {
        "id": row.get("id"),
        "group_id:id": row.get("group_id:id"),
    }
    for row in construction_acl_rows
    if row.get("id") in SCENE_ORCHESTRATION_ADMIN_ACLS
    and row.get("group_id:id") != CANONICAL_PLATFORM_ADMIN_GROUP
]
assert_true(
    not scene_acl_group_gaps,
    f"scene/capability admin ACLs must use {CANONICAL_PLATFORM_ADMIN_GROUP}: {scene_acl_group_gaps}",
)
scene_governance_view_text = (ROOT / SCENE_GOVERNANCE_VIEW).read_text(encoding="utf-8")
assert_true(
    LEGACY_PLATFORM_ADMIN_GROUP not in scene_governance_view_text,
    f"{SCENE_GOVERNANCE_VIEW}: scene governance UI must use {CANONICAL_PLATFORM_ADMIN_GROUP}",
)
assert_true(
    CANONICAL_PLATFORM_ADMIN_GROUP in scene_governance_view_text,
    f"{SCENE_GOVERNANCE_VIEW}: missing canonical platform admin group",
)
scene_governance_acl_rows = _csv_rows(ROOT / "addons/smart_construction_scene/security/ir.model.access.csv")
scene_governance_acl_group_gaps = [
    {
        "id": row.get("id"),
        "group_id:id": row.get("group_id:id"),
    }
    for row in scene_governance_acl_rows
    if row.get("id") in SCENE_GOVERNANCE_ADMIN_ACLS
    and row.get("group_id:id") != CANONICAL_PLATFORM_ADMIN_GROUP
]
assert_true(
    not scene_governance_acl_group_gaps,
    f"scene governance admin ACLs must use {CANONICAL_PLATFORM_ADMIN_GROUP}: {scene_governance_acl_group_gaps}",
)
platform_acl_group_gaps = [
    {
        "id": row.get("id"),
        "group_id:id": row.get("group_id:id"),
    }
    for row in construction_acl_rows
    if row.get("id") in CONSTRUCTION_PLATFORM_ADMIN_ACLS
    and row.get("group_id:id") != CANONICAL_PLATFORM_ADMIN_GROUP
]
assert_true(
    not platform_acl_group_gaps,
    f"workflow platform ACLs must use {CANONICAL_PLATFORM_ADMIN_GROUP}: {platform_acl_group_gaps}",
)
for rel_path in sorted(CONSTRUCTION_PLATFORM_SURFACE_FILES):
    surfaces = _xml_group_surfaces(ROOT / rel_path, CONSTRUCTION_PLATFORM_SURFACE_XMLIDS)
    for xmlid, group_expr in sorted(surfaces.items()):
        assert_true(
            CANONICAL_PLATFORM_ADMIN_GROUP in group_expr,
            f"{rel_path}: platform governance surface {xmlid} must use {CANONICAL_PLATFORM_ADMIN_GROUP}",
        )
        assert_true(
            LEGACY_PLATFORM_ADMIN_GROUP not in group_expr,
            f"{rel_path}: platform governance surface {xmlid} must not use {LEGACY_PLATFORM_ADMIN_GROUP}",
        )
runtime_user_management_text = (
    ROOT / "addons/smart_construction_core/views/support/runtime_user_management_views.xml"
).read_text(encoding="utf-8")
assert_true(
    "ref('smart_core.group_smart_core_admin')" in runtime_user_management_text,
    "runtime user management must explicitly filter canonical platform admins",
)
for rel_path in (
    "addons/smart_construction_core/controllers/pack_controller.py",
    "addons/smart_construction_core/models/support/scene_orchestration.py",
):
    text = (ROOT / rel_path).read_text(encoding="utf-8")
    assert_true(
        'env.get("sc.entitlement")' not in text and 'env.get("sc.usage.counter")' not in text,
        f"{rel_path}: must consume platform company access through smart_core.security.platform_company_access",
    )
custom_security_policy_text = (ROOT / "addons/smart_construction_custom/models/security_policy.py").read_text(encoding="utf-8")
assert_true(
    "platform_admin_group_xmlids" in custom_security_policy_text
    and '"smart_construction_core.group_sc_cap_config_admin"' not in custom_security_policy_text,
    "custom security policy must consume platform admin group xmlids from smart_core.security.platform_admin",
)
release_approval_policy_text = (ROOT / RELEASE_APPROVAL_POLICY_SERVICE).read_text(encoding="utf-8")
assert_true(
    "smart_core.security.platform_admin" in release_approval_policy_text
    and "user_is_platform_admin" in release_approval_policy_text,
    f"{RELEASE_APPROVAL_POLICY_SERVICE}: release approval role policy must consume canonical platform admin helper",
)
assert_true(
    'has_group("smart_core.group_smart_core_admin")' not in release_approval_policy_text
    and "has_group('smart_core.group_smart_core_admin')" not in release_approval_policy_text
    and 'has_group("base.group_system")' not in release_approval_policy_text
    and "has_group('base.group_system')" not in release_approval_policy_text,
    f"{RELEASE_APPROVAL_POLICY_SERVICE}: must not hardcode platform admin group checks",
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

for rel_path in sorted(FORBIDDEN_DIRECT_SYSTEM_ADMIN_CHECKS):
    text = (ROOT / rel_path).read_text(encoding="utf-8")
    assert_true(
        "user_is_platform_admin" in text,
        f"{rel_path}: must consume smart_core.security.platform_admin helper",
    )
    assert_true(
        'has_group("base.group_system")' not in text and "has_group('base.group_system')" not in text,
        f"{rel_path}: must not hardcode base.group_system as platform-admin authority",
    )

print(
    "PLATFORM_COMPANY_ACCESS_MANIFEST_GUARD=PASS "
    f"platform_files={len(PLATFORM_DATA_FILES)} xmlids={len(REQUIRED_PLATFORM_XMLIDS)} "
    f"models={len(PLATFORM_MODELS)}"
)
