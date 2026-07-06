# -*- coding: utf-8 -*-
import json
import os
import tempfile

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.core.scene_delivery_policy import (
    REASON_SCENE_DELIVERY_DEEP_LINK_ONLY,
    REASON_SCENE_SURFACE_MISMATCH,
    filter_delivery_scenes,
    legacy_surface_alias_source_authority_contract,
    resolve_delivery_policy_runtime,
    source_authority_contract,
)


@tagged("post_install", "-at_install", "smart_core", "scene_delivery_policy")
class TestSceneDeliveryPolicy(TransactionCase):
    def test_runtime_defaults_to_workspace_surface_when_enabled(self):
        runtime = resolve_delivery_policy_runtime(
            None,
            {"scene_delivery_policy_enabled": True},
        )
        self.assertTrue(bool(runtime.get("enabled")))
        self.assertEqual(runtime.get("surface"), "workspace_default_v1")

    def test_scene_delivery_policy_declares_projection_boundary(self):
        source = source_authority_contract()

        self.assertEqual(source.get("kind"), "scene_delivery_policy_projection")
        self.assertTrue(source.get("projection_only"))
        self.assertTrue(source.get("no_business_fact_authority"))
        self.assertEqual(source.get("legacy_surface_alias_source"), "legacy_scene_surface_alias_projection")
        legacy_source = legacy_surface_alias_source_authority_contract()
        self.assertEqual(legacy_source.get("kind"), "legacy_scene_surface_alias_projection")
        self.assertTrue(legacy_source.get("legacy_compatibility"))

    def test_workspace_surface_alias_is_reported_in_runtime_and_filter_meta(self):
        runtime = resolve_delivery_policy_runtime(
            None,
            {"scene_delivery_policy_enabled": True, "scene_surface": "workspace_pm_v1"},
        )
        alias = runtime.get("legacy_surface_alias") or {}
        self.assertEqual(runtime.get("surface"), "workspace_default_v1")
        self.assertEqual(alias.get("requested_surface"), "workspace_pm_v1")
        self.assertEqual((alias.get("source_authority") or {}).get("kind"), "legacy_scene_surface_alias_projection")

        result = filter_delivery_scenes(
            [],
            surface="workspace_pm_v1",
            role_surface={},
            enabled=False,
        )
        meta_alias = ((result.get("meta") or {}).get("legacy_surface_alias") or {})
        self.assertEqual(meta_alias.get("normalized_surface"), "workspace_default_v1")
        self.assertEqual((meta_alias.get("source_authority") or {}).get("kind"), "legacy_scene_surface_alias_projection")

    def test_workspace_surface_policy_filters_nav_and_deep_link(self):
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
            surface="workspace_pm_v1",
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
        self.assertIn(
            str((result.get("meta") or {}).get("surface_policy_source") or ""),
            {"file", "builtin"},
        )
        self.assertEqual((result.get("meta") or {}).get("surface"), "workspace_default_v1")

    def test_exec_surface_policy_filters_nav_and_deep_link(self):
        scenes = [
            {
                "code": "projects.dashboard",
                "name": "项目驾驶舱",
                "state": "published",
                "target": {"route": "/s/projects.dashboard"},
            },
            {
                "code": "projects.ledger",
                "name": "项目台账",
                "state": "published",
                "target": {"route": "/s/projects.ledger"},
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
            surface="construction_exec_v1",
            role_surface={},
            contract_mode="user",
            runtime_env="dev",
            enabled=True,
        )

        delivery_codes = {str(item.get("code") or "").strip() for item in (result.get("delivery_scenes") or [])}
        deep_link_codes = {str(item.get("code") or "").strip() for item in (result.get("deep_link_scenes") or [])}
        reason_counts = (result.get("meta") or {}).get("excluded_reason_counts") or {}

        self.assertSetEqual(delivery_codes, {"projects.dashboard"})
        self.assertSetEqual(deep_link_codes, {"projects.ledger"})
        self.assertGreaterEqual(int(reason_counts.get(REASON_SCENE_DELIVERY_DEEP_LINK_ONLY, 0)), 1)
        self.assertGreaterEqual(int(reason_counts.get(REASON_SCENE_SURFACE_MISMATCH, 0)), 1)

    def test_runtime_uses_policy_file_default_surface(self):
        fd, path = tempfile.mkstemp(prefix="scene_delivery_policy_", suffix=".json")
        os.close(fd)
        payload = {
            "version": "v1",
            "default_surface": "construction_exec_v1",
            "surfaces": {
                "construction_exec_v1": {
                    "nav_allowlist": ["projects.dashboard"],
                    "deep_link_allowlist": [],
                }
            },
        }
        old = os.environ.get("SCENE_DELIVERY_POLICY_FILE")
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(payload, ensure_ascii=False))
            os.environ["SCENE_DELIVERY_POLICY_FILE"] = path
            runtime = resolve_delivery_policy_runtime(
                None,
                {"scene_delivery_policy_enabled": True},
            )
            self.assertEqual(runtime.get("surface"), "construction_exec_v1")
        finally:
            if old is None:
                os.environ.pop("SCENE_DELIVERY_POLICY_FILE", None)
            else:
                os.environ["SCENE_DELIVERY_POLICY_FILE"] = old
            try:
                os.remove(path)
            except Exception:
                pass
