# -*- coding: utf-8 -*-
import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "load_contract_entry_context.py"


def _load_target_module():
    sys.modules.setdefault(
        "odoo",
        SimpleNamespace(
            SUPERUSER_ID=1,
            api=SimpleNamespace(Environment=lambda *args, **kwargs: None),
        ),
    )
    spec = importlib.util.spec_from_file_location("load_contract_entry_context_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
infer_view_types_from_entry_context = TARGET.infer_view_types_from_entry_context
normalize_requested_view_types = TARGET.normalize_requested_view_types
resolve_entry_action = TARGET.resolve_entry_action
resolve_model_from_entry_context = TARGET.resolve_model_from_entry_context


class _FakeAction:
    def __init__(self, *, exists=True, name="ir.actions.act_window", res_model=None, view_mode="tree,form"):
        self._exists = exists
        self._name = name
        self.res_model = res_model
        self.view_mode = view_mode

    def exists(self):
        return self if self._exists else None


class _FakeMenu:
    def __init__(self, action=None, *, exists=True):
        self.action = action
        self._exists = exists

    def exists(self):
        return self if self._exists else None


class _FakeModelAccessor:
    def __init__(self, records):
        self._records = records

    def browse(self, record_id):
        return self._records.get(int(record_id), _FakeAction(exists=False))


class _FakeEnv:
    def __init__(self, menu_records=None, action_records=None):
        self.cr = object()
        self.context = {}
        self._models = {
            "ir.ui.menu": _FakeModelAccessor(menu_records or {}),
            "ir.actions.actions": _FakeModelAccessor(action_records or {}),
        }

    def __getitem__(self, model_name):
        return self._models[model_name]


class TestLoadContractEntryContext(unittest.TestCase):
    def test_resolve_entry_action_prefers_menu_action(self):
        menu_action = _FakeAction(res_model="project.project", view_mode="kanban,tree,form")
        env = _FakeEnv(menu_records={7: _FakeMenu(action=menu_action)})

        action = resolve_entry_action(env, su_env=env, menu_id=7, action_id=99)

        self.assertIs(action, menu_action)

    def test_resolve_model_from_entry_context_uses_action_id_fallback(self):
        action = _FakeAction(res_model="project.task", view_mode="tree,form")
        env = _FakeEnv(action_records={18: action})

        model_name = resolve_model_from_entry_context(env, su_env=env, action_id=18)

        self.assertEqual(model_name, "project.task")

    def test_infer_view_types_filters_and_deduplicates(self):
        action = _FakeAction(res_model="project.task", view_mode="kanban,tree,kanban,form,pivot")
        env = _FakeEnv(action_records={18: action})

        view_types = infer_view_types_from_entry_context(
            env,
            su_env=env,
            action_id=18,
            valid_views={"tree", "form", "kanban"},
        )

        self.assertEqual(view_types, ["kanban", "tree", "form"])

    def test_infer_view_types_returns_empty_for_non_window_action(self):
        action = _FakeAction(name="ir.actions.server", res_model="project.task", view_mode="tree,form")
        env = _FakeEnv(action_records={18: action})

        view_types = infer_view_types_from_entry_context(
            env,
            su_env=env,
            action_id=18,
            valid_views={"tree", "form"},
        )

        self.assertEqual(view_types, [])

    def test_normalize_requested_view_types_uses_inferred_default(self):
        view_types = normalize_requested_view_types(
            None,
            inferred_view_types=["kanban", "tree"],
            valid_views={"tree", "form", "kanban"},
            default_view_type="tree",
        )

        self.assertEqual(view_types, ["kanban", "tree"])

    def test_normalize_requested_view_types_rejects_invalid_values(self):
        with self.assertRaisesRegex(ValueError, "unsupported view_type: dashboard"):
            normalize_requested_view_types(
                "tree,dashboard",
                inferred_view_types=["tree"],
                valid_views={"tree", "form", "kanban"},
                default_view_type="tree",
            )


if __name__ == "__main__":
    unittest.main()
