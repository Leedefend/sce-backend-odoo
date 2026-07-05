# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]


def _load_module(module_name: str, relative_path: str):
    target = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, target)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _ensure_stub_packages():
    odoo_module = sys.modules.setdefault("odoo", types.ModuleType("odoo"))
    odoo_module.api = SimpleNamespace(Environment=lambda *args, **kwargs: None)
    odoo_module.fields = SimpleNamespace(Datetime=SimpleNamespace(now=lambda: "2026-01-01 00:00:00"))
    odoo_module.SUPERUSER_ID = 1
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    sys.modules.setdefault("odoo.modules", types.ModuleType("odoo.modules"))
    registry_module = sys.modules.setdefault("odoo.modules.registry", types.ModuleType("odoo.modules.registry"))
    registry_module.Registry = lambda *args, **kwargs: None
    smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
    smart_core_pkg.__path__ = [str(ROOT / "addons/smart_core")]
    core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
    core_pkg.__path__ = [str(ROOT / "addons/smart_core/core")]
    sys.modules.setdefault("odoo.exceptions", types.ModuleType("odoo.exceptions"))
    sys.modules["odoo.exceptions"].AccessError = type("AccessError", (Exception,), {})


_ensure_stub_packages()
_load_module(
    "odoo.addons.smart_core.core.scene_contract_parser_semantic_bridge",
    "addons/smart_core/core/scene_contract_parser_semantic_bridge.py",
)
_load_module(
    "odoo.addons.smart_core.core.scene_contract_semantic_orchestration_bridge",
    "addons/smart_core/core/scene_contract_semantic_orchestration_bridge.py",
)
_load_module(
    "odoo.addons.smart_core.core.released_scene_semantic_surface_bridge",
    "addons/smart_core/core/released_scene_semantic_surface_bridge.py",
)


SCENE_CONTRACT_BUILDER = _load_module(
    "smart_core_scene_contract_builder_test",
    "addons/smart_core/core/scene_contract_builder.py",
)
PRODUCT_POLICY_SERVICE = _load_module(
    "smart_core_product_policy_service_test",
    "addons/smart_core/delivery/product_policy_service.py",
)
PRODUCT_POLICY_CATALOG_SYNC_SERVICE = _load_module(
    "odoo.addons.smart_core.delivery.product_policy_catalog_sync_service",
    "addons/smart_core/delivery/product_policy_catalog_sync_service.py",
)
CORE_EXTENSION = _load_module(
    "smart_construction_core_extension_test",
    "addons/smart_construction_core/core_extension.py",
)


def _use_construction_catalog_source(service):
    service._catalog_source_config = lambda source_env: {
        "module": "smart_construction_core",
        "xmlid_prefix": "smart_construction_core.",
        "root_label": "智慧施工管理平台",
    }
    return service


class _FakeAction:
    def __init__(self, action_id: int, res_model: str = "", *, model_name: str = "", model_id=None):
        self.id = action_id
        self.res_model = res_model
        self.model_name = model_name
        self.model_id = model_id
        self._name = "ir.actions.act_window"


class _FakeMenu:
    def __init__(
        self,
        menu_id: int,
        name: str,
        *,
        xmlid: str,
        parent=None,
        action=None,
        sequence=10,
        active=True,
    ):
        self.id = menu_id
        self.name = name
        self.parent_id = parent
        self.action = action
        self.sequence = sequence
        self.active = active
        self._xmlid = xmlid
        self.child_id = []
        if parent is not None and hasattr(parent, "child_id"):
            parent.child_id.append(self)

    def get_external_id(self):
        return {self.id: self._xmlid}


class _FakeMenuModel:
    def __init__(self, records):
        self.records = records
        self.last_domain = None
        self.browsed_ids = []

    def sudo(self):
        return self

    def search(self, domain, order=None):
        self.last_domain = list(domain or [])
        if domain == [("action", "!=", False)]:
            return []
        return list(self.records)

    def browse(self, ids):
        self.browsed_ids = list(ids or [])
        return _FakeRecordset([record for record in self.records if record.id in self.browsed_ids])


class _FakeRecordset(list):
    def exists(self):
        return self


class _FakeModelDataRow:
    def __init__(self, res_id: int):
        self.res_id = res_id


class _FakeModelDataModel:
    def __init__(self, menu_ids):
        self.menu_ids = menu_ids
        self.last_domain = None

    def sudo(self):
        return self

    def search(self, domain):
        self.last_domain = list(domain or [])
        return [_FakeModelDataRow(menu_id) for menu_id in self.menu_ids]


class _FakeSourceEnv:
    def __init__(self, menu_model, model_data_model):
        self.menu_model = menu_model
        self.model_data_model = model_data_model

    def __getitem__(self, key):
        if key == "ir.ui.menu":
            return self.menu_model
        if key == "ir.model.data":
            return self.model_data_model
        raise KeyError(key)


