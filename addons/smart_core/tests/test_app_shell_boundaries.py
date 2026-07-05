# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, request=None, params=None, context=None):
        self.env = env or types.SimpleNamespace(uid=9)
        self.request = request
        self.params = params or {}
        self.context = context or {}


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_handler():
    root = Path(__file__).resolve().parents[1]
    _install_module("odoo")
    _install_module("odoo.addons")
    smart_core_mod = _install_module("odoo.addons.smart_core")
    handlers_mod = _install_module("odoo.addons.smart_core.handlers")
    core_mod = _install_module("odoo.addons.smart_core.core")
    security_mod = _install_module("odoo.addons.smart_core.security")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]
    security_mod.__path__ = [str(root / "security")]

    _install_module("odoo.addons.smart_core.core.base_handler", BaseIntentHandler=_BaseIntentHandler)
    _install_module(
        "odoo.addons.smart_core.security.platform_admin",
        user_is_platform_admin=lambda user: bool(getattr(user, "is_platform_admin", False)),
    )
    _install_module(
        "odoo.addons.smart_core.core.scene_provider",
        load_scenes_from_db_or_fallback=lambda *args, **kwargs: {
            "scenes": [
                {"key": "workspace.home", "label": "Home", "target": {"route": "/s/workspace.home"}},
                {"key": "project.initiation", "label": "Project Initiation", "target": {"route": "/s/project.initiation"}},
                {"key": "projects.list", "label": "Projects", "target": {"route": "/s/projects.list"}},
                {"key": "contract.center", "label": "Contract", "target": {"route": "/s/contract.center"}},
                {"key": "contracts.workspace", "label": "Contracts", "target": {"route": "/s/contracts.workspace"}},
                {"key": "delivery.command", "label": "Delivery", "target": {"route": "/s/delivery.command"}},
                {"key": "scene_smoke_default", "label": "Smoke", "target": {"route": "/s/scene_smoke_default"}},
                {"key": "default", "label": "Default", "target": {"route": "/s/default"}},
            ]
        },
    )
    _install_module(
        "odoo.addons.smart_core.core.unified_page_contract_v2_client",
        resolve_client_type=lambda headers, payload: "web_mobile",
        resolve_delivery_profile=lambda client_type, payload=None: "mobile_compact",
        trim_navigation_contract_for_client=lambda contract, **kwargs: {
            **contract,
            "trim_kwargs": kwargs,
        },
    )
    utils_mod = _install_module("odoo.addons.smart_core.utils")
    utils_mod.__path__ = [str(root / "utils")]

    def _extension_hook(env, hook_name, *args, **kwargs):
        if hook_name == "smart_core_app_shell_contract":
            return {
                "taxonomy": {
                    "projects": {
                        "label": "项目管理",
                        "category": "business",
                        "sequence": 20,
                        "primary_scene": "projects.list",
                    },
                    "contracts": {
                        "label": "合同管理",
                        "category": "business",
                        "sequence": 30,
                        "primary_scene": "contracts.workspace",
                    },
                },
                "aliases": {
                    "project": "projects",
                    "contract": "contracts",
                },
            }
        return None

    _install_module(
        "odoo.addons.smart_core.utils.extension_hooks",
        call_extension_hook_first=_extension_hook,
    )

    request_params_name = "odoo.addons.smart_core.core.request_params"
    sys.modules.pop(request_params_name, None)
    request_params_spec = importlib.util.spec_from_file_location(
        request_params_name, root / "core" / "request_params.py"
    )
    request_params_module = importlib.util.module_from_spec(request_params_spec)
    sys.modules[request_params_name] = request_params_module
    request_params_spec.loader.exec_module(request_params_module)

    module_name = "odoo.addons.smart_core.handlers.app_shell"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "app_shell.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class _FakeAction:
    def __init__(self, action_id=501, name="Product Policies", res_model="sc.product.policy", view_mode="tree,form"):
        self.id = action_id
        self.name = name
        self.res_model = res_model
        self.view_mode = view_mode


class _FakeEnv:
    uid = 9

    def __init__(self, *, is_platform_admin=False, has_action=True):
        self.user = types.SimpleNamespace(is_platform_admin=is_platform_admin)
        self.has_action = has_action

    def ref(self, xmlid, raise_if_not_found=False):
        if self.has_action and xmlid == "smart_core.action_sc_product_policy":
            return _FakeAction()
        if self.has_action and xmlid == "smart_core.action_sc_subscription_plan":
            return _FakeAction(action_id=502, name="Subscription Plans", res_model="sc.subscription.plan")
        return None


