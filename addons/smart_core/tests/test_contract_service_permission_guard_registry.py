# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


SMART_CORE_DIR = Path(__file__).resolve().parents[1]


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_contract_service():
    root = SMART_CORE_DIR
    _install_module("odoo")
    _install_module("odoo.http", request=types.SimpleNamespace(httprequest=types.SimpleNamespace(headers={})))
    _install_module(
        "odoo.api",
        Environment=lambda cr, uid, context: types.SimpleNamespace(cr=cr, uid=uid, context=context),
    )
    odoo_mod = sys.modules["odoo"]
    odoo_mod.SUPERUSER_ID = 1
    odoo_mod.api = sys.modules["odoo.api"]
    _install_module("odoo.tools")
    _install_module("odoo.tools.safe_eval", safe_eval=lambda raw, ctx=None: eval(raw, {"__builtins__": {}}, ctx or {}))
    _install_module("odoo.addons")
    smart_core_mod = _install_module("odoo.addons.smart_core")
    app_config_mod = _install_module("odoo.addons.smart_core.app_config_engine")
    services_mod = _install_module("odoo.addons.smart_core.app_config_engine.services")
    utils_mod = _install_module("odoo.addons.smart_core.app_config_engine.utils")
    dispatchers_mod = _install_module("odoo.addons.smart_core.app_config_engine.services.dispatchers")
    core_mod = _install_module("odoo.addons.smart_core.core")
    smart_core_mod.__path__ = [str(root)]
    app_config_mod.__path__ = [str(root / "app_config_engine")]
    services_mod.__path__ = [str(root / "app_config_engine" / "services")]
    utils_mod.__path__ = [str(root / "app_config_engine" / "utils")]
    dispatchers_mod.__path__ = [str(root / "app_config_engine" / "services" / "dispatchers")]
    core_mod.__path__ = [str(root / "core")]
    _install_module("odoo.addons.smart_core.app_config_engine.utils.http", read_json_body=lambda _request: {})
    _install_module("odoo.addons.smart_core.app_config_engine.utils.payload", parse_payload=lambda payload: payload)
    _install_module(
        "odoo.addons.smart_core.app_config_engine.utils.misc",
        stable_etag=lambda payload: "etag",
        format_versions=lambda versions: versions,
    )
    _install_module(
        "odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher",
        NavDispatcher=object,
    )
    _install_module(
        "odoo.addons.smart_core.app_config_engine.services.dispatchers.menu_dispatcher",
        MenuDispatcher=object,
    )
    _install_module(
        "odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher",
        ActionDispatcher=object,
    )
    _install_module("odoo.addons.smart_core.core.trace", get_trace_id=lambda headers=None: "trace")
    _install_module(
        "odoo.addons.smart_core.core.exceptions",
        BAD_REQUEST="bad_request",
        VALIDATION_ERROR="validation_error",
        INTERNAL_ERROR="internal_error",
        DEFAULT_API_VERSION="v1",
        DEFAULT_CONTRACT_VERSION="v2",
        build_error_envelope=lambda **kwargs: kwargs,
    )
    _install_module(
        "odoo.addons.smart_core.utils.contract_governance",
        apply_contract_governance=lambda data, mode, inject_contract_mode=False: data,
        resolve_contract_mode=lambda payload: "native",
    )
    sys.modules.pop("odoo.addons.smart_core.app_config_engine.services.contract_service", None)
    spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.app_config_engine.services.contract_service",
        root / "app_config_engine" / "services" / "contract_service.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestContractServicePermissionGuardRegistry(unittest.TestCase):
    def test_tautology_permission_guard_groups_are_extension_registered(self):
        module = _load_contract_service()

        self.assertEqual(module.tautology_permission_guard_group_xmlids(), ())

        module.register_tautology_permission_guard_group_xmlid("base.group_user")
        module.register_tautology_permission_guard_group_xmlid("base.group_user")
        module.register_tautology_permission_guard_group_xmlid("")

        self.assertEqual(module.tautology_permission_guard_group_xmlids(), ("base.group_user",))

    def test_finalize_contract_uses_registered_tautology_permission_guard_groups(self):
        module = _load_contract_service()
        module.register_tautology_permission_guard_group_xmlid("base.group_user")
        service = object.__new__(module.ContractService)
        contract = {
            "data": {
                "permissions": {
                    "rules": {
                        "read": {
                            "clauses": [
                                {
                                    "domain": [(1, "=", 1)],
                                    "groups_xmlids": ["custom.group_existing"],
                                    "global": True,
                                }
                            ]
                        }
                    }
                }
            }
        }

        result = service.finalize_contract(contract)

        clause = result["data"]["permissions"]["rules"]["read"]["clauses"][0]
        self.assertEqual(clause["groups_xmlids"], ["base.group_user", "custom.group_existing"])
        self.assertFalse(clause["global"])


if __name__ == "__main__":
    unittest.main()
