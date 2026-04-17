# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


SMART_CORE_DIR = Path(__file__).resolve().parents[1]
SERVICE_PATH = SMART_CORE_DIR / "app_config_engine" / "services" / "page_policy_service.py"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


service_module = _load_module(
    "odoo.addons.smart_core.app_config_engine.services.page_policy_service",
    SERVICE_PATH,
)


class _AllowedModel:
    def check_access_rights(self, mode, raise_exception=False):
        return True


class _FakeEnv(dict):
    def __getitem__(self, item):
        return _AllowedModel()


class TestPagePolicyService(unittest.TestCase):
    def test_restrict_form_fields_to_layout_keeps_layout_and_statusbar_fields(self):
        service = service_module.PagePolicyService(_FakeEnv(), {"res.users"})
        data = {
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "sheet",
                            "children": [
                                {"type": "field", "name": "name"},
                                {"type": "field", "name": "user_id"},
                            ],
                            "statusbar": {"field": "state"},
                        },
                    ],
                    "statusbar": {"field": "state"},
                },
                "tree": {"columns": ["name"]},
            },
            "fields": {
                "name": {"type": "char"},
                "user_id": {"type": "many2one"},
                "state": {"type": "selection"},
                "other": {"type": "char"},
            },
        }

        service.restrict_form_fields_to_layout(data)

        self.assertEqual(set(data["fields"].keys()), {"name", "user_id", "state", "other"})
        self.assertEqual(data["visible_fields"], ["name", "user_id"])
        self.assertEqual(
            data["views"]["form"]["layout"][0]["children"],
            [{"type": "field", "name": "name"}, {"type": "field", "name": "user_id"}],
        )
        self.assertEqual(data["layout_visible_fields"], ["name", "user_id"])

    def test_restrict_form_fields_to_layout_does_not_overwrite_existing_visible_fields(self):
        service = service_module.PagePolicyService(_FakeEnv(), {"res.users"})
        data = {
            "visible_fields": ["governed_name", "governed_owner_id"],
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "sheet",
                            "children": [
                                {"type": "field", "name": "name"},
                                {"type": "field", "name": "user_id"},
                            ],
                        },
                    ],
                },
            },
            "fields": {
                "name": {"type": "char"},
                "user_id": {"type": "many2one"},
                "governed_name": {"type": "char"},
                "governed_owner_id": {"type": "many2one"},
            },
        }

        service.restrict_form_fields_to_layout(data)

        self.assertEqual(data["visible_fields"], ["governed_name", "governed_owner_id"])
        self.assertEqual(data["layout_visible_fields"], ["name", "user_id"])

    def test_apply_access_policy_marks_core_relation_as_block(self):
        service = service_module.PagePolicyService(_FakeEnv(), {"res.users"})
        data = {
            "field_groups": [{"name": "core", "fields": ["partner_id"]}],
            "fields": {
                "partner_id": {
                    "relation": "res.partner",
                    "relation_entry": {"can_read": False, "reason_code": "RELATION_READ_FORBIDDEN"},
                }
            },
        }

        service.apply_access_policy(data, model_name="project.project")

        self.assertEqual(data["access_policy"]["mode"], "block")
        self.assertEqual(data["access_policy"]["reason_code"], "RELATION_READ_FORBIDDEN_CORE")


if __name__ == "__main__":
    unittest.main()
