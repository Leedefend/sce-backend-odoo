# -*- coding: utf-8 -*-
from pathlib import Path

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.core.scene_nav_contract_builder import (
    build_scene_delivery_report,
    build_scene_nav_contract,
)
from odoo.addons.smart_scene.core.nav_policy_registry import build_nav_policy_coverage_report


def _collect_scene_keys(nav_payload: dict) -> set[str]:
    out: set[str] = set()
    nav = nav_payload.get("nav") if isinstance(nav_payload, dict) else []
    root = nav[0] if isinstance(nav, list) and nav else {}
    groups = root.get("children") if isinstance(root, dict) else []
    for group in groups or []:
        for leaf in (group.get("children") or []):
            key = str(leaf.get("scene_key") or "").strip()
            if key:
                out.add(key)
    return out


def _collect_group_keys(nav_payload: dict) -> set[str]:
    out: set[str] = set()
    nav = nav_payload.get("nav") if isinstance(nav_payload, dict) else []
    root = nav[0] if isinstance(nav, list) and nav else {}
    groups = root.get("children") if isinstance(root, dict) else []
    for group in groups or []:
        key = str(group.get("key") or "").strip()
        if key:
            out.add(key)
    return out


@tagged("post_install", "-at_install", "smart_core", "scene_nav_contract")
class TestSceneNavContractBuilder(TransactionCase):
    def test_delivery_report_summary(self):
        report = build_scene_delivery_report(
            [
                {
                    "code": "default",
                    "name": "默认场景",
                    "target": {"route": "/workbench?scene=default"},
                },
                {
                    "code": "projects.list",
                    "name": "项目列表",
                    "target": {"action_xmlid": "smart_construction_core.action_sc_project_list"},
                },
            ]
        )
        self.assertEqual(report.get("scene_input_count"), 2)
        self.assertEqual(report.get("scene_count"), 1)
        self.assertEqual(report.get("excluded_scene_count"), 1)
        self.assertIn("projects.list", report.get("delivery_ready_scene_codes") or [])
        self.assertGreaterEqual(int((report.get("excluded_reason_counts") or {}).get("default_placeholder", 0)), 1)

    def test_filters_non_delivery_scenes(self):
        payload = build_scene_nav_contract(
            {
                "scenes": [
                    {
                        "code": "projects.list",
                        "name": "项目列表",
                        "target": {"action_xmlid": "smart_construction_core.action_sc_project_list"},
                    },
                    {
                        "code": "portal.dashboard",
                        "name": "工作台",
                        "portal_only": True,
                        "spa_ready": False,
                        "target": {"route": "/portal/dashboard"},
                    },
                    {
                        "code": "projects.dashboard",
                        "name": "项目驾驶舱",
                        "target": {"route": "/s/projects.dashboard"},
                    },
                    {
                        "code": "projects.dashboard_showcase",
                        "name": "项目驾驶舱（演示）",
                        "target": {"action_xmlid": "smart_construction_demo.action_project_dashboard_showcase"},
                    },
                ]
            }
        )
        scene_keys = _collect_scene_keys(payload)
        self.assertIn("projects.list", scene_keys)
        self.assertNotIn("portal.dashboard", scene_keys)
        self.assertNotIn("projects.dashboard", scene_keys)
        self.assertNotIn("projects.dashboard_showcase", scene_keys)

    def test_merges_project_group_alias(self):
        payload = build_scene_nav_contract(
            {
                "scenes": [
                    {
                        "code": "projects.list",
                        "name": "项目列表",
                        "target": {"action_xmlid": "smart_construction_core.action_sc_project_list"},
                    },
                    {
                        "code": "project.management",
                        "name": "项目驾驶舱",
                        "target": {"route": "/s/project.management"},
                    },
                ]
            }
        )
        group_keys = _collect_group_keys(payload)
        self.assertIn("group:projects", group_keys)
        self.assertNotIn("group:project", group_keys)

    def test_meta_contains_excluded_reason_stats(self):
        payload = build_scene_nav_contract(
            {
                "scenes": [
                    {
                        "code": "default",
                        "name": "默认场景",
                        "target": {"route": "/workbench?scene=default"},
                    },
                    {
                        "code": "portal.dashboard",
                        "name": "工作台",
                        "portal_only": True,
                        "spa_ready": False,
                        "target": {"route": "/portal/dashboard"},
                    },
                    {
                        "code": "projects.list",
                        "name": "项目列表",
                        "target": {"action_xmlid": "smart_construction_core.action_sc_project_list"},
                    },
                ]
            }
        )
        meta = payload.get("meta") or {}
        reason_counts = meta.get("excluded_reason_counts") or {}
        self.assertEqual(meta.get("scene_input_count"), 3)
        self.assertEqual(meta.get("scene_count"), 1)
        self.assertEqual(meta.get("excluded_scene_count"), 2)
        self.assertGreaterEqual(int(reason_counts.get("default_placeholder", 0)), 1)
        self.assertGreaterEqual(int(reason_counts.get("portal_only_not_spa_ready", 0)), 1)

    def test_meta_contains_nav_policy_diagnostics(self):
        payload = build_scene_nav_contract(
            {
                "scenes": [
                    {
                        "code": "projects.list",
                        "name": "项目列表",
                        "target": {"action_xmlid": "smart_construction_core.action_sc_project_list"},
                    },
                ]
            }
        )
        meta = payload.get("meta") or {}
        self.assertTrue(meta.get("nav_policy_provider"))
        self.assertTrue(meta.get("nav_policy_source"))
        self.assertTrue(meta.get("nav_policy_version"))
        self.assertTrue(bool(meta.get("nav_policy_validation_ok")))

    def test_nav_policy_coverage_report(self):
        report = build_nav_policy_coverage_report(base_dir=Path(__file__).resolve())
        self.assertIsInstance(report, dict)
        self.assertIn("provider_count", report)
