# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


SCENE_DIR = Path(__file__).resolve().parents[1]


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


sys.modules.setdefault("odoo", types.ModuleType("odoo"))
sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))

scene_pkg = sys.modules.setdefault("odoo.addons.smart_construction_scene", types.ModuleType("odoo.addons.smart_construction_scene"))
scene_pkg.__path__ = [str(SCENE_DIR)]

scene_registry_mod = types.ModuleType("odoo.addons.smart_construction_scene.scene_registry")
scene_registry_mod.load_scene_configs = lambda env: []
scene_registry_mod.load_scene_configs_with_timings = lambda env: ([], {})
sys.modules["odoo.addons.smart_construction_scene.scene_registry"] = scene_registry_mod
scene_pkg.scene_registry = scene_registry_mod

enterprise_base_pkg = sys.modules.setdefault("odoo.addons.smart_enterprise_base", types.ModuleType("odoo.addons.smart_enterprise_base"))
enterprise_base_pkg.__path__ = [str(SCENE_DIR.parent / "smart_enterprise_base")]

target_core_extension = _load_module(
    "odoo.addons.smart_construction_scene.core_extension",
    SCENE_DIR / "core_extension.py",
)
scene_merge_resolver = _load_module(
    "odoo.addons.smart_core.core.scene_merge_resolver",
    SCENE_DIR.parent / "smart_core" / "core" / "scene_merge_resolver.py",
)
project_dashboard_scene_content = _load_module(
    "odoo.addons.smart_construction_scene.profiles.project_dashboard_scene_content",
    SCENE_DIR / "profiles" / "project_dashboard_scene_content.py",
)
enterprise_bootstrap_provider = _load_module(
    "odoo.addons.smart_construction_scene.providers.enterprise_bootstrap_provider",
    SCENE_DIR / "providers" / "enterprise_bootstrap_provider.py",
)
contract_center_provider = _load_module(
    "odoo.addons.smart_construction_scene.providers.contract_center_provider",
    SCENE_DIR / "providers" / "contract_center_provider.py",
)
contracts_workspace_provider = _load_module(
    "odoo.addons.smart_construction_scene.providers.contracts_workspace_provider",
    SCENE_DIR / "providers" / "contracts_workspace_provider.py",
)
workflow_rollout_handoff = _load_module(
    "odoo.addons.smart_construction_scene.services.workflow_rollout_handoff",
    SCENE_DIR / "services" / "workflow_rollout_handoff.py",
)
approval_workbench_provider = _load_module(
    "odoo.addons.smart_construction_scene.providers.approval_workbench_provider",
    SCENE_DIR / "providers" / "approval_workbench_provider.py",
)
projects_list_provider = _load_module(
    "odoo.addons.smart_construction_scene.providers.projects_list_provider",
    SCENE_DIR / "providers" / "projects_list_provider.py",
)
finance_center_provider = _load_module(
    "odoo.addons.smart_construction_scene.providers.finance_center_provider",
    SCENE_DIR / "providers" / "finance_center_provider.py",
)
cost_project_budget_provider = _load_module(
    "odoo.addons.smart_construction_scene.providers.cost_project_budget_provider",
    SCENE_DIR / "providers" / "cost_project_budget_provider.py",
)
task_center_provider = _load_module(
    "odoo.addons.smart_construction_scene.providers.task_center_provider",
    SCENE_DIR / "providers" / "task_center_provider.py",
)
payment_entry_workbench_provider = _load_module(
    "odoo.addons.smart_construction_scene.providers.payment_entry_workbench_provider",
    SCENE_DIR / "providers" / "payment_entry_workbench_provider.py",
)
register_scene_providers = _load_module(
    "odoo.addons.smart_construction_scene.bootstrap.register_scene_providers",
    SCENE_DIR / "bootstrap" / "register_scene_providers.py",
)
enterprise_base_core_extension = _load_module(
    "odoo.addons.smart_enterprise_base.core_extension",
    SCENE_DIR.parent / "smart_enterprise_base" / "core_extension.py",
)
scene_registry_content = _load_module(
    "odoo.addons.smart_construction_scene.profiles.scene_registry_content",
    SCENE_DIR / "profiles" / "scene_registry_content.py",
)
target_capability = _load_module(
    "odoo.addons.smart_construction_scene.services.capability_scene_targets",
    SCENE_DIR / "services" / "capability_scene_targets.py",
)
scene_ready_bridge = _load_module(
    "odoo.addons.smart_core.core.scene_ready_semantic_orchestration_bridge",
    SCENE_DIR.parent / "smart_core" / "core" / "scene_ready_semantic_orchestration_bridge.py",
)


class _DummyRef:
    def __init__(self, record_id: int):
        self.id = record_id


class _DummyCursor:
    dbname = "test_sc_scene_semantic_supply"


