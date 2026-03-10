# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.core.scene_nav_contract_builder import build_scene_nav_contract


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
                        "name": "项目管理控制台",
                        "target": {"route": "/s/project.management"},
                    },
                ]
            }
        )
        group_keys = _collect_group_keys(payload)
        self.assertIn("group:projects", group_keys)
        self.assertNotIn("group:project", group_keys)