class TestBackendSemanticCopySupply(unittest.TestCase):
    def test_release_surface_contract_keeps_backend_description_and_scope(self):
        contract = SCENE_CONTRACT_BUILDER.build_release_surface_scene_contract_from_delivery_entry(
            {
                "scene_key": "payment",
                "label": "FR-4 付款记录",
                "route": "/release/fr4",
                "product_key": "fr4",
                "capability_key": "delivery.fr4.payment_tracking",
                "requires_project_context": True,
                "description": "查看与记录项目付款事实。",
                "scope": "项目执行 -> 成本 -> 付款记录 -> 付款汇总。",
            }
        )
        identity = contract.get("identity") or {}
        self.assertEqual(identity.get("description"), "查看与记录项目付款事实。")
        self.assertEqual(identity.get("scope"), "项目执行 -> 成本 -> 付款记录 -> 付款汇总。")

    def test_missing_construction_policy_uses_empty_platform_shell(self):
        class _Env:
            registry = SimpleNamespace(models={})

            def __getitem__(self, key):
                raise KeyError(key)

        service = PRODUCT_POLICY_SERVICE.ProductPolicyService(_Env())
        policy = service.get_policy(product_key="construction.standard")

        self.assertEqual(policy.get("product_key"), "construction.standard")
        self.assertEqual(((policy.get("policy_source_authority") or {}).get("kind")), "minimal_default_product_policy_provider")
        self.assertEqual(policy.get("menu_groups") or [], [])
        self.assertEqual(policy.get("scenes") or [], [])
        self.assertEqual(policy.get("capabilities") or [], [])

    def test_default_product_policy_fallback_is_provider_scoped_and_parameterized(self):
        class _Env:
            registry = SimpleNamespace(models={})

            def __getitem__(self, key):
                raise KeyError(key)

        service = PRODUCT_POLICY_SERVICE.ProductPolicyService(_Env())
        source = service.default_policy_source_authority_contract()
        policy = service.get_policy(product_key="platform.preview")

        self.assertEqual(source.get("kind"), "platform_default_product_policy_provider")
        self.assertTrue(source.get("no_business_fact_authority"))
        self.assertEqual(policy.get("product_key"), "platform.preview")
        self.assertEqual(policy.get("base_product_key"), "platform")
        self.assertEqual(policy.get("edition_key"), "preview")
        self.assertEqual(policy.get("label"), "Platform Preview")
        self.assertEqual(((policy.get("policy_source_authority") or {}).get("kind")), "minimal_default_product_policy_provider")
        self.assertEqual(policy.get("scenes") or [], [])

    def test_enterprise_enablement_contract_supplies_status_label(self):
        user = SimpleNamespace(company_id=SimpleNamespace(id=3, name="Demo Co"))
        payload = CORE_EXTENSION._build_enterprise_enablement_contract(env=None, user=user)
        steps = (((payload or {}).get("mainline") or {}).get("steps")) or []
        self.assertTrue(steps)
        self.assertTrue(all(isinstance(row, dict) and row.get("status_label") for row in steps))

    def test_catalog_sync_extracts_project_center_when_action_domain_is_stale(self):
        root = _FakeMenu(1, "智慧施工管理平台", xmlid="smart_construction_core.menu_sc_root")
        project_center = _FakeMenu(
            2,
            "项目中心",
            xmlid="smart_construction_core.menu_sc_project_center",
            parent=root,
        )
        project_group = _FakeMenu(
            3,
            "项目管理",
            xmlid="smart_construction_core.menu_sc_project_management_group",
            parent=project_center,
        )
        project_ledger = _FakeMenu(
            4,
            "项目台账",
            xmlid="smart_construction_core.menu_sc_project_project",
            parent=project_group,
            action=_FakeAction(506, "project.project"),
        )
        menu_model = _FakeMenuModel([root, project_center, project_group, project_ledger])
        model_data_model = _FakeModelDataModel([root.id, project_center.id, project_group.id, project_ledger.id])
        service = _use_construction_catalog_source(
            PRODUCT_POLICY_CATALOG_SYNC_SERVICE.ProductPolicyCatalogSyncService(env=None)
        )

        pages = service._extract_user_menu_pages(_FakeSourceEnv(menu_model, model_data_model))

        self.assertEqual(menu_model.last_domain, None)
        self.assertEqual(menu_model.browsed_ids, [1, 2, 3, 4])
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["group_label"], "项目中心")
        self.assertEqual(pages[0]["visible_menu_path"], "智慧施工管理平台 / 项目中心 / 项目管理 / 项目台账")
        self.assertEqual(pages[0]["menu_xmlid"], "smart_construction_core.menu_sc_project_project")

    def test_catalog_sync_extracts_server_action_model_target(self):
        root = _FakeMenu(1, "智慧施工管理平台", xmlid="smart_construction_core.menu_sc_root")
        project_center = _FakeMenu(
            2,
            "项目中心",
            xmlid="smart_construction_core.menu_sc_project_center",
            parent=root,
        )
        project_group = _FakeMenu(
            3,
            "项目管理",
            xmlid="smart_construction_core.menu_sc_project_management_group",
            parent=project_center,
        )
        execution_structure = _FakeMenu(
            4,
            "执行结构",
            xmlid="smart_construction_core.menu_sc_project_wbs",
            parent=project_group,
            action=_FakeAction(519, model_name="project.project"),
        )
        menu_model = _FakeMenuModel([root, project_center, project_group, execution_structure])
        model_data_model = _FakeModelDataModel([root.id, project_center.id, project_group.id, execution_structure.id])
        service = _use_construction_catalog_source(
            PRODUCT_POLICY_CATALOG_SYNC_SERVICE.ProductPolicyCatalogSyncService(env=None)
        )

        pages = service._extract_user_menu_pages(_FakeSourceEnv(menu_model, model_data_model))

        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["menu_xmlid"], "smart_construction_core.menu_sc_project_wbs")
        self.assertEqual(pages[0]["res_model"], "project.project")

    def test_catalog_sync_skips_action_directories_and_non_product_roots(self):
        root = _FakeMenu(1, "智慧施工管理平台", xmlid="smart_construction_core.menu_sc_root")
        contract_center = _FakeMenu(
            2,
            "合同中心",
            xmlid="smart_construction_core.menu_sc_contract_center",
            parent=root,
            action=_FakeAction(578, "construction.contract.income"),
        )
        income_ledger = _FakeMenu(
            3,
            "收入合同台账",
            xmlid="smart_construction_core.menu_sc_contract_income",
            parent=contract_center,
            action=_FakeAction(578, "construction.contract.income"),
        )
        native_root = _FakeMenu(10, "项目", xmlid="project.menu_main_pm")
        native_budget = _FakeMenu(
            11,
            "项目预算",
            xmlid="smart_construction_core.menu_project_budget",
            parent=native_root,
            action=_FakeAction(507, "project.budget"),
        )
        menu_model = _FakeMenuModel([root, contract_center, income_ledger, native_root, native_budget])
        model_data_model = _FakeModelDataModel([1, 2, 3, 10, 11])
        service = _use_construction_catalog_source(
            PRODUCT_POLICY_CATALOG_SYNC_SERVICE.ProductPolicyCatalogSyncService(env=None)
        )

        pages = service._extract_user_menu_pages(_FakeSourceEnv(menu_model, model_data_model))

        self.assertEqual([page["menu_xmlid"] for page in pages], ["smart_construction_core.menu_sc_contract_income"])

    def test_policy_payload_dedupes_same_label_and_model_within_group(self):
        service = PRODUCT_POLICY_CATALOG_SYNC_SERVICE.ProductPolicyCatalogSyncService(env=None)

        payload = service._build_catalog_policy_payload_from_menu_pages(
            identity={
                "product_key": "construction.standard",
                "base_product_key": "construction",
                "edition_key": "standard",
            },
            menu_pages=[
                {
                    "group_key": "construction.contract",
                    "group_label": "合同中心",
                    "page_key": "smart_construction_core.menu_a",
                    "page_label": "历史采购/一般合同事实",
                    "menu_key": "smart_construction_core.menu_a",
                    "route": "/a/714?menu_id=1",
                    "app_id": "contract",
                    "menu_id": 1,
                    "menu_xmlid": "smart_construction_core.menu_a",
                    "action_id": 714,
                    "res_model": "sc.legacy.purchase.contract.fact",
                },
                {
                    "group_key": "construction.contract",
                    "group_label": "合同中心",
                    "page_key": "smart_construction_core.menu_b",
                    "page_label": "历史采购/一般合同事实",
                    "menu_key": "smart_construction_core.menu_b",
                    "route": "/a/798?menu_id=2",
                    "app_id": "contract",
                    "menu_id": 2,
                    "menu_xmlid": "smart_construction_core.menu_b",
                    "action_id": 798,
                    "res_model": "sc.legacy.purchase.contract.fact",
                },
            ],
            menu_source={"source_db": "sc_demo", "source": "test"},
        )

        menus = payload["menu_groups"][0]["menus"]
        self.assertEqual(len(menus), 1)
        self.assertEqual(menus[0]["menu_xmlid"], "smart_construction_core.menu_a")


if __name__ == "__main__":
    unittest.main()
