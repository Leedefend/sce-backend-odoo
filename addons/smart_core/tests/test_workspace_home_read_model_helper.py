# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "workspace_home_read_model_helper.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("workspace_home_read_model_helper_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
as_record_list = TARGET.as_record_list
extract_business_collections = TARGET.extract_business_collections
scene_from_route = TARGET.scene_from_route


class TestWorkspaceHomeReadModelHelper(unittest.TestCase):
    def test_scene_from_route_reads_short_scene_path(self):
        self.assertEqual(scene_from_route("/s/workspace.home"), "workspace.home")

    def test_scene_from_route_reads_scene_query_param(self):
        self.assertEqual(scene_from_route("/web?foo=1&scene=workspace.risk"), "workspace.risk")

    def test_as_record_list_supports_list_and_nested_payload(self):
        self.assertEqual(as_record_list([{"id": 1}, "x"]), [{"id": 1}])
        self.assertEqual(as_record_list({"rows": [{"id": 2}, 3]}), [{"id": 2}])

    def test_extract_business_collections_ignores_shell_keys(self):
        payload = {
            "nav": [{"id": "skip"}],
            "risk_items": [{"id": 1}],
            "project_rows": {"rows": [{"id": 2}]},
            "user": {"id": 10},
        }

        self.assertEqual(
            extract_business_collections(payload),
            {"risk_items": [{"id": 1}], "project_rows": [{"id": 2}]},
        )


if __name__ == "__main__":
    unittest.main()
