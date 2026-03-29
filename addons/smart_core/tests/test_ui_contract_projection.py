# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


SMART_CORE_DIR = Path(__file__).resolve().parents[1]
CORE_DIR = SMART_CORE_DIR / "core"
HANDLERS_DIR = SMART_CORE_DIR / "handlers"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


sys.modules.setdefault("odoo", types.ModuleType("odoo"))
odoo_module = sys.modules["odoo"]
odoo_module.api = types.SimpleNamespace(Environment=lambda cr, uid, ctx: types.SimpleNamespace(cr=cr, uid=uid, context=ctx))
odoo_module.SUPERUSER_ID = 1
odoo_tools = types.ModuleType("odoo.tools")
odoo_safe_eval = types.ModuleType("odoo.tools.safe_eval")
odoo_safe_eval.safe_eval = lambda expr, *args, **kwargs: expr
sys.modules["odoo.tools"] = odoo_tools
sys.modules["odoo.tools.safe_eval"] = odoo_safe_eval

odoo_addons = sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
smart_core_pkg.__path__ = [str(SMART_CORE_DIR)]
core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
core_pkg.__path__ = [str(CORE_DIR)]
handlers_pkg = sys.modules.setdefault("odoo.addons.smart_core.handlers", types.ModuleType("odoo.addons.smart_core.handlers"))
handlers_pkg.__path__ = [str(HANDLERS_DIR)]
app_config_pkg = sys.modules.setdefault(
    "odoo.addons.smart_core.app_config_engine", types.ModuleType("odoo.addons.smart_core.app_config_engine")
)
services_pkg = sys.modules.setdefault(
    "odoo.addons.smart_core.app_config_engine.services", types.ModuleType("odoo.addons.smart_core.app_config_engine.services")
)
dispatchers_pkg = sys.modules.setdefault(
    "odoo.addons.smart_core.app_config_engine.services.dispatchers",
    types.ModuleType("odoo.addons.smart_core.app_config_engine.services.dispatchers"),
)
utils_pkg = sys.modules.setdefault("odoo.addons.smart_core.utils", types.ModuleType("odoo.addons.smart_core.utils"))
odoo_addons.smart_core = smart_core_pkg
smart_core_pkg.core = core_pkg
smart_core_pkg.handlers = handlers_pkg
smart_core_pkg.app_config_engine = app_config_pkg
smart_core_pkg.utils = utils_pkg
app_config_pkg.services = services_pkg
services_pkg.dispatchers = dispatchers_pkg


base_handler_module = types.ModuleType("odoo.addons.smart_core.core.base_handler")


class BaseIntentHandler:
    def __init__(self, env, su_env=None, request=None, context=None, payload=None):
        self.env = env
        self.su_env = su_env or env
        self.request = request
        self.context = dict(context or {})
        self.payload = payload or {}
        self.params = self.payload

    def _err(self, code, message):
        return {"ok": False, "code": code, "message": message}


base_handler_module.BaseIntentHandler = BaseIntentHandler
sys.modules["odoo.addons.smart_core.core.base_handler"] = base_handler_module

projection_module = _load_module(
    "odoo.addons.smart_core.core.native_view_contract_projection",
    CORE_DIR / "native_view_contract_projection.py",
)
core_pkg.native_view_contract_projection = projection_module

contract_service_module = types.ModuleType("odoo.addons.smart_core.app_config_engine.services.contract_service")


class ContractService:
    last_shape_handler_delivery_call = None

    def __init__(self, env):
        self.env = env

    def finalize_contract(self, contract):
        return contract

    def finalize_data(self, data, *, subject=None, meta=None):
        return data

    @staticmethod
    def inject_render_hints(data, payload):
        return data

    def govern_data(
        self,
        data,
        *,
        contract_mode="user",
        contract_surface="user",
        source_mode="",
        inject_contract_mode=False,
    ):
        return data

    def apply_delivery_surface_governance(
        self,
        data,
        *,
        contract_mode="user",
        contract_surface="user",
        source_mode="",
        inject_contract_mode=False,
    ):
        return data

    def shape_handler_delivery_data(
        self,
        data,
        *,
        payload=None,
        contract_mode="user",
        contract_surface="user",
        source_mode="",
        inject_contract_mode=False,
    ):
        type(self).last_shape_handler_delivery_call = {
            "payload": payload,
            "contract_mode": contract_mode,
            "contract_surface": contract_surface,
            "source_mode": source_mode,
            "inject_contract_mode": inject_contract_mode,
        }
        return data