class TestAppShellBoundaries(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler()

    def test_nav_rejects_invalid_max_items(self):
        handler = self.module.AppNavHandler(env=types.SimpleNamespace(uid=9))

        result = handler.handle(payload={"params": {"max_items": "bad"}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "max_items 无效")

    def test_nav_rejects_invalid_max_depth(self):
        handler = self.module.AppNavHandler(env=types.SimpleNamespace(uid=9))

        result = handler.handle(payload={"params": {"max_depth": 0}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "max_depth 无效")

    def test_nav_passes_valid_limits_to_trim(self):
        handler = self.module.AppNavHandler(env=types.SimpleNamespace(uid=9))

        result = handler.handle(payload={"params": {"max_items": "3", "max_depth": "2"}})

        self.assertTrue(result["ok"])
        trim_kwargs = result["data"]["trim_kwargs"]
        self.assertEqual(trim_kwargs["max_items"], 3)
        self.assertEqual(trim_kwargs["max_depth"], 2)

    def test_open_reads_nested_app_param(self):
        handler = self.module.AppOpenHandler(env=types.SimpleNamespace(uid=9))

        result = handler.handle(payload={"params": {"app": "workspace"}})

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["subject"], "ui.contract")
        self.assertEqual(result["data"]["scene_key"], "workspace.home")

    def test_open_workspace_has_minimum_fallback(self):
        original_scene_list = self.module._scene_list
        self.module._scene_list = lambda env: []
        try:
            handler = self.module.AppOpenHandler(env=types.SimpleNamespace(uid=9))

            result = handler.handle(payload={"params": {"app": "workspace"}})
        finally:
            self.module._scene_list = original_scene_list

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["scene_key"], "workspace.home")
        self.assertEqual(result["data"]["route"], "/s/workspace.home")

    def test_catalog_projects_published_label_and_alias_merge(self):
        handler = self.module.AppCatalogHandler(env=types.SimpleNamespace(uid=9))

        result = handler.handle(payload={})

        self.assertTrue(result["ok"])
        apps = result["data"]["apps"]
        app_ids = [row["meta"]["app_id"] for row in apps]
        labels = {row["meta"]["app_id"]: row["label"] for row in apps}
        sequences = {row["meta"]["app_id"]: row["meta"]["sequence"] for row in apps}
        self.assertEqual(apps[0]["meta"]["app_id"], "workspace")
        self.assertIn("projects", app_ids)
        self.assertNotIn("project", app_ids)
        self.assertIn("contracts", app_ids)
        self.assertNotIn("contract", app_ids)
        self.assertNotIn("default", app_ids)
        self.assertNotIn("scene_smoke_default", app_ids)
        self.assertNotIn("delivery", app_ids)
        self.assertEqual(labels["projects"], "项目管理")
        self.assertEqual(labels["contracts"], "合同管理")
        self.assertEqual(sequences["workspace"], 0)

    def test_catalog_keeps_delivery_app_platform_admin_only(self):
        normal_handler = self.module.AppCatalogHandler(env=_FakeEnv(is_platform_admin=False))
        admin_handler = self.module.AppCatalogHandler(env=_FakeEnv(is_platform_admin=True))

        normal_result = normal_handler.handle(payload={})
        admin_result = admin_handler.handle(payload={})

        normal_app_ids = [row["meta"]["app_id"] for row in normal_result["data"]["apps"]]
        admin_app_ids = [row["meta"]["app_id"] for row in admin_result["data"]["apps"]]
        self.assertNotIn("delivery", normal_app_ids)
        self.assertIn("delivery", admin_app_ids)

    def test_catalog_hides_business_apps_from_platform_admin_without_business_groups(self):
        handler = self.module.AppCatalogHandler(env=_FakeEnv(is_platform_admin=True))

        result = handler.handle(payload={})

        app_ids = [row["meta"]["app_id"] for row in result["data"]["apps"]]
        self.assertIn("workspace", app_ids)
        self.assertIn("release_management", app_ids)
        self.assertNotIn("projects", app_ids)
        self.assertNotIn("contracts", app_ids)

    def test_nav_hides_business_scene_from_platform_admin_without_business_groups(self):
        handler = self.module.AppNavHandler(env=_FakeEnv(is_platform_admin=True))

        result = handler.handle(payload={"params": {"app": "projects"}})

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["sections"], [])

    def test_open_alias_app_uses_stable_primary_scene(self):
        handler = self.module.AppOpenHandler(env=types.SimpleNamespace(uid=9))

        result = handler.handle(payload={"params": {"app": "project"}})

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["scene_key"], "projects.list")

    def test_catalog_adds_platform_admin_apps_only_for_platform_admin(self):
        normal_handler = self.module.AppCatalogHandler(env=_FakeEnv(is_platform_admin=False))
        admin_handler = self.module.AppCatalogHandler(env=_FakeEnv(is_platform_admin=True))

        normal_result = normal_handler.handle(payload={})
        admin_result = admin_handler.handle(payload={})

        normal_app_ids = [row["meta"]["app_id"] for row in normal_result["data"]["apps"]]
        admin_app_ids = [row["meta"]["app_id"] for row in admin_result["data"]["apps"]]
        self.assertNotIn("release_management", normal_app_ids)
        self.assertIn("release_management", admin_app_ids)
        self.assertIn("company_access", admin_app_ids)
        self.assertEqual(admin_result["data"]["apps"][0]["meta"]["app_id"], "release_management")

    def test_open_platform_admin_app_returns_release_operator_target(self):
        handler = self.module.AppOpenHandler(env=_FakeEnv(is_platform_admin=True))

        result = handler.handle(payload={"params": {"app": "release_management"}})

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["subject"], "ui.contract")
        self.assertEqual(result["data"]["route"], "/admin/release-operator?product_key=platform.standard")
        self.assertEqual(result["data"]["intent"], "release.operator.surface")

    def test_nav_platform_admin_app_returns_management_action(self):
        handler = self.module.AppNavHandler(env=_FakeEnv(is_platform_admin=True))

        result = handler.handle(payload={"params": {"app": "release_management"}})

        self.assertTrue(result["ok"])
        child = result["data"]["sections"][0]["children"][0]
        self.assertEqual(child["meta"]["kind"], "admin")
        self.assertEqual(child["meta"]["open"]["subject"], "ui.contract")
        self.assertEqual(child["meta"]["open"]["route"], "/admin/release-operator?product_key=platform.standard")


if __name__ == "__main__":
    unittest.main()
