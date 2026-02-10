# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.handlers.scene_package import (
    ScenePackageDryRunImportHandler,
    ScenePackageExportHandler,
    ScenePackageImportHandler,
)


@tagged("sc_smoke", "scene_package_backend")
class TestScenePackagePayloadBackend(TransactionCase):
    def test_export_accepts_flat_payload(self):
        handler = ScenePackageExportHandler(self.env, payload={})

        class _Svc:
            def export_package(self, package_name, package_version, scene_channel="stable", reason="", trace_id=None):
                return {
                    "action": "package_export",
                    "package_name": package_name,
                    "package_version": package_version,
                    "scene_channel": scene_channel,
                }

        with patch("odoo.addons.smart_core.handlers.scene_package._service", return_value=_Svc()):
            result = handler.handle(
                {
                    "package_name": "snapshot.pkg",
                    "package_version": "0.0.1",
                    "scene_channel": "stable",
                    "reason": "snapshot",
                }
            )
        self.assertTrue(result.get("ok"))
        self.assertEqual((result.get("data") or {}).get("action"), "package_export")

    def test_dry_run_import_accepts_flat_payload(self):
        handler = ScenePackageDryRunImportHandler(self.env, payload={})

        class _Svc:
            def dry_run_import(self, package_json):
                return {"dry_run": True, "summary": {"scene_count": len((package_json or {}).get("scenes") or [])}}

        with patch("odoo.addons.smart_core.handlers.scene_package._service", return_value=_Svc()):
            result = handler.handle({"package": {"scenes": []}})
        self.assertTrue(result.get("ok"))
        self.assertTrue((result.get("data") or {}).get("dry_run"))

    def test_import_accepts_flat_payload(self):
        handler = ScenePackageImportHandler(self.env, payload={})

        class _Svc:
            def import_package(self, package_json, strategy, reason, trace_id=None):
                return {"action": "package_import", "strategy": strategy, "summary": {"imported_count": 0}}

        with patch("odoo.addons.smart_core.handlers.scene_package._service", return_value=_Svc()):
            result = handler.handle(
                {
                    "package": {"scenes": []},
                    "strategy": "skip_existing",
                    "reason": "snapshot",
                }
            )
        self.assertTrue(result.get("ok"))
        self.assertEqual((result.get("data") or {}).get("action"), "package_import")
