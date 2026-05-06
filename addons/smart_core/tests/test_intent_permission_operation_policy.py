# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class AccessError(Exception):
    pass


class MissingError(Exception):
    pass


class _FakeUser:
    id = 7
    company_id = object()
    groups_id = set()


class _FakeRecordset:
    def __init__(self, model, ids):
        self.model = model
        self.ids = ids if isinstance(ids, list) else [ids]

    def exists(self):
        return self

    def __len__(self):
        return len(self.ids)

    def check_access_rule(self, mode):
        self.model.rule_modes.append(mode)


class _FakeModel:
    def __init__(self):
        self.access_modes = []
        self.rule_modes = []
        self.browsed_ids = []

    def check_access_rights(self, mode):
        self.access_modes.append(mode)

    def browse(self, ids):
        self.browsed_ids.append(ids)
        return _FakeRecordset(self, ids)


class _FakeEnv:
    def __init__(self, model):
        self.model = model
        self.user = _FakeUser()

    def __call__(self, user=None):
        self.uid = user
        return self

    def __getitem__(self, name):
        if name == "x.model":
            return self.model
        raise KeyError(name)


class _FakeRequest:
    def __init__(self, env):
        self.env = env
        self.uid = None


class _Ctx:
    def __init__(self, params):
        self.params = params
        self.user = None
        self.uid = None
        self.env = None


def _load_module(fake_request, user_provider=None):
    root = Path(__file__).resolve().parents[1]
    module_path = root / "security" / "intent_permission.py"

    odoo_mod = types.ModuleType("odoo")
    http_mod = types.ModuleType("odoo.http")
    http_mod.request = fake_request
    exc_mod = types.ModuleType("odoo.exceptions")
    exc_mod.AccessError = AccessError
    exc_mod.MissingError = MissingError

    addons_mod = types.ModuleType("odoo.addons")
    smart_core_mod = types.ModuleType("odoo.addons.smart_core")
    security_mod = types.ModuleType("odoo.addons.smart_core.security")
    auth_mod = types.ModuleType("odoo.addons.smart_core.security.auth")
    auth_mod.get_user_from_token = user_provider or (lambda: 7)

    security_mod.__path__ = [str(root / "security")]
    smart_core_mod.__path__ = [str(root)]
    addons_mod.__path__ = [str(root.parents[1])]

    sys.modules.update(
        {
            "odoo": odoo_mod,
            "odoo.http": http_mod,
            "odoo.exceptions": exc_mod,
            "odoo.addons": addons_mod,
            "odoo.addons.smart_core": smart_core_mod,
            "odoo.addons.smart_core.security": security_mod,
            "odoo.addons.smart_core.security.auth": auth_mod,
        }
    )

    name = "odoo.addons.smart_core.security.intent_permission"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TestIntentPermissionOperationPolicy(unittest.TestCase):
    def setUp(self):
        self.model = _FakeModel()
        self.env = _FakeEnv(self.model)
        self.permission = _load_module(_FakeRequest(self.env))

    def test_nested_api_data_write_uses_write_access_and_record_rule(self):
        ctx = _Ctx({"intent": "api.data.write", "params": {"model": "x.model", "id": 11}})

        self.permission.check_intent_permission(ctx)

        self.assertEqual(self.model.access_modes, ["write"])
        self.assertEqual(self.model.browsed_ids, [[11]])
        self.assertEqual(self.model.rule_modes, ["write"])
        self.assertEqual(self.permission.request.uid, 7)
        self.assertIs(ctx.env, self.env)
        self.assertIs(ctx.user, self.env.user)
        self.assertEqual(ctx.uid, 7)

    def test_existing_context_user_is_reused_without_redecoding_token(self):
        def _unexpected_auth():
            raise AssertionError("token should not be decoded twice")

        self.permission = _load_module(_FakeRequest(self.env), user_provider=_unexpected_auth)
        ctx = _Ctx({"intent": "api.data.write", "params": {"model": "x.model", "id": 12}})
        ctx.user = _FakeUser()

        self.permission.check_intent_permission(ctx)

        self.assertEqual(self.model.access_modes, ["write"])
        self.assertEqual(ctx.uid, 7)

    def test_api_data_create_uses_create_access_without_record_rule(self):
        ctx = _Ctx({"intent": "api.data.create", "params": {"model": "x.model", "vals": {"name": "A"}}})

        self.permission.check_intent_permission(ctx)

        self.assertEqual(self.model.access_modes, ["create"])
        self.assertEqual(self.model.browsed_ids, [])
        self.assertEqual(self.model.rule_modes, [])

    def test_api_data_unlink_ids_use_unlink_access_and_record_rule(self):
        ctx = _Ctx({"intent": "api.data.unlink", "params": {"model": "x.model", "ids": [2, "3"]}})

        self.permission.check_intent_permission(ctx)

        self.assertEqual(self.model.access_modes, ["unlink"])
        self.assertEqual(self.model.browsed_ids, [[2, 3]])
        self.assertEqual(self.model.rule_modes, ["unlink"])

    def test_batch_archive_is_write_policy(self):
        ctx = _Ctx({"intent": "api.data.batch", "params": {"model": "x.model", "action": "archive", "ids": [9]}})

        self.permission.check_intent_permission(ctx)

        self.assertEqual(self.model.access_modes, ["write"])
        self.assertEqual(self.model.rule_modes, ["write"])

    def test_non_api_write_intent_uses_write_policy_when_model_is_present(self):
        ctx = _Ctx({"intent": "execute_button", "params": {"model": "x.model", "record_id": 4}})

        self.permission.check_intent_permission(ctx)

        self.assertEqual(self.model.access_modes, ["write"])
        self.assertEqual(self.model.rule_modes, ["write"])

    def test_capability_key_can_be_top_level_or_nested(self):
        self.assertEqual(
            self.permission._capability_key({"capability_key": "top"}),
            "top",
        )
        self.assertEqual(
            self.permission._capability_key({"params": {"capability": "nested"}}),
            "nested",
        )


if __name__ == "__main__":
    unittest.main()