contract_service_module.ContractService = ContractService
sys.modules["odoo.addons.smart_core.app_config_engine.services.contract_service"] = contract_service_module
services_pkg.contract_service = contract_service_module


class _FakeDispatcher:
    def __init__(self, env, su_env):
        self.env = env
        self.su_env = su_env

    def dispatch(self, payload):
        return (
            {
                "head": {"model": payload.get("model"), "view_type": payload.get("view_type")},
                "views": {
                    "form": {
                        "layout": [{"kind": "group"}],
                        "parser_contract": {"view_type": "form", "layout": {"kind": "form"}},
                        "view_semantics": {"source_view": "form", "capability_flags": {"has_title": True}},
                    }
                },
            },
            {"etag": "demo"},
        )


nav_dispatcher_module = types.ModuleType("odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher")
nav_dispatcher_module.NavDispatcher = _FakeDispatcher
menu_dispatcher_module = types.ModuleType("odoo.addons.smart_core.app_config_engine.services.dispatchers.menu_dispatcher")
menu_dispatcher_module.MenuDispatcher = _FakeDispatcher
action_dispatcher_module = types.ModuleType("odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher")
action_dispatcher_module.ActionDispatcher = _FakeDispatcher
sys.modules["odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher"] = nav_dispatcher_module
sys.modules["odoo.addons.smart_core.app_config_engine.services.dispatchers.menu_dispatcher"] = menu_dispatcher_module
sys.modules["odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher"] = action_dispatcher_module
dispatchers_pkg.nav_dispatcher = nav_dispatcher_module
dispatchers_pkg.menu_dispatcher = menu_dispatcher_module
dispatchers_pkg.action_dispatcher = action_dispatcher_module

contract_governance_module = types.ModuleType("odoo.addons.smart_core.utils.contract_governance")
contract_governance_module.apply_contract_governance = lambda data, *args, **kwargs: data
contract_governance_module.resolve_contract_mode = lambda payload: "native"
contract_governance_module.resolve_contract_surface = lambda payload, contract_mode=None: "native"
sys.modules["odoo.addons.smart_core.utils.contract_governance"] = contract_governance_module
utils_pkg.contract_governance = contract_governance_module

ui_contract_module = _load_module("odoo.addons.smart_core.handlers.ui_contract", HANDLERS_DIR / "ui_contract.py")


class _FakeEnv(dict):
    cr = object()
    uid = 7
    user = types.SimpleNamespace(id=7)
    context = {}

    def __contains__(self, item):
        return item == "project.project"


class TestUiContractProjection(unittest.TestCase):
    def setUp(self):
        ContractService.last_shape_handler_delivery_call = None

    def test_op_model_promotes_parser_contract_and_semantics(self):
        handler = ui_contract_module.UiContractHandler(
            env=_FakeEnv(),
            su_env=_FakeEnv(),
            context={},
            payload={"model": "project.project", "view_type": "form"},
        )

        data, meta = handler._op_model({"model": "project.project", "view_type": "form"}, {})

        self.assertEqual(data["parser_contract"]["view_type"], "form")
        self.assertEqual(data["view_semantics"]["source_view"], "form")
        self.assertEqual(data["layout"], [{"kind": "group"}])
        self.assertEqual(data["view_type"], "form")
        self.assertEqual(meta["schema_version"], "view-contract-1")

    def test_handle_uses_canonical_handler_delivery_helper(self):
        handler = ui_contract_module.UiContractHandler(
            env=_FakeEnv(),
            su_env=_FakeEnv(),
            context={},
            payload={"op": "model", "model": "project.project", "view_type": "form"},
        )

        response = handler.handle({"op": "model", "model": "project.project", "view_type": "form"}, {})

        self.assertTrue(response["ok"])
        self.assertIsNotNone(ContractService.last_shape_handler_delivery_call)
        self.assertEqual(ContractService.last_shape_handler_delivery_call["contract_mode"], "native")
        self.assertEqual(ContractService.last_shape_handler_delivery_call["contract_surface"], "native")


if __name__ == "__main__":
    unittest.main()
