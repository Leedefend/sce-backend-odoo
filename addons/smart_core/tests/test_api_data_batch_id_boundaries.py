# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, params=None, payload=None, context=None):
        self.env = env or {}
        self.params = params or {}
        self.payload = payload or {}
        self.context = context or {}


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_handler():
    root = Path(__file__).resolve().parents[1]
    exc_mod = _install_module("odoo.exceptions", AccessError=type("AccessError", (Exception,), {}))
    _install_module("odoo", exceptions=exc_mod)

    smart_core_mod = _install_module("odoo.addons.smart_core")
    handlers_mod = _install_module("odoo.addons.smart_core.handlers")
    core_mod = _install_module("odoo.addons.smart_core.core")
    utils_mod = _install_module("odoo.addons.smart_core.utils")
    _install_module("odoo.addons")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]
    utils_mod.__path__ = [str(root / "utils")]

    _install_module("odoo.addons.smart_core.core.base_handler", BaseIntentHandler=_BaseIntentHandler)
    _install_module(
        "odoo.addons.smart_core.core.project_context",
        apply_project_scope_domain=lambda env_model, domain, project_id: (domain, {"applied": False}),
        selected_project_id_from_context=lambda params, context: None,
    )
    _install_module(
        "odoo.addons.smart_core.utils.idempotency",
        apply_idempotency_identity=lambda data, **kwargs: {**data, **kwargs},
        build_idempotency_fingerprint=lambda payload, normalize_id_keys=None: "fp",
        build_idempotency_conflict_response=lambda **kwargs: {"ok": False, "error": {"code": "CONFLICT"}},
        enrich_replay_contract=lambda data, **kwargs: {**data, **kwargs},
        normalize_request_id=lambda value, prefix: value or f"{prefix}_1",
        resolve_idempotency_decision=lambda *args, **kwargs: {},
        replay_window_seconds=lambda default, env_key=None: default,
    )

    reason_name = "odoo.addons.smart_core.handlers.reason_codes"
    sys.modules.pop(reason_name, None)
    reason_spec = importlib.util.spec_from_file_location(reason_name, root / "handlers" / "reason_codes.py")
    reason_module = importlib.util.module_from_spec(reason_spec)
    sys.modules[reason_name] = reason_module
    reason_spec.loader.exec_module(reason_module)

    module_name = "odoo.addons.smart_core.handlers.api_data_batch"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "api_data_batch.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestApiDataBatchIdBoundaries(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler()

    def test_invalid_list_id_rejects_entire_batch(self):
        handler = self.module.ApiDataBatchHandler(params={"model": "x.model", "ids": [1, "bad"], "vals": {"name": "A"}})

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "ids 无效")

    def test_non_positive_id_rejects_entire_batch(self):
        handler = self.module.ApiDataBatchHandler(params={"model": "x.model", "ids": [0], "vals": {"name": "A"}})

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "ids 无效")

    def test_assign_rejects_invalid_assignee_id(self):
        handler = self.module.ApiDataBatchHandler(
            params={"model": "x.model", "ids": [1], "action": "assign", "assignee_id": "bad"}
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "assignee_id 无效")

    def test_assign_rejects_missing_assignee_id(self):
        handler = self.module.ApiDataBatchHandler(
            params={"model": "x.model", "ids": [1], "action": "assign"}
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "assignee_id 无效")


if __name__ == "__main__":
    unittest.main()
