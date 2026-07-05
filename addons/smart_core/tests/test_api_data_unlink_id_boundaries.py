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
    exc_mod = _install_module(
        "odoo.exceptions",
        AccessError=type("AccessError", (Exception,), {}),
        UserError=type("UserError", (Exception,), {}),
        ValidationError=type("ValidationError", (Exception,), {}),
    )
    _install_module("odoo", exceptions=exc_mod)

    _install_module("odoo.addons")
    smart_core_mod = _install_module("odoo.addons.smart_core")
    handlers_mod = _install_module("odoo.addons.smart_core.handlers")
    core_mod = _install_module("odoo.addons.smart_core.core")
    utils_mod = _install_module("odoo.addons.smart_core.utils")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]
    utils_mod.__path__ = [str(root / "utils")]

    _install_module("odoo.addons.smart_core.core.base_handler", BaseIntentHandler=_BaseIntentHandler)
    _install_module(
        "odoo.addons.smart_core.core.project_context",
        apply_business_scope_domain=lambda env_model, domain, params=None, context=None: (domain, {"applied": False}),
        apply_project_scope_domain=lambda env_model, domain, project_id: (domain, {"applied": False}),
        record_scope_denied_response=lambda meta, message="": {"ok": False, "meta": meta, "message": message},
        project_scope_denied_response=lambda meta, message="": {"ok": False, "meta": meta, "message": message},
        selected_record_context_id_from_context=lambda params, context: None,
        selected_project_id_from_context=lambda params, context: None,
    )
    _install_module(
        "odoo.addons.smart_core.utils.idempotency",
        apply_idempotency_identity=lambda data, **kwargs: {**data, **kwargs},
        build_idempotency_conflict_response=lambda **kwargs: {"ok": False},
        build_idempotency_fingerprint=lambda payload, normalize_id_keys=None: "fp",
        find_recent_audit_entry=lambda *args, **kwargs: None,
        normalize_request_id=lambda value, prefix: value or f"{prefix}_1",
        replay_window_seconds=lambda default, env_key=None: default,
    )
    _install_module(
        "odoo.addons.smart_core.utils.delete_policy",
        resolve_unlink_policy=lambda env, model, default_allowed_models=None: env.get(
            "__delete_policy__",
            {"allowed": True, "delete_mode": "unlink"},
        ),
    )

    reason_name = "odoo.addons.smart_core.utils.reason_codes"
    sys.modules.pop(reason_name, None)
    reason_spec = importlib.util.spec_from_file_location(reason_name, root / "utils" / "reason_codes.py")
    reason_module = importlib.util.module_from_spec(reason_spec)
    sys.modules[reason_name] = reason_module
    reason_spec.loader.exec_module(reason_module)

    module_name = "odoo.addons.smart_core.handlers.api_data_unlink"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "api_data_unlink.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestApiDataUnlinkIdBoundaries(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler()

    def test_invalid_list_id_rejects_unlink(self):
        handler = self.module.ApiDataUnlinkHandler(env={"x.model": object()}, params={"model": "x.model", "ids": [1, "bad"]})

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "INVALID_ID")

    def test_non_positive_id_rejects_unlink(self):
        handler = self.module.ApiDataUnlinkHandler(env={"x.model": object()}, params={"model": "x.model", "ids": [0]})

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "INVALID_ID")

    def test_partial_missing_ids_rejects_without_unlink(self):
        model = _FakeModel(existing_ids={1})
        handler = self.module.ApiDataUnlinkHandler(
            env={"x.model": model},
            params={"model": "x.model", "ids": [1, 2]},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 404)
        self.assertEqual(result["error"]["reason_code"], "NOT_FOUND")
        self.assertFalse(model.unlinked)

    def test_dry_run_checks_access_but_does_not_unlink(self):
        model = _FakeModel(existing_ids={1, 2})
        handler = self.module.ApiDataUnlinkHandler(
            env={"x.model": model},
            params={"model": "x.model", "ids": [1, 2], "dry_run": True},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertTrue(result["data"]["dry_run"])
        self.assertEqual(result["data"]["deleted_count"], 0)
        self.assertFalse(model.unlinked)

    def test_state_policy_allows_draft_record(self):
        model = _FakeModel(existing_ids={1}, states={1: "draft"})
        handler = self.module.ApiDataUnlinkHandler(
            env={
                "x.model": model,
                "__delete_policy__": {
                    "allowed": True,
                    "delete_mode": "unlink",
                    "state_field": "state",
                    "allowed_states": ["draft", "cancel"],
                },
            },
            params={"model": "x.model", "ids": [1], "dry_run": True},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertFalse(model.unlinked)

    def test_state_policy_rejects_submitted_record_without_unlink(self):
        model = _FakeModel(existing_ids={1}, states={1: "submitted"})
        handler = self.module.ApiDataUnlinkHandler(
            env={
                "x.model": model,
                "__delete_policy__": {
                    "allowed": True,
                    "delete_mode": "unlink",
                    "state_field": "state",
                    "allowed_states": ["draft", "cancel"],
                },
            },
            params={"model": "x.model", "ids": [1]},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "BUSINESS_RULE_FAILED")
        self.assertFalse(model.unlinked)


class _FakeModel:
    _fields = {"state": object()}

    def __init__(self, existing_ids, states=None):
        self.existing_ids = set(existing_ids)
        self.states = dict(states or {})
        self.unlinked = False

    def browse(self, ids):
        return _FakeRecords(self, ids)

    def check_access_rights(self, operation):
        self.access_operation = operation


class _FakeRecords:
    def __init__(self, model, ids):
        self.model = model
        self._fields = model._fields
        self.requested_ids = list(ids or [])
        self.ids = [rec_id for rec_id in self.requested_ids if rec_id in model.existing_ids]

    def exists(self):
        return self

    def __iter__(self):
        for rec_id in self.ids:
            yield _FakeRecord(rec_id, self.model.states.get(rec_id, "draft"))

    def check_access_rule(self, operation):
        self.access_rule_operation = operation

    def unlink(self):
        self.model.unlinked = True


class _FakeRecord:
    def __init__(self, rec_id, state):
        self.id = rec_id
        self.state = state


if __name__ == "__main__":
    unittest.main()
