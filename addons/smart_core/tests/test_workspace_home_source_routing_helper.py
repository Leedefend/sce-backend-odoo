# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "workspace_home_source_routing_helper.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("workspace_home_source_routing_helper_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
is_risk_semantic_action = TARGET.is_risk_semantic_action
parse_deadline = TARGET.parse_deadline
provider_token_set = TARGET.provider_token_set
route_scene_by_source = TARGET.route_scene_by_source


class _Provider:
    @staticmethod
    def build_risk_semantic_tokens():
        return ["invoice", "approval"]

    @staticmethod
    def resolve_scene_by_source(source_key):
        if "special" in source_key:
            return "workspace.special"
        return ""


def _workspace_scene(name: str) -> str:
    aliases = {
        "default": "workspace.home",
        "risk_center": "workspace.risk",
        "task_center": "workspace.tasks",
        "cost_center": "workspace.cost",
        "project_list": "workspace.list",
    }
    return aliases.get(name, name)


class TestWorkspaceHomeSourceRoutingHelper(unittest.TestCase):
    def test_provider_token_set_prefers_keyword_override(self):
        tokens = provider_token_set(
            "build_risk_semantic_tokens",
            ["risk"],
            keyword_overrides={"token_sets": {"build_risk_semantic_tokens": ["blocked", "urgent"]}},
            provider=_Provider(),
        )

        self.assertEqual(tokens, ("blocked", "urgent"))

    def test_is_risk_semantic_action_uses_provider_tokens(self):
        self.assertTrue(
            is_risk_semantic_action(
                "overview",
                {"title": "Approval Queue"},
                {},
                provider=_Provider(),
            )
        )

    def test_route_scene_by_source_uses_provider_then_fallback(self):
        self.assertEqual(
            route_scene_by_source(
                "special_source",
                workspace_scene_resolver=_workspace_scene,
                provider=_Provider(),
            ),
            "workspace.special",
        )
        self.assertEqual(
            route_scene_by_source(
                "risk_board",
                workspace_scene_resolver=_workspace_scene,
            ),
            "workspace.risk",
        )

    def test_parse_deadline_supports_iso_and_blank(self):
        self.assertIsNotNone(parse_deadline("2026-03-28T12:00:00Z"))
        self.assertIsNone(parse_deadline(""))


if __name__ == "__main__":
    unittest.main()
