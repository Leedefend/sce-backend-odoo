# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "workspace_home_loader_helper.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("workspace_home_loader_helper_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
load_workspace_data_provider = TARGET.load_workspace_data_provider
load_workspace_scene_engine = TARGET.load_workspace_scene_engine
resolve_action_target = TARGET.resolve_action_target


class TestWorkspaceHomeLoaderHelper(unittest.TestCase):
    def test_resolve_action_target_prefers_cached_resolver(self):
        def _resolver(action_key, page_key):
            return {"kind": "scene.key", "scene_key": f"{action_key}:{page_key}"}

        payload, cached = resolve_action_target("open", "workspace.home", cached_resolver=_resolver)

        self.assertEqual(payload, {"kind": "scene.key", "scene_key": "open:workspace.home"})
        self.assertIs(cached, _resolver)

    def test_resolve_action_target_falls_back_to_page_key(self):
        payload, cached = resolve_action_target("open", "workspace.tasks", base_path=Path("/tmp/nonexistent.py"))

        self.assertEqual(payload, {"kind": "scene.key", "scene_key": "workspace.tasks"})
        self.assertIsNone(cached)

    def test_load_workspace_data_provider_respects_cached_module(self):
        marker = object()
        self.assertIs(load_workspace_data_provider(cached_module=marker), marker)

    def test_load_workspace_scene_engine_respects_cached_module(self):
        marker = object()
        self.assertIs(load_workspace_scene_engine(cached_module=marker), marker)


if __name__ == "__main__":
    unittest.main()
