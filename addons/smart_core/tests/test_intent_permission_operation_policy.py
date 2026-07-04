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

    def exists(self):
        return self


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


class _FakeAction:
    def __init__(self, action_id=31, name="Fake Action", groups_id=None, exists=True):
        self.id = action_id
        self.name = name
        self.groups_id = groups_id or set()
        self._exists = exists

    def exists(self):
        return self if self._exists else False


class _FakeActionModel:
    def __init__(self, action):
        self.action = action
        self.browsed_ids = []

    def sudo(self):
        return self

    def browse(self, action_id):
        self.browsed_ids.append(action_id)
        if int(action_id or 0) == self.action.id:
            return self.action
        return _FakeAction(action_id=action_id, exists=False)


class _FakeMenu:
    name = "Fake Menu"

    def __init__(self, exists=True, groups_id=None, parent_id=None):
        self._exists = exists
        self.groups_id = groups_id or set()
        self.parent_id = parent_id

    def exists(self):
        return self if self._exists else False


class _FakeMenuModel:
    def __init__(self):
        self.browsed_ids = []
        self.menu_map = {
            41: _FakeMenu(exists=True),
            42: _FakeMenu(exists=True, groups_id={3}),
        }

    def browse(self, menu_id):
        self.browsed_ids.append(menu_id)
        return self.menu_map.get(menu_id, _FakeMenu(exists=False))


class _FakeCapability:
    key = "cap.x"
    required_flag = "feature.x"


class _FakeCapabilityModel:
    def sudo(self):
        return self

    def search(self, domain, limit=1):
        del domain, limit
        return _FakeCapability()


class _FakeEntitlementModel:
    def __init__(self, effective=None):
        self.effective = effective

    def get_effective(self, company):
        del company
        return self.effective

    def _flag_enabled(self, flags, required_flag):
        return bool((flags or {}).get(required_flag))


class _FakeUserModel:
    def __init__(self, user):
        self.user = user

    def browse(self, user_id):
        return self.user if int(user_id or 0) == self.user.id else _FakeMissingUser()


class _FakeMissingUser:
    id = 0
    groups_id = set()

    def exists(self):
        return False


class _FakeModel:
    def __init__(self, name="x.model"):
        self.name = name
        self.access_modes = []
        self.rule_modes = []
        self.browsed_ids = []

    def check_access_rights(self, mode):
        self.access_modes.append(mode)

    def browse(self, ids):
        self.browsed_ids.append(ids)
        return _FakeRecordset(self, ids)


class _FakeEnv:
    def __init__(self, model, dbname="sc_demo"):
        self.model = model
        self.action = _FakeAction()
        self.generic_action_model = _FakeActionModel(self.action)
        self.client_action_model = _FakeActionModel(self.action)
        self.menu_model = _FakeMenuModel()
        self.entitlement_model = None
        self.capability_model = _FakeCapabilityModel()
        self.user = _FakeUser()
        self.uid = self.user.id
        self.context = {}
        self.cr = _FakeCursor(dbname, self)

    def __call__(self, user=None):
        self.uid = user
        return self

    def __getitem__(self, name):
        if name == self.model.name:
            return self.model
        if name == "ir.actions.actions":
            return self.generic_action_model
        if name == "ir.actions.client":
            return self.client_action_model
        if name == "ir.ui.menu":
            return self.menu_model
        if name == "res.users":
            return _FakeUserModel(self.user)
        if name == "sc.entitlement" and self.entitlement_model:
            return self.entitlement_model
        if name == "sc.capability":
            return self.capability_model
        raise KeyError(name)


class _FakeCursor:
    def __init__(self, dbname, env):
        self.dbname = dbname
        self.env = env
        self.closed = False

    def close(self):
        self.closed = True


class _FakeRegistry:
    def __init__(self, env):
        self.env = env

    def check_signaling(self):
        return None

    def cursor(self):
        return self.env.cr


class _FakeApi:
    @staticmethod
    def Environment(cr, uid, context):
        env = cr.env
        env.uid = uid
        env.context = context
        return env


