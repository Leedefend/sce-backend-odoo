# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


def _install_module(name, **attrs):
    mod = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    sys.modules[name] = mod
    return mod


def _load_dispatcher():
    root = Path(__file__).resolve().parents[1]
    module_path = root / "controllers" / "intent_dispatcher.py"

    class _Controller:
        pass

    class _AccessError(Exception):
        pass

    class _MissingError(Exception):
        pass

    class _AccessDenied(Exception):
        pass

    class _HttpError(Exception):
        code = 400

    http_mod = _install_module("odoo.http", request=types.SimpleNamespace())
    http_mod.Controller = _Controller
    http_mod.route = lambda *args, **kwargs: (lambda fn: fn)
    _install_module("odoo", http=http_mod)
    _install_module("odoo.exceptions", AccessError=_AccessError, MissingError=_MissingError, AccessDenied=_AccessDenied)
    werkzeug_mod = _install_module("werkzeug")
    exceptions_mod = _install_module(
        "werkzeug.exceptions",
        Unauthorized=_HttpError,
        Forbidden=_HttpError,
        BadRequest=_HttpError,
        NotFound=_HttpError,
    )
    werkzeug_mod.exceptions = exceptions_mod

    _install_module("odoo.addons")
    smart_core_mod = _install_module("odoo.addons.smart_core")
    controllers_mod = _install_module("odoo.addons.smart_core.controllers")
    core_mod = _install_module("odoo.addons.smart_core.core")
    security_mod = _install_module("odoo.addons.smart_core.security")
    utils_mod = _install_module("odoo.addons.smart_core.utils")
    smart_core_mod.__path__ = [str(root)]
    controllers_mod.__path__ = [str(root / "controllers")]
    core_mod.__path__ = [str(root / "core")]
    security_mod.__path__ = [str(root / "security")]
    utils_mod.__path__ = [str(root / "utils")]

    _install_module("odoo.addons.smart_core.core.intent_router", route_intent_payload=lambda payload, ctx: {})
    _install_module("odoo.addons.smart_core.security.intent_permission", check_intent_permission=lambda ctx: True)
    _install_module("odoo.addons.smart_core.core.trace", get_trace_id=lambda headers: "trace")
    _install_module(
        "odoo.addons.smart_core.core.exceptions",
        BAD_REQUEST="BAD_REQUEST",
        AUTH_REQUIRED="AUTH_REQUIRED",
        PERMISSION_DENIED="PERMISSION_DENIED",
        INTENT_NOT_FOUND="INTENT_NOT_FOUND",
        INTERNAL_ERROR="INTERNAL_ERROR",
        map_http_status_to_code=lambda status: {403: "PERMISSION_DENIED", 404: "INTENT_NOT_FOUND", 500: "INTERNAL_ERROR"}.get(status, "INTERNAL_ERROR"),
        build_error_envelope=lambda **kwargs: {"ok": False, "error": {"code": kwargs.get("code"), "message": kwargs.get("message")}},
    )
    _install_module(
        "odoo.addons.smart_core.utils.reason_codes",
        REASON_PERMISSION_DENIED="permission_denied",
        failure_meta_for_reason=lambda reason: {"reason": reason},
    )

    _install_module("odoo.addons.smart_core.core.context", RequestContext=type("RequestContext", (), {}))

    for rel in ("intent_operation_policy", "http_result_policy", "intent_access_policy"):
        name = f"odoo.addons.smart_core.core.{rel}"
        sys.modules.pop(name, None)
        spec = importlib.util.spec_from_file_location(name, root / "core" / f"{rel}.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)

    name = "odoo.addons.smart_core.controllers.intent_dispatcher"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TestIntentDispatcherPermissionDetails(unittest.TestCase):
    def setUp(self):
        self.dispatcher = _load_dispatcher()

    def test_nested_params_preserve_model_and_operation(self):
        details = self.dispatcher._permission_error_details(
            "api.data.write",
            {"params": {"model": "x.model", "id": 7}},
            "denied",
        )

        self.assertEqual(details["model"], "x.model")
        self.assertEqual(details["op"], "write")

    def test_batch_action_keeps_legacy_batch_operation_label(self):
        details = self.dispatcher._permission_error_details(
            "api.data.batch",
            {"params": {"model": "x.model", "action": "archive"}},
            "denied",
        )

        self.assertEqual(details["model"], "x.model")
        self.assertEqual(details["op"], "batch.archive")


if __name__ == "__main__":
    unittest.main()
