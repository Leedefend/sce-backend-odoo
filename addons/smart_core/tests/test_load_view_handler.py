# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch

from odoo.exceptions import AccessError

from ..handlers.load_view import LoadModelViewHandler


class _DummyViewRecord:
    def __init__(self, view_id=None, model=None, view_type=None):
        self.id = view_id
        self.model = model
        self.type = view_type

    def exists(self):
        return bool(self.id)


class _DummyViewModel:
    def __init__(self, *, by_id=None, default_view=None):
        self.by_id = by_id or {}
        self.default_view = default_view

    def browse(self, view_id):
        return self.by_id.get(int(view_id), _DummyViewRecord())

    def search(self, _domain, limit=1):
        del limit
        return self.default_view or _DummyViewRecord()


class _DummyModel:
    def __init__(self, *, deny_read=False):
        self.deny_read = deny_read
        self.get_view_calls = []

    def with_context(self, _ctx):
        return self

    def check_access_rights(self, operation, raise_exception=False):
        if self.deny_read and operation == "read" and raise_exception:
            raise AccessError("read denied")
        return not self.deny_read

    def get_view(self, *, view_id=None, view_type=None):
        self.get_view_calls.append({"view_id": view_id, "view_type": view_type})
        return {"view_id": view_id, "view_type": view_type}


class _DummyEnv:
    def __init__(self, mapping):
        self._mapping = dict(mapping)

    def __getitem__(self, model_name):
        if model_name not in self._mapping:
            raise KeyError(model_name)
        return self._mapping[model_name]


class TestLoadViewHandler(unittest.TestCase):
    def _make_handler(self, env, su_env, params):
        return LoadModelViewHandler(env=env, su_env=su_env, context={}, payload={"params": params})

    @patch("addons.smart_core.handlers.load_view.UniversalViewSemanticParser")
    def test_load_view_uses_controlled_sudo_and_returns_data(self, parser_cls):
        user_model = _DummyModel()
        su_model = _DummyModel()
        view_model = _DummyViewModel(default_view=_DummyViewRecord(17, "project.project", "form"))
        env = _DummyEnv({"project.project": user_model})
        su_env = _DummyEnv({"project.project": su_model, "ir.ui.view": view_model})
        parser_cls.return_value.parse.return_value = {"layout": {"groups": []}}

        handler = self._make_handler(env, su_env, {"model": "project.project", "view_type": "form"})
        result = handler.run()

        self.assertTrue(result.get("ok"), result)
        self.assertEqual(result.get("data", {}).get("view_id"), 17)
        self.assertEqual(su_model.get_view_calls[0]["view_id"], 17)
        parser_cls.assert_called_once()

    @patch("addons.smart_core.handlers.load_view.UniversalViewSemanticParser")
    def test_load_view_returns_403_when_model_read_denied(self, parser_cls):
        user_model = _DummyModel(deny_read=True)
        su_model = _DummyModel()
        view_model = _DummyViewModel(default_view=_DummyViewRecord(17, "project.project", "form"))
        env = _DummyEnv({"project.project": user_model})
        su_env = _DummyEnv({"project.project": su_model, "ir.ui.view": view_model})

        handler = self._make_handler(env, su_env, {"model": "project.project", "view_type": "form"})
        result = handler.run()

        self.assertFalse(result.get("ok"), result)
        self.assertEqual(result.get("code"), 403)
        self.assertEqual((result.get("error") or {}).get("code"), "PERMISSION_DENIED")
        parser_cls.assert_not_called()

    @patch("addons.smart_core.handlers.load_view.UniversalViewSemanticParser")
    def test_load_view_returns_400_when_view_model_mismatch(self, parser_cls):
        user_model = _DummyModel()
        su_model = _DummyModel()
        view_model = _DummyViewModel(by_id={99: _DummyViewRecord(99, "res.partner", "form")})
        env = _DummyEnv({"project.project": user_model})
        su_env = _DummyEnv({"project.project": su_model, "ir.ui.view": view_model})

        handler = self._make_handler(
            env,
            su_env,
            {"model": "project.project", "view_type": "form", "view_id": 99},
        )
        result = handler.run()

        self.assertFalse(result.get("ok"), result)
        self.assertEqual(result.get("code"), 400)
        self.assertEqual((result.get("error") or {}).get("code"), "BAD_REQUEST")
        parser_cls.assert_not_called()


if __name__ == "__main__":
    unittest.main()