class _DummyEnv:
    def __init__(self, refs=None):
        self.cr = _DummyCursor()
        self._refs = dict(refs or {})

    def ref(self, xmlid, raise_if_not_found=False):
        record_id = self._refs.get(str(xmlid or "").strip())
        if not record_id:
            return None
        return _DummyRef(int(record_id))

    @property
    def company(self):
        return None

    def __getitem__(self, model_name):
        return _DummyModel(model_name)


class _DummyModel:
    def __init__(self, model_name: str):
        self._model_name = model_name

    def sudo(self):
        return self

    def search_count(self, domain):
        _ = domain
        return 0


class _DummyUser:
    def __init__(self):
        self.id = 7
        self.company_id = None


class _DummyRegistry:
    def __init__(self):
        self.specs = []

    def register_spec(self, **kwargs):
        self.specs.append(dict(kwargs))


def _reset_caches():
    target_core_extension._DERIVED_NAV_SCENE_MAP_CACHE.clear()
    target_capability._SCENE_CONFIGS_CACHE.clear()
    target_capability._SCENE_MAP_CACHE.clear()
    target_capability._TARGET_SCENE_LOOKUP_CACHE.clear()


class TestActionOnlySceneSemanticSupply(unittest.TestCase):
    def test_project_dashboard_entry_capability_converges_to_project_management_scene(self):
        self.assertEqual(
            target_capability.CAPABILITY_ENTRY_SCENE_MAP["project.dashboard.enter"],
            "project.management",
        )
        self.assertEqual(
            target_capability.CAPABILITY_ENTRY_SCENE_MAP["project.dashboard.open"],
            "project.management",
        )

    def test_project_management_scene_declares_explicit_dashboard_action_target(self):
        rows = scene_registry_content.list_scene_entries()
        project_management = next((row for row in rows if row.get("code") == "project.management"), {})
        target = project_management.get("target") if isinstance(project_management.get("target"), dict) else {}

        self.assertEqual(target.get("menu_xmlid"), "smart_construction_core.menu_sc_project_management_scene")
        self.assertEqual(target.get("action_xmlid"), "smart_construction_core.action_project_dashboard")
        self.assertEqual(target.get("route"), "/s/project.management")

    def test_project_intake_scene_is_canonical_registry_owner_for_project_initiation_menu(self):
        rows = scene_registry_content.list_scene_entries()
        project_intake = next((row for row in rows if row.get("code") == "projects.intake"), {})
        project_initiation = next((row for row in rows if row.get("code") == "project.initiation"), {})

        self.assertEqual(((project_intake.get("target") or {}).get("route")), "/s/projects.intake")
        self.assertEqual(
            ((project_intake.get("target") or {}).get("menu_xmlid")),
            "smart_construction_core.menu_sc_project_initiation",
        )
        self.assertEqual(
            ((project_intake.get("target") or {}).get("action_xmlid")),
            "smart_construction_core.action_project_initiation",
        )
        self.assertEqual(((project_initiation.get("target") or {}).get("route")), "/s/project.initiation")
        self.assertFalse(bool(((project_initiation.get("target") or {}).get("menu_xmlid"))))
        self.assertFalse(bool(((project_initiation.get("target") or {}).get("action_xmlid"))))

    def test_project_initiation_entry_capability_converges_to_projects_intake_scene(self):
        self.assertEqual(
            target_capability.CAPABILITY_ENTRY_SCENE_MAP["project.initiation.enter"],
            "projects.intake",
        )

    def test_projects_list_scene_supplies_canonical_route_with_native_menu_action_parity(self):
        rows = scene_registry_content.list_scene_entries()
        projects_list = next((row for row in rows if row.get("code") == "projects.list"), {})

        self.assertEqual(((projects_list.get("target") or {}).get("route")), "/s/projects.list")
        self.assertEqual(
            ((projects_list.get("target") or {}).get("menu_xmlid")),
            "smart_construction_core.menu_sc_project_project",
        )
        self.assertEqual(
            ((projects_list.get("target") or {}).get("action_xmlid")),
            "smart_construction_core.action_sc_project_list",
        )

    def test_task_center_scene_supplies_canonical_route_without_menu_authority(self):
        rows = scene_registry_content.list_scene_entries()
        task_center = next((row for row in rows if row.get("code") == "task.center"), {})
        task_board = next((row for row in rows if row.get("code") == "task.board"), {})

        self.assertEqual(((task_center.get("target") or {}).get("route")), "/s/task.center")
        self.assertEqual(((task_center.get("target") or {}).get("action_xmlid")), "project.action_view_all_task")
        self.assertFalse(bool(((task_center.get("target") or {}).get("menu_xmlid"))))
        self.assertEqual(((task_board.get("target") or {}).get("route")), "/s/task.board")
        self.assertFalse(bool(((task_board.get("target") or {}).get("menu_xmlid"))))
        self.assertFalse(bool(((task_board.get("target") or {}).get("action_xmlid"))))
        self.assertEqual(
            target_capability.CAPABILITY_ENTRY_SCENE_MAP["project.task.list"],
            "task.center",
        )
        self.assertEqual(
            target_capability.CAPABILITY_ENTRY_SCENE_MAP["project.task.board"],
            "task.board",
        )

    def test_projects_ledger_scene_supplies_canonical_route_with_shared_native_parity(self):
        rows = scene_registry_content.list_scene_entries()
        projects_ledger = next((row for row in rows if row.get("code") == "projects.ledger"), {})

        self.assertEqual(((projects_ledger.get("target") or {}).get("route")), "/s/projects.ledger")
        self.assertEqual(
            ((projects_ledger.get("target") or {}).get("menu_xmlid")),
            "smart_construction_core.menu_sc_project_project",
        )
        self.assertEqual(
            ((projects_ledger.get("target") or {}).get("action_xmlid")),
            "smart_construction_core.action_sc_project_list",
        )

    def test_projects_detail_scene_keeps_route_and_menu_without_sharing_ledger_action_authority(self):
        rows = scene_registry_content.list_scene_entries()
        projects_detail = next((row for row in rows if row.get("code") == "projects.detail"), {})

        self.assertEqual(((projects_detail.get("target") or {}).get("route")), "/s/projects.detail")
        self.assertEqual(
            ((projects_detail.get("target") or {}).get("menu_xmlid")),
            "smart_construction_core.menu_sc_project_project",
        )
        self.assertIsNone(((projects_detail.get("target") or {}).get("action_xmlid")))

    def test_finance_center_scene_targets_align_with_root_menu_action(self):
        rows = scene_registry_content.list_scene_entries()
        finance_center = next((row for row in rows if row.get("code") == "finance.center"), {})
        finance_workspace = next((row for row in rows if row.get("code") == "finance.workspace"), {})

        self.assertEqual(((finance_center.get("target") or {}).get("route")), "/s/finance.center")
        self.assertEqual(((finance_center.get("target") or {}).get("menu_xmlid")), "smart_construction_core.menu_sc_finance_center")
        self.assertEqual(((finance_center.get("target") or {}).get("action_xmlid")), "smart_construction_core.action_sc_finance_dashboard")
        self.assertEqual(((finance_workspace.get("target") or {}).get("route")), "/s/finance.workspace")
        self.assertEqual(((finance_workspace.get("target") or {}).get("menu_xmlid")), "smart_construction_core.menu_sc_finance_center")
        self.assertIsNone(((finance_workspace.get("target") or {}).get("action_xmlid")))

    def test_payments_approval_scene_supplies_formal_approval_action_target(self):
        rows = scene_registry_content.list_scene_entries()
        approval = next((row for row in rows if row.get("code") == "payments.approval"), {})

        self.assertEqual(((approval.get("target") or {}).get("route")), "/s/payments.approval")
        self.assertEqual(
            ((approval.get("target") or {}).get("menu_xmlid")),
            "smart_construction_core.menu_sc_tier_review_my_payment_request",
        )
        self.assertEqual(
            ((approval.get("target") or {}).get("action_xmlid")),
            "smart_construction_core.action_sc_tier_review_my_payment_request",
        )

    def test_finance_payment_requests_scene_aligns_with_personal_entry_action(self):
        rows = scene_registry_content.list_scene_entries()
        payment_requests = next((row for row in rows if row.get("code") == "finance.payment_requests"), {})

        self.assertEqual(((payment_requests.get("target") or {}).get("route")), "/s/finance.payment_requests")
        self.assertEqual(((payment_requests.get("target") or {}).get("menu_xmlid")), "smart_construction_core.menu_payment_request")
        self.assertEqual(
            ((payment_requests.get("target") or {}).get("action_xmlid")),
            "smart_construction_core.action_payment_request_my",
        )

    def test_cost_project_budget_scene_prefers_direct_scene_route_over_native_action_target(self):
        rows = scene_registry_content.list_scene_entries()
        budget = next((row for row in rows if row.get("code") == "cost.project_budget"), {})

        self.assertEqual(((budget.get("target") or {}).get("route")), "/s/cost.project_budget")
        self.assertFalse(bool(((budget.get("target") or {}).get("menu_xmlid"))))
        self.assertFalse(bool(((budget.get("target") or {}).get("action_xmlid"))))

    def test_cost_project_budget_provider_supplies_guidance_payload(self):
        payload = cost_project_budget_provider.build(scene_key="cost.project_budget", runtime={"company_id": 9})

        self.assertEqual(payload.get("scene_key"), "cost.project_budget")
        self.assertEqual(((payload.get("guidance") or {}).get("title")), "预算管理")
        self.assertEqual(((payload.get("runtime") or {}).get("company_id")), 9)

    def test_finance_menu_scene_maps_keep_payment_list_and_approval_split(self):
        _reset_caches()
        target_core_extension.scene_registry.load_scene_configs = lambda env: list(scene_registry_content.list_scene_entries())
        maps = target_core_extension.smart_core_nav_scene_maps(_DummyEnv())

        self.assertEqual(
            maps["menu_scene_map"]["smart_construction_core.menu_payment_request"],
            "finance.payment_requests",
        )
        self.assertEqual(
            maps["menu_scene_map"]["smart_construction_core.menu_sc_tier_review_my_payment_request"],
            "payments.approval",
        )

    def test_contract_center_capability_converges_to_contract_family_root_authority(self):
        self.assertEqual(
            target_capability.CAPABILITY_ENTRY_SCENE_MAP["contract.center.open"],
            "contract.center",
        )

    def test_contract_center_provider_supplies_delivery_handoff_v1(self):
        payload = contract_center_provider.build(scene_key="contract.center", runtime={"company_id": 9})
        handoff = payload.get("delivery_handoff_v1") or {}

        self.assertEqual(((payload.get("primary_action") or {}).get("route")), "/s/contract.center")
        self.assertEqual(handoff.get("family"), "contracts")
        self.assertEqual(handoff.get("runtime_mode"), "direct")
        self.assertEqual(handoff.get("user_entry"), "menu:smart_construction_core.menu_sc_contract_center")
        self.assertEqual(handoff.get("final_scene"), "contract.center")

    def test_contract_center_registry_target_is_scene_first(self):
        rows = scene_registry_content.list_scene_entries()
        contract_center = next((row for row in rows if row.get("code") == "contract.center"), {})
        target = contract_center.get("target") or {}

        self.assertEqual(target.get("route"), "/s/contract.center")
        self.assertEqual(target.get("menu_xmlid"), "smart_construction_core.menu_sc_contract_center")
        self.assertNotIn("action_xmlid", target)

    def test_contract_center_capability_default_payload_is_scene_first(self):
        xml_path = SCENE_DIR / "data" / "sc_scene_orchestration.xml"
        tree = ET.parse(str(xml_path))
        capability = next(
            record
            for record in tree.findall(".//record")
            if record.get("id") == "smart_construction_core.sc_cap_contract_work"
        )
        default_payload = next(
            field
            for field in capability.findall("field")
            if field.get("name") == "default_payload"
        )
        payload_expr = str(default_payload.get("eval") or "")

        self.assertIn("'scene_key': 'contract.center'", payload_expr)
        self.assertIn("'route': '/s/contract.center'", payload_expr)
        self.assertIn("'menu_xmlid': 'smart_construction_core.menu_sc_contract_center'", payload_expr)
        self.assertNotIn("action_xmlid", payload_expr)

    def test_contract_center_is_in_critical_runtime_target_overrides(self):
        overrides = set(target_core_extension.smart_core_critical_scene_target_overrides(None))
        self.assertIn("contract.center", overrides)

    def test_contracts_workspace_provider_supplies_delivery_handoff_v1(self):
        payload = contracts_workspace_provider.build(scene_key="contracts.workspace", runtime={"company_id": 9})
        handoff = payload.get("delivery_handoff_v1") or {}

        self.assertEqual(handoff.get("family"), "contracts")
        self.assertEqual(handoff.get("runtime_entry_type"), "governed_user_flow")
        self.assertEqual(handoff.get("runtime_mode"), "direct")
        self.assertEqual(handoff.get("user_entry"), "route:/s/contracts.workspace")
        self.assertEqual(handoff.get("final_scene"), "contracts.workspace")

    def test_enterprise_bootstrap_scenes_supply_explicit_registry_targets(self):
        rows = scene_registry_content.list_scene_entries()
        company = next((row for row in rows if row.get("code") == "enterprise.company"), {})
        department = next((row for row in rows if row.get("code") == "enterprise.department"), {})
        user = next((row for row in rows if row.get("code") == "enterprise.user"), {})
        post = next((row for row in rows if row.get("code") == "enterprise.post"), {})

        self.assertEqual(((company.get("target") or {}).get("route")), "/s/enterprise.company")
        self.assertEqual(((company.get("target") or {}).get("menu_xmlid")), "smart_enterprise_base.menu_enterprise_company")
        self.assertEqual(((department.get("target") or {}).get("route")), "/s/enterprise.department")
        self.assertEqual(((department.get("target") or {}).get("action_xmlid")), "smart_enterprise_base.action_enterprise_department")
        self.assertEqual(((user.get("target") or {}).get("route")), "/s/enterprise.user")
        self.assertEqual(((user.get("target") or {}).get("action_xmlid")), "smart_enterprise_base.action_enterprise_user")
        self.assertEqual(((post.get("target") or {}).get("route")), "/s/enterprise.post")
        self.assertEqual(((post.get("target") or {}).get("action_xmlid")), "smart_enterprise_base.action_enterprise_post")

    def test_enterprise_bootstrap_provider_supplies_guidance_and_next_scene(self):
        company = enterprise_bootstrap_provider.build(scene_key="enterprise.company", runtime={"company_id": 9})
        department = enterprise_bootstrap_provider.build(scene_key="enterprise.department", runtime={"company_id": 9})
        post = enterprise_bootstrap_provider.build(scene_key="enterprise.post", runtime={"company_id": 9})
        user = enterprise_bootstrap_provider.build(scene_key="enterprise.user", runtime={"company_id": 9})

        self.assertEqual(company.get("next_scene"), "enterprise.department")
        self.assertEqual(company.get("next_scene_route"), "/s/enterprise.department")
        self.assertEqual(((department.get("guidance") or {}).get("title")), "组织架构")
        self.assertEqual(department.get("next_scene"), "enterprise.post")
        self.assertEqual(((post.get("guidance") or {}).get("title")), "岗位管理")
        self.assertEqual(post.get("next_scene"), "enterprise.user")
        self.assertFalse(bool(user.get("next_scene")))
        self.assertEqual(((user.get("guidance") or {}).get("title")), "用户设置")

    def test_approval_workbench_provider_supplies_approval_first_semantics(self):
        payload = approval_workbench_provider.build(scene_key="payments.approval", runtime={"company_id": 9})

        self.assertEqual(((payload.get("guidance") or {}).get("title")), "付款审批工作台")
        self.assertEqual(((payload.get("primary_action") or {}).get("action_xmlid")), "smart_construction_core.action_sc_tier_review_my_payment_request")
        self.assertEqual(((payload.get("primary_action") or {}).get("semantic")), "payment_approval_workbench_entry")
        self.assertEqual(((payload.get("next_action") or {}).get("semantic")), "payment_approval_queue")
        self.assertEqual(((payload.get("fallback_strategy") or {}).get("type")), "native_action_compat")

    def test_approval_workbench_provider_supplies_delivery_handoff_v1(self):
        payload = approval_workbench_provider.build(scene_key="payments.approval", runtime={"company_id": 9})
        handoff = payload.get("delivery_handoff_v1") or {}

        self.assertEqual(handoff.get("family"), "payment_approval")
        self.assertEqual(handoff.get("runtime_entry_type"), "governed_user_flow")
        self.assertEqual(handoff.get("runtime_mode"), "direct")
        self.assertEqual(handoff.get("user_entry"), "menu:smart_construction_core.menu_sc_tier_review_my_payment_request")
        self.assertEqual(handoff.get("final_scene"), "payments.approval")

    def test_payment_entry_workbench_provider_supplies_personal_entry_semantics(self):
        payload = payment_entry_workbench_provider.build(scene_key="finance.payment_requests", runtime={"company_id": 9})

        self.assertEqual(((payload.get("guidance") or {}).get("title")), "付款申请列表")
        self.assertEqual(((payload.get("primary_action") or {}).get("action_xmlid")), "smart_construction_core.action_payment_request_my")
        self.assertEqual(((payload.get("primary_action") or {}).get("semantic")), "payment_request_personal_entry")
        self.assertEqual(((payload.get("next_action") or {}).get("semantic")), "payment_request_list_queue")
        self.assertEqual(((payload.get("fallback_strategy") or {}).get("action_xmlid")), "smart_construction_core.action_payment_request")

    def test_payment_entry_workbench_provider_supplies_delivery_handoff_v1(self):
        payload = payment_entry_workbench_provider.build(scene_key="finance.payment_requests", runtime={"company_id": 9})
        handoff = payload.get("delivery_handoff_v1") or {}

        self.assertEqual(handoff.get("family"), "payment_entry")
        self.assertEqual(handoff.get("runtime_entry_type"), "governed_user_flow")
        self.assertEqual(handoff.get("runtime_mode"), "direct")
        self.assertEqual(handoff.get("user_entry"), "menu:smart_construction_core.menu_payment_request")
        self.assertEqual(handoff.get("final_scene"), "finance.payment_requests")

    def test_wave1_projects_provider_supplies_delivery_handoff_v1(self):
        payload = projects_list_provider.build(scene_key="projects.list", runtime={"company_id": 9})
        handoff = payload.get("delivery_handoff_v1") or {}

        self.assertEqual((payload.get("primary_action") or {}).get("action_xmlid"), "smart_construction_core.action_sc_project_list")
        self.assertEqual(handoff.get("family"), "projects")
        self.assertEqual(handoff.get("runtime_mode"), "direct")
        self.assertEqual(handoff.get("user_entry"), "menu:smart_construction_core.menu_sc_root")
        self.assertEqual(handoff.get("final_scene"), "projects.list")

    def test_wave1_finance_provider_supplies_delivery_handoff_v1(self):
        payload = finance_center_provider.build(scene_key="finance.center", runtime={"company_id": 9})
        handoff = payload.get("delivery_handoff_v1") or {}

        self.assertEqual(handoff.get("family"), "finance_center")
        self.assertEqual(handoff.get("runtime_consumer"), "family_runtime_consumer")
        self.assertEqual(handoff.get("runtime_mode"), "direct")
        self.assertEqual(handoff.get("final_scene"), "finance.center")
        self.assertEqual(((handoff.get("acceptance") or {}).get("workflow_ready")), True)

    def test_wave1_task_provider_supplies_delivery_handoff_v1(self):
        payload = task_center_provider.build(scene_key="task.center", runtime={"company_id": 9})
        handoff = payload.get("delivery_handoff_v1") or {}

        self.assertEqual(handoff.get("family"), "tasks")
        self.assertEqual(handoff.get("runtime_entry_type"), "governed_user_flow")
        self.assertEqual(handoff.get("runtime_mode"), "direct")
        self.assertEqual(handoff.get("user_entry"), "action:project.action_view_all_task")
        self.assertEqual(handoff.get("final_scene"), "task.center")

    def test_wave1_rollout_handoff_consumes_direct_runtime_surface(self):
        payload = projects_list_provider.build(scene_key="projects.list", runtime={"company_id": 9})
        bridged = scene_ready_bridge.apply_scene_ready_semantic_orchestration_bridge(
            payload,
            scene_key="projects.list",
        )

        rollout = workflow_rollout_handoff.build_wave1_rollout_handoff(
            bridged.get("runtime_handoff_surface")
        )

        self.assertEqual(rollout.get("family"), "projects")
        self.assertEqual(rollout.get("rollout_mode"), "direct_runtime_handoff")
        self.assertEqual(rollout.get("consume_mode"), "direct")
        self.assertEqual(rollout.get("final_scene"), "projects.list")
        self.assertEqual(((rollout.get("acceptance") or {}).get("advisory_only")), False)
        self.assertEqual(((rollout.get("acceptance") or {}).get("workflow_ready")), True)

    def test_wave1_rollout_handoff_consumes_advisory_runtime_surface(self):
        payload = approval_workbench_provider.build(scene_key="payments.approval", runtime={"company_id": 9})
        bridged = scene_ready_bridge.apply_scene_ready_semantic_orchestration_bridge(
            payload,
            scene_key="payments.approval",
        )

        rollout = workflow_rollout_handoff.build_wave1_rollout_handoff(
            bridged.get("runtime_handoff_surface")
        )

        self.assertEqual(rollout.get("family"), "payment_approval")
        self.assertEqual(rollout.get("rollout_mode"), "advisory_only")
        self.assertEqual(rollout.get("consume_mode"), "advisory")
        self.assertEqual(rollout.get("final_scene"), "payments.approval")
        self.assertEqual(((rollout.get("acceptance") or {}).get("advisory_only")), True)

    def test_project_management_scene_ready_provider_exposes_dashboard_page_semantics(self):
        payload = project_dashboard_scene_content.build(scene_key="project.management", runtime={}, context={})
        page = payload.get("page") if isinstance(payload.get("page"), dict) else {}

        self.assertEqual(page.get("key"), "project.management.dashboard")
        self.assertEqual(page.get("route"), "/s/project.management")
        self.assertEqual(page.get("page_type"), "dashboard")
        self.assertEqual(page.get("layout_mode"), "dashboard")

    def test_provider_merge_projects_dashboard_page_semantics_into_startup_contract(self):
        compiled = {
            "scene": {"key": "project.management", "title": "项目驾驶舱", "layout": {}},
            "page": {"scene_key": "project.management", "route": "/s/project.management", "zones": []},
            "meta": {},
        }
        providers = [{"key": "runtime.scene_provider.project.management", "payload": project_dashboard_scene_content.build(scene_key="project.management")}]
        merged = scene_merge_resolver.apply_provider_merge(
            compiled,
            providers,
            scene_merge_resolver.MergeContext(scene_key="project.management", runtime={}, provider_registry={}),
        )
        page = merged.get("page") if isinstance(merged.get("page"), dict) else {}

        self.assertEqual(page.get("key"), "project.management.dashboard")
        self.assertEqual(page.get("page_type"), "dashboard")
        self.assertEqual(page.get("layout_mode"), "dashboard")

    def test_smart_core_nav_scene_maps_derives_missing_action_and_menu_mappings(self):
        _reset_caches()
        target_core_extension.scene_registry.load_scene_configs = lambda env: [
            {
                "code": "finance.operating_metrics",
                "target": {
                    "menu_xmlid": "smart_construction_core.menu_sc_operating_metrics_project",
                    "action_xmlid": "smart_construction_core.action_sc_operating_metrics_project",
                    "model": "operating.metrics.project",
                    "view_type": "tree",
                },
            }
        ]
        maps = target_core_extension.smart_core_nav_scene_maps(_DummyEnv())

        self.assertEqual(
            maps["menu_scene_map"]["smart_construction_core.menu_sc_operating_metrics_project"],
            "finance.operating_metrics",
        )
        self.assertEqual(
            maps["action_xmlid_scene_map"]["smart_construction_core.action_sc_operating_metrics_project"],
            "finance.operating_metrics",
        )
        self.assertEqual(
            maps["model_view_scene_map"][("operating.metrics.project", "list")],
            "finance.operating_metrics",
        )
        self.assertEqual(
            maps["action_xmlid_scene_map"]["smart_construction_core.action_sc_project_list"],
            "projects.list",
        )
        self.assertEqual(
            maps["action_xmlid_scene_map"]["smart_construction_core.action_sc_project_overview"],
            "projects.list",
        )
        self.assertEqual(
            maps["action_xmlid_scene_map"]["smart_construction_core.action_sc_project_my_list"],
            "projects.list",
        )
        self.assertEqual(
            maps["action_xmlid_scene_map"]["smart_construction_core.action_sc_project_manage"],
            "project.management",
        )
        self.assertEqual(
            maps["menu_scene_map"]["smart_construction_core.menu_sc_project_initiation"],
            "projects.intake",
        )
        self.assertEqual(
            maps["menu_scene_map"]["smart_construction_core.menu_sc_project_quick_create"],
            "projects.intake",
        )
        self.assertEqual(
            maps["menu_scene_map"]["smart_construction_core.menu_sc_project_manage"],
            "project.management",
        )
        self.assertEqual(
            maps["action_xmlid_scene_map"]["smart_construction_core.action_project_initiation"],
            "projects.intake",
        )
        self.assertEqual(
            maps["action_xmlid_scene_map"]["smart_construction_core.action_project_initiation_quick"],
            "projects.intake",
        )
        self.assertNotIn(
            "smart_construction_demo.menu_sc_project_list_showcase",
            maps["menu_scene_map"],
        )
        self.assertNotIn(
            "smart_construction_demo.action_sc_project_list_showcase",
            maps["action_xmlid_scene_map"],
        )

    def test_projects_detail_remains_route_plus_record_context_authority_not_shared_action_owner(self):
        _reset_caches()
        target_core_extension.scene_registry.load_scene_configs = lambda env: list(scene_registry_content.list_scene_entries())
        maps = target_core_extension.smart_core_nav_scene_maps(_DummyEnv())

        self.assertEqual(
            maps["action_xmlid_scene_map"]["smart_construction_core.action_sc_project_list"],
            "projects.list",
        )
        self.assertNotEqual(
            maps["action_xmlid_scene_map"]["smart_construction_core.action_sc_project_overview"],
            "projects.detail",
        )
        self.assertNotEqual(
            maps["action_xmlid_scene_map"]["smart_construction_core.action_sc_project_my_list"],
            "projects.detail",
        )
        self.assertEqual(
            maps["action_xmlid_scene_map"]["smart_construction_core.action_sc_project_manage"],
            "project.management",
        )

    def test_smart_core_nav_scene_maps_include_enterprise_bootstrap_registry_targets(self):
        _reset_caches()
        target_core_extension.scene_registry.load_scene_configs = lambda env: list(scene_registry_content.list_scene_entries())
        maps = target_core_extension.smart_core_nav_scene_maps(_DummyEnv())

        self.assertEqual(
            maps["menu_scene_map"]["smart_enterprise_base.menu_enterprise_company"],
            "enterprise.company",
        )
        self.assertEqual(
            maps["action_xmlid_scene_map"]["smart_enterprise_base.action_enterprise_department"],
            "enterprise.department",
        )
        self.assertEqual(
            maps["action_xmlid_scene_map"]["smart_enterprise_base.action_enterprise_user"],
            "enterprise.user",
        )
        self.assertEqual(
            maps["action_xmlid_scene_map"]["smart_enterprise_base.action_enterprise_post"],
            "enterprise.post",
        )
        self.assertEqual(
            maps["menu_scene_map"]["smart_enterprise_base.menu_enterprise_post"],
            "enterprise.post",
        )

    def test_register_scene_providers_includes_enterprise_bootstrap_scenes(self):
        registry = _DummyRegistry()
        register_scene_providers.register_scene_content_providers(registry, SCENE_DIR.parent)
        specs = {row.get("scene_key"): row for row in registry.specs}

        self.assertEqual(
            ((specs.get("enterprise.company") or {}).get("provider_path")).name,
            "enterprise_bootstrap_provider.py",
        )
        self.assertEqual(
            ((specs.get("enterprise.department") or {}).get("provider_path")).name,
            "enterprise_bootstrap_provider.py",
        )
        self.assertEqual(
            ((specs.get("enterprise.user") or {}).get("provider_path")).name,
            "enterprise_bootstrap_provider.py",
        )
        self.assertEqual(
            ((specs.get("enterprise.post") or {}).get("provider_path")).name,
            "enterprise_bootstrap_provider.py",
        )
        self.assertEqual(
            ((specs.get("payments.approval") or {}).get("provider_path")).name,
            "approval_workbench_provider.py",
        )
        self.assertEqual(
            ((specs.get("payments.approval") or {}).get("provider_key")),
            "construction.approval_workbench_provider.v1",
        )
        self.assertEqual(
            ((specs.get("finance.payment_requests") or {}).get("provider_path")).name,
            "payment_entry_workbench_provider.py",
        )
        self.assertEqual(
            ((specs.get("finance.payment_requests") or {}).get("provider_key")),
            "construction.payment_entry_workbench_provider.v1",
        )
        self.assertEqual(
            ((specs.get("cost.project_budget") or {}).get("provider_path")).name,
            "cost_project_budget_provider.py",
        )
        self.assertEqual(
            ((specs.get("cost.project_budget") or {}).get("provider_key")),
            "construction.cost_project_budget_provider.v1",
        )

    def test_enterprise_enablement_targets_publish_scene_first_routes(self):
        payload = {}
        env = _DummyEnv(
            refs={
                "smart_enterprise_base.action_enterprise_company": 246,
                "smart_enterprise_base.menu_enterprise_company": 144,
                "smart_enterprise_base.action_enterprise_department": 247,
                "smart_enterprise_base.menu_enterprise_department": 145,
                "smart_enterprise_base.action_enterprise_user": 248,
                "smart_enterprise_base.menu_enterprise_user": 146,
            }
        )

        enterprise_base_core_extension.smart_core_extend_system_init(payload, env, _DummyUser())
        mainline = (((payload.get("ext_facts") or {}).get("enterprise_enablement") or {}).get("mainline") or {})
        steps = mainline.get("steps") or []

        self.assertEqual((((steps[0] or {}).get("target") or {}).get("route")), "/s/enterprise.company")
        self.assertEqual((((steps[1] or {}).get("target") or {}).get("route")), "/s/enterprise.department")
        self.assertEqual((((steps[2] or {}).get("target") or {}).get("route")), "/s/enterprise.user")
        self.assertEqual(((mainline.get("primary_action") or {}).get("route")), "/s/enterprise.company")

    def test_capability_entry_target_derives_scene_key_and_route_from_explicit_action_target(self):
        _reset_caches()
        scene_rows = [
            {
                "code": "finance.operating_metrics",
                "target": {
                    "route": "/s/finance.operating_metrics",
                    "menu_xmlid": "smart_construction_core.menu_sc_operating_metrics_project",
                    "action_xmlid": "smart_construction_core.action_sc_operating_metrics_project",
                    "action_id": 931,
                    "menu_id": 417,
                    "model": "operating.metrics.project",
                    "view_type": "tree",
                },
            }
        ]
        target_capability.scene_registry.load_scene_configs = lambda env: list(scene_rows)
        target_capability.scene_registry.load_scene_configs_with_timings = lambda env: (list(scene_rows), {})

        env = _DummyEnv(
            refs={
                "smart_construction_core.action_sc_operating_metrics_project": 931,
                "smart_construction_core.menu_sc_operating_metrics_project": 417,
            }
        )
        entry_target = target_capability.build_capability_entry_target(
            "",
            explicit_target={"action_xmlid": "smart_construction_core.action_sc_operating_metrics_project"},
            env=env,
        )
        payload = target_capability.resolve_capability_entry_target_payload(
            env,
            "",
            explicit_target={"action_xmlid": "smart_construction_core.action_sc_operating_metrics_project"},
        )

        self.assertEqual(entry_target["scene_key"], "finance.operating_metrics")
        self.assertEqual(payload["scene_key"], "finance.operating_metrics")
        self.assertEqual(payload["route"], "/s/finance.operating_metrics")
        self.assertEqual(payload["action_id"], 931)
        self.assertEqual(payload["menu_id"], 417)


if __name__ == "__main__":
    unittest.main()
