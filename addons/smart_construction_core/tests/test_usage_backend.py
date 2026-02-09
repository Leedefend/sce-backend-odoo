# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from uuid import uuid4

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.handlers.usage_export_csv import build_usage_csv
from odoo.addons.smart_construction_core.handlers.usage_report import (
    _matches_prefix,
    build_usage_report_data,
)


@tagged("sc_smoke", "usage_backend")
class TestUsageBackend(TransactionCase):
    def test_usage_report_supports_days_and_prefix_filter(self):
        Usage = self.env["sc.usage.counter"].sudo()
        company = self.env.user.company_id
        today = datetime.utcnow().date()
        day0 = today.strftime("%Y-%m-%d")
        day1 = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        marker = f"u{uuid4().hex[:8]}"
        scene_a = f"{marker}.alpha"
        scene_b = f"{marker}.beta"
        cap_a = f"{marker}.create.alpha"
        cap_b = f"{marker}.create.beta"

        Usage.bump(company, "usage.scene_open.total", 12)
        Usage.bump(company, "usage.capability_open.total", 9)
        Usage.bump(company, f"usage.scene_open.{scene_a}", 7)
        Usage.bump(company, f"usage.scene_open.{scene_b}", 5)
        Usage.bump(company, f"usage.capability_open.{cap_a}", 6)
        Usage.bump(company, f"usage.capability_open.{cap_b}", 3)
        Usage.bump(company, f"usage.scene_open.daily.{day1}", 4)
        Usage.bump(company, f"usage.scene_open.daily.{day0}", 8)
        Usage.bump(company, f"usage.capability_open.daily.{day0}", 9)

        report = build_usage_report_data(
            self.env,
            params={
                "top": 5,
                "days": 2,
                "scene_key_prefix": marker,
                "capability_key_prefix": marker,
            },
        )
        self.assertEqual(report["filters"]["days"], 2)
        self.assertEqual(len(report["daily"]["scene_open"]), 2)
        self.assertEqual(report["filters"]["scene_key_prefix"], marker)
        self.assertEqual(report["filters"]["capability_key_prefix"], marker)
        self.assertTrue(_matches_prefix(f"{marker}.x", marker))
        self.assertFalse(_matches_prefix("other.x", marker))

    def test_usage_report_role_and_user_slice(self):
        Usage = self.env["sc.usage.counter"].sudo()
        company = self.env.user.company_id
        today = datetime.utcnow().date().strftime("%Y-%m-%d")
        role_code = f"pm_{uuid4().hex[:4]}"
        user_id = 999001
        scene_key = f"slice.scene.{uuid4().hex[:4]}"
        cap_key = f"slice.cap.{uuid4().hex[:4]}"

        Usage.bump(company, f"usage.scene_open.role.{role_code}.total", 4)
        Usage.bump(company, f"usage.scene_open.role.{role_code}.{scene_key}", 3)
        Usage.bump(company, f"usage.scene_open.role.{role_code}.daily.{today}", 3)
        Usage.bump(company, f"usage.capability_open.role.{role_code}.total", 2)
        Usage.bump(company, f"usage.capability_open.role.{role_code}.{cap_key}", 2)
        Usage.bump(company, f"usage.capability_open.role.{role_code}.daily.{today}", 2)
        Usage.bump(company, f"usage.scene_open.user.{user_id}.total", 5)
        Usage.bump(company, f"usage.capability_open.user.{user_id}.total", 1)

        report = build_usage_report_data(
            self.env,
            params={"days": 1, "role_code": role_code, "user_id": user_id},
        )
        self.assertEqual(report["filters"]["role_code"], role_code)
        self.assertEqual(report["filters"]["user_id"], user_id)
        self.assertTrue(any(item["role_code"] == role_code for item in report.get("role_top") or []))
        self.assertTrue(any(item["user_id"] == user_id for item in report.get("user_top") or []))
        self.assertTrue(any(item["key"] == scene_key for item in report.get("scene_top") or []))
        self.assertTrue(any(item["key"] == cap_key for item in report.get("capability_top") or []))

    def test_usage_csv_respects_hidden_reason_filter(self):
        report = {
            "filters": {"day_from": "2026-02-01", "day_to": "2026-02-07"},
            "totals": {"scene_open_total": 10, "capability_open_total": 11},
            "scene_top": [{"key": "projects.list", "count": 4}],
            "capability_top": [{"key": "projects.create", "count": 3}],
            "daily": {
                "scene_open": [{"day": "2026-02-07", "count": 2}],
                "capability_open": [{"day": "2026-02-07", "count": 1}],
            },
        }
        visibility = {
            "summary": {"total": 2, "visible": 1, "hidden": 1},
            "reason_counts": [{"reason_code": "ROLE_SCOPE_MISMATCH", "count": 1}],
            "hidden_samples": [
                {"key": "x.a", "reason_code": "ROLE_SCOPE_MISMATCH"},
                {"key": "x.b", "reason_code": "PERMISSION_DENIED"},
            ],
        }
        csv_text = build_usage_csv(
            report=report,
            visibility=visibility,
            export_filtered_only=True,
            hidden_reason="ROLE_SCOPE_MISMATCH",
        )
        self.assertIn("x.a", csv_text)
        self.assertNotIn("x.b", csv_text)
        self.assertIn("meta,role_code,", csv_text)