class _FakeRequest:
    def __init__(self, env, registry_envs=None):
        self.env = env
        self.uid = None
        self.registry_envs = registry_envs or {}


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
    odoo_mod.api = _FakeApi
    odoo_mod.registry = lambda db: _FakeRegistry(fake_request.registry_envs[db])
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
            "odoo.api": _FakeApi,
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

    def test_api_data_permission_uses_params_db_when_request_env_db_differs(self):
        current_model = _FakeModel()
        current_env = _FakeEnv(current_model, dbname="sc_demo")
        target_model = _FakeModel()
        target_env = _FakeEnv(target_model, dbname="sc_odoo")
        self.permission = _load_module(
            _FakeRequest(current_env, registry_envs={"sc_odoo": target_env})
        )
        ctx = _Ctx({"intent": "api.data", "params": {"db": "sc_odoo", "model": "x.model"}})

        self.permission.check_intent_permission(ctx)

        self.assertEqual(current_model.access_modes, [])
        self.assertEqual(target_model.access_modes, ["read"])
        self.assertTrue(target_env.cr.closed)
        self.assertIs(ctx.env, target_env)

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

    def test_invalid_record_id_raises_missing_error_instead_of_skipping_rule_check(self):
        ctx = _Ctx({"intent": "api.data.write", "params": {"model": "x.model", "id": "bad-id"}})

        with self.assertRaises(MissingError):
            self.permission.check_intent_permission(ctx)

        self.assertEqual(self.model.access_modes, ["write"])
        self.assertEqual(self.model.browsed_ids, [])
        self.assertEqual(self.model.rule_modes, [])

    def test_invalid_ids_entry_raises_missing_error_instead_of_partial_rule_check(self):
        ctx = _Ctx({"intent": "api.data.unlink", "params": {"model": "x.model", "ids": [2, "bad-id"]}})

        with self.assertRaises(MissingError):
            self.permission.check_intent_permission(ctx)

        self.assertEqual(self.model.access_modes, ["unlink"])
        self.assertEqual(self.model.browsed_ids, [])
        self.assertEqual(self.model.rule_modes, [])

    def test_unknown_model_raises_missing_error_instead_of_key_error(self):
        ctx = _Ctx({"intent": "api.data", "params": {"model": "missing.model"}})

        with self.assertRaises(MissingError) as raised:
            self.permission.check_intent_permission(ctx)

        self.assertIn("missing.model", str(raised.exception))

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

    def test_user_view_preference_get_does_not_gate_on_target_business_model_acl(self):
        ctx = _Ctx({"intent": "user.view.preference.get", "params": {"model": "x.model", "action_id": 31}})

        self.permission.check_intent_permission(ctx)

        self.assertEqual(self.model.access_modes, [])
        self.assertEqual(self.model.browsed_ids, [])
        self.assertEqual(self.model.rule_modes, [])
        self.assertEqual(self.env.generic_action_model.browsed_ids, [31])

    def test_user_view_preference_set_does_not_gate_on_target_business_model_acl(self):
        ctx = _Ctx({"intent": "user.view.preference.set", "params": {"model": "x.model", "action_id": 31}})

        self.permission.check_intent_permission(ctx)

        self.assertEqual(self.model.access_modes, [])
        self.assertEqual(self.model.browsed_ids, [])
        self.assertEqual(self.model.rule_modes, [])
        self.assertEqual(self.env.generic_action_model.browsed_ids, [31])

    def test_business_config_low_code_writes_do_not_gate_on_target_business_model_acl(self):
        for intent_name in (
            "ui.business_config.list_search.set",
            "ui.business_config.analysis.set",
            "ui.business_config.contract.save",
            "ui.business_config.contract.publish",
            "ui.business_config.contract.rollback",
            "sc.approval_policy.config.set",
            "sc.approval_policy.steps.set",
        ):
            with self.subTest(intent_name=intent_name):
                self.model.access_modes.clear()
                self.model.browsed_ids.clear()
                self.model.rule_modes.clear()
                self.env.generic_action_model.browsed_ids.clear()
                ctx = _Ctx({"intent": intent_name, "params": {"model": "x.model", "action_id": 31}})

                self.permission.check_intent_permission(ctx)

                self.assertEqual(self.model.access_modes, [])
                self.assertEqual(self.model.browsed_ids, [])
                self.assertEqual(self.model.rule_modes, [])
                self.assertEqual(self.env.generic_action_model.browsed_ids, [31])

    def test_action_permission_resolves_generic_action_model(self):
        ctx = _Ctx({"intent": "ui.contract", "params": {"action_id": 31}})

        self.permission.check_intent_permission(ctx)

        self.assertEqual(self.env.generic_action_model.browsed_ids, [31])

    def test_action_permission_honors_action_type_model_before_generic_fallback(self):
        ctx = _Ctx({"intent": "ui.contract", "params": {"action_id": 31, "action_type": "ir.actions.client"}})

        self.permission.check_intent_permission(ctx)

        self.assertEqual(self.env.client_action_model.browsed_ids, [31])
        self.assertEqual(self.env.generic_action_model.browsed_ids, [])

    def test_invalid_menu_id_raises_missing_error_instead_of_value_error(self):
        ctx = _Ctx({"intent": "ui.contract", "params": {"menu_id": "not-a-number"}})

        with self.assertRaises(MissingError):
            self.permission.check_intent_permission(ctx)

        self.assertEqual(self.env.menu_model.browsed_ids, [])

    def test_menu_permission_normalizes_numeric_id(self):
        ctx = _Ctx({"intent": "ui.contract", "params": {"menu_id": "41"}})

        self.permission.check_intent_permission(ctx)

        self.assertEqual(self.env.menu_model.browsed_ids, [41])

    def test_synthetic_navigation_menu_id_uses_action_permission_without_menu_lookup(self):
        ctx = _Ctx({"intent": "ui.contract.v2", "params": {"menu_id": 877186421, "action_id": 31}})

        self.permission.check_intent_permission(ctx)

        self.assertEqual(self.env.menu_model.browsed_ids, [])
        self.assertEqual(self.env.generic_action_model.browsed_ids, [31])

    def test_menu_permission_denies_group_mismatch(self):
        self.env.user.groups_id = {1}
        ctx = _Ctx({"intent": "ui.contract", "params": {"menu_id": 42}})

        with self.assertRaises(AccessError):
            self.permission.check_intent_permission(ctx)

        self.assertEqual(self.env.menu_model.browsed_ids, [42])

    def test_capability_key_can_be_top_level_or_nested(self):
        self.assertEqual(
            self.permission._capability_key({"capability_key": "top"}),
            "top",
        )
        self.assertEqual(
            self.permission._capability_key({"params": {"capability": "nested"}}),
            "nested",
        )

    def test_missing_effective_entitlement_denies_required_capability_without_attribute_error(self):
        self.env.entitlement_model = _FakeEntitlementModel(effective=None)
        ctx = _Ctx({"intent": "ui.contract", "params": {"capability_key": "cap.x"}})

        with self.assertRaises(AccessError) as raised:
            self.permission.check_intent_permission(ctx)

        self.assertIn("FEATURE_DISABLED", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
