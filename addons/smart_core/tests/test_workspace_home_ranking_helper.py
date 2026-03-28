# -*- coding: utf-8 -*-
import importlib.util
import unittest
from datetime import datetime, timedelta
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "workspace_home_ranking_helper.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("workspace_home_ranking_helper_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
impact_score = TARGET.impact_score
urgency_score = TARGET.urgency_score
workspace_v1_copy = TARGET.workspace_v1_copy


class _Provider:
    @staticmethod
    def build_v1_copy_overrides():
        return {"hero_title": "今日工作台"}


def _ranking_profile(role_code: str):
    return {
        "severity_weight": 60 if role_code == "pm" else 50,
        "deadline_weight": 40,
        "pending_weight": 15,
        "source_weight": 12,
        "impact_weight": 22,
    }


def _token_set(hook_name, defaults, keyword_overrides=None):
    if hook_name == "build_critical_status_tokens":
        return ("critical", "urgent")
    if hook_name == "build_warning_status_tokens":
        return ("warning",)
    return tuple(defaults)


def _is_urgent(title: str, source_key: str):
    return "risk" in f"{title} {source_key}".lower()


def _deadline_parser(value):
    if value == "tomorrow":
        return datetime.now() + timedelta(hours=12)
    return None


class TestWorkspaceHomeRankingHelper(unittest.TestCase):
    def test_workspace_v1_copy_merges_provider_overrides(self):
        merged = workspace_v1_copy({"hero_title": "默认"}, _Provider())
        self.assertEqual(merged["hero_title"], "今日工作台")

    def test_impact_score_uses_amount_and_project_count(self):
        self.assertGreaterEqual(impact_score({"amount": 1000000, "project_count": 2}), 20)

    def test_urgency_score_accounts_for_status_deadline_and_impact(self):
        score = urgency_score(
            row={"amount": 1000000, "project_count": 1, "pending_count": 2, "deadline": "tomorrow"},
            title="Risk Queue",
            source_key="risk_items",
            status_text="urgent",
            role_code="pm",
            ranking_profile_builder=_ranking_profile,
            provider_token_set_builder=_token_set,
            urgent_capability_checker=_is_urgent,
            deadline_parser=_deadline_parser,
        )
        self.assertGreater(score, 0)


if __name__ == "__main__":
    unittest.main()
