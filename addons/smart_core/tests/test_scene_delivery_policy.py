# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.core.scene_delivery_policy import (
    REASON_SCENE_DELIVERY_DEEP_LINK_ONLY,
    REASON_SCENE_SURFACE_MISMATCH,
    filter_delivery_scenes,
    resolve_delivery_policy_runtime,
)


@tagged("post_install", "-at_install", "smart_core", "scene_delivery_policy")
class TestSceneDeliveryPolicy(TransactionCase):
    def test_runtime_defaults_to_construction_surface_when_enabled(self):
        runtime = resolve_delivery_policy_runtime(
            None,
            {"scene_delivery_policy_enabled": True},
        )
        self.assertTrue(bool(runtime.get("enabled")))
        self.assertEqual(runtime.get("surface"), "construction_pm_v1")

    def test_construction_surface_policy_filters_nav_and_deep_link(self):
        scenes = [
            {
                "code": "project.management",
                "name": "项目管理",
                "state": "published",
                "target": {"route": "/s/project.management"},
            },
            {
                "code": "finance.payment_requests",
                "name": "收付款申请",
                "state": "published",
                "target": {"route": "/s/finance.payment_requests"},
            },
            {
                "code": "unknown.scene",
                "name": "未知场景",
                "state": "published",
                "target": {"route": "/s/unknown.scene"},
            },
        ]

        result = filter_delivery_scenes(
            scenes,
            surface="construction_pm_v1",
            role_surface={},
            contract_mode="user",
            runtime_env="dev",
            enabled=True,
        )

        delivery_codes = {str(item.get("code") or "").strip() for item in (result.get("delivery_scenes") or [])}
        deep_link_codes = {str(item.get("code") or "").strip() for item in (result.get("deep_link_scenes") or [])}
        reason_counts = (result.get("meta") or {}).get("excluded_reason_counts") or {}

        self.assertSetEqual(delivery_codes, {"project.management"})
        self.assertSetEqual(deep_link_codes, {"finance.payment_requests"})
        self.assertGreaterEqual(int(reason_counts.get(REASON_SCENE_DELIVERY_DEEP_LINK_ONLY, 0)), 1)
        self.assertGreaterEqual(int(reason_counts.get(REASON_SCENE_SURFACE_MISMATCH, 0)), 1)
        self.assertTrue(bool((result.get("meta") or {}).get("surface_policy_applied")))
