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
    sys.modules.setdefault("odoo", types.ModuleType("odoo"))
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
    sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
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
CORE_EXTENSION = _load_module(
    "smart_construction_core_extension_test",
    "addons/smart_construction_core/core_extension.py",
)


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

    def test_default_product_policy_scenes_include_user_facing_copy(self):
        scenes = PRODUCT_POLICY_SERVICE.DEFAULT_PRODUCT_POLICY.get("scenes") or []
        payment_scene = next((row for row in scenes if isinstance(row, dict) and row.get("scene_key") == "payment"), {})
        self.assertTrue(payment_scene.get("description"))
        self.assertTrue(payment_scene.get("scope"))

    def test_legacy_default_product_policy_nodes_are_marked_as_projection(self):
        class _Env:
            registry = SimpleNamespace(models={})

            def __getitem__(self, key):
                raise KeyError(key)

        service = PRODUCT_POLICY_SERVICE.ProductPolicyService(_Env())
        policy = service.get_policy(product_key="construction.standard")
        payment_scene = next((row for row in policy.get("scenes") or [] if row.get("scene_key") == "payment"), {})
        first_menu = ((((policy.get("menu_groups") or [{}])[0]).get("menus") or [{}])[0])

        self.assertEqual(
            ((payment_scene.get("policy_node_source_authority") or {}).get("kind")),
            "legacy_default_product_policy_node_projection",
        )
        self.assertEqual(
            ((first_menu.get("policy_node_source_authority") or {}).get("kind")),
            "legacy_default_product_policy_node_projection",
        )

    def test_default_product_policy_fallback_is_provider_scoped_and_parameterized(self):
        class _Env:
            registry = SimpleNamespace(models={})

            def __getitem__(self, key):
                raise KeyError(key)

        service = PRODUCT_POLICY_SERVICE.ProductPolicyService(_Env())
        source = service.default_policy_source_authority_contract()
        policy = service.get_policy(product_key="platform.preview")

        self.assertEqual(source.get("kind"), "legacy_default_product_policy_provider")
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


if __name__ == "__main__":
    unittest.main()
