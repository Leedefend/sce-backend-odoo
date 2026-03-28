# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "workspace_home_shell_helper.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("workspace_home_shell_helper_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
build_workspace_scene_aliases = TARGET.build_workspace_scene_aliases
merge_workspace_mapping_overrides = TARGET.merge_workspace_mapping_overrides
resolve_workspace_keyword_overrides = TARGET.resolve_workspace_keyword_overrides
resolve_workspace_scene = TARGET.resolve_workspace_scene


class _Provider:
    @staticmethod
    def build_scene_aliases():
        return {" Dashboard ": "workspace.home", "Risk_Center": "workspace.risk"}

    @staticmethod
    def build_layout_texts_overrides():
        return {"hero_title": "工作台", "hero_lead": "今日优先项"}


class TestWorkspaceHomeShellHelper(unittest.TestCase):
    def test_build_workspace_scene_aliases_uses_provider_when_available(self):
        aliases = build_workspace_scene_aliases(_Provider())

        self.assertEqual(aliases["dashboard"], "workspace.home")
        self.assertEqual(aliases["risk_center"], "workspace.risk")

    def test_resolve_workspace_scene_uses_alias_or_default(self):
        aliases = {"default": "workspace.home", "dashboard": "workspace.home", "tasks": "workspace.tasks"}

        self.assertEqual(resolve_workspace_scene("Tasks", aliases), "workspace.tasks")
        self.assertEqual(resolve_workspace_scene("unknown", aliases), "workspace.home")

    def test_resolve_workspace_keyword_overrides_prefers_direct_payload(self):
        overrides = resolve_workspace_keyword_overrides(
            {
                "workspace_keyword_overrides": {"hero": "overview"},
                "ext_facts": {"workspace_keyword_overrides": {"hero": "ignored"}},
            }
        )

        self.assertEqual(overrides, {"hero": "overview"})

    def test_resolve_workspace_keyword_overrides_falls_back_to_ext_facts(self):
        overrides = resolve_workspace_keyword_overrides(
            {"ext_facts": {"workspace_keyword_overrides": {"hero": "overview"}}}
        )

        self.assertEqual(overrides, {"hero": "overview"})

    def test_merge_workspace_mapping_overrides_merges_provider_values(self):
        merged = merge_workspace_mapping_overrides(
            {"hero_title": "默认标题"},
            _Provider(),
            override_builder="build_layout_texts_overrides",
        )

        self.assertEqual(merged["hero_title"], "工作台")
        self.assertEqual(merged["hero_lead"], "今日优先项")


if __name__ == "__main__":
    unittest.main()
