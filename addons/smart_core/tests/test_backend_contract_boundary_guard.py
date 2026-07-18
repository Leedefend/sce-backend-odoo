# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[3] / "scripts" / "verify" / "backend_contract_boundary_guard.py"
DOC_PATH = Path(__file__).resolve().parents[3] / "docs" / "architecture" / "backend_contract_boundaries.md"
spec = importlib.util.spec_from_file_location("backend_contract_boundary_guard", MODULE_PATH)
guard = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(guard)


class BackendContractBoundaryGuardTests(unittest.TestCase):
    def test_guard_report_is_classified_and_clean(self):
        report = guard.build_report()

        self.assertEqual(report["guard"], "backend_contract_boundary_guard")
        self.assertEqual(report["schema_version"], "1.0")
        self.assertEqual(report["error_count"], 0)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["contract_writer_count"], 5)
        self.assertEqual(report["approval_policy_writer_count"], 1)
        self.assertEqual(report["lowcoding_policy_writer_count"], 4)
        self.assertEqual(report["writer_boundary_count"], 10)
        self.assertEqual(report["writer_file_count"], 7)
        self.assertIn("addons/smart_core/handlers/form_field_configuration.py", report["writer_paths"])
        self.assertIn("addons/smart_core/handlers/menu_configuration.py", report["writer_paths"])
        self.assertEqual(
            {row["category"] for row in report["writers"]},
            {
                "business_config_contract",
                "approval_policy_runtime",
                "lowcoding_policy_runtime",
            },
        )

    def test_guard_rules_are_declared_once(self):
        rules = guard.BOUNDARY_RULES

        self.assertEqual(
            [rule["category"] for rule in rules],
            [
                "business_config_contract",
                "approval_policy_runtime",
                "lowcoding_policy_runtime",
            ],
        )
        for rule in rules:
            self.assertIn("report_key", rule)
            self.assertIn("rows_key", rule)
            self.assertIn("count_key", rule)
            self.assertTrue(callable(rule["predicate"]))
            self.assertTrue(rule["allowed"])

    def test_report_keys_match_declared_rules(self):
        report = guard.build_report()

        for rule in guard.BOUNDARY_RULES:
            self.assertIn(rule["report_key"], report)
            self.assertIn(rule["rows_key"], report)
            self.assertIn(rule["count_key"], report)
            self.assertEqual(report[rule["count_key"]], len(report[rule["rows_key"]]))
            self.assertEqual(
                sorted(row["path"] for row in report[rule["report_key"]]),
                sorted(rule["allowed"]),
            )

    def test_guard_tracks_expected_writer_boundaries(self):
        report = guard.build_report()
        by_boundary = {
            (row["path"], row["boundary"]): row
            for row in report["writers"]
        }
        allowed_by_boundary = {
            (row["path"], row["boundary"]): row
            for row in report["allowed_lowcoding_policy_runtime_writers"]
        }

        self.assertEqual(
            by_boundary[
                ("addons/smart_core/handlers/business_config_change_set.py", "atomic_lowcode_change_set_publish")
            ]["expected_source"],
            "ui.business.config.change.set",
        )
        self.assertEqual(
            by_boundary[
                ("addons/smart_core/handlers/form_field_configuration.py", "form_lowcode_runtime_config")
            ]["expected_source"],
            "smart_core.lowcode.form_field_policy",
        )
        self.assertEqual(
            by_boundary[
                ("addons/smart_core/handlers/form_field_configuration.py", "form_field_policy_runtime_configuration")
            ]["target_models"],
            ["ui.form.field.policy"],
        )
        self.assertEqual(
            by_boundary[
                ("addons/smart_core/handlers/menu_configuration.py", "menu_lowcode_runtime_config")
            ]["expected_source"],
            "smart_core.lowcode.menu_config",
        )
        self.assertEqual(
            by_boundary[
                (
                    "addons/smart_construction_core/handlers/approval_policy_configuration.py",
                    "approval_policy_runtime_configuration",
                )
            ]["expected_source"],
            "smart_core.lowcode.approval_policy",
        )
        self.assertEqual(
            allowed_by_boundary[
                (
                    "addons/smart_construction_core/models/support/product_policy_sync.py",
                    "industry_product_menu_policy_projection",
                )
            ]["layer"],
            "L2",
        )
        self.assertEqual(
            by_boundary[
                (
                    "addons/smart_construction_core/migrations/17.0.0.61/post-migration.py",
                    "industry_stale_contract_scope_cleanup_migration",
                )
            ]["expected_source"],
            "smart_construction_core.stale_contract_scope_cleanup",
        )
        self.assertEqual(
            allowed_by_boundary[
                (
                    "addons/smart_construction_core/migrations/17.0.0.61/post-migration.py",
                    "industry_product_menu_policy_baseline_migration",
                )
            ]["expected_source"],
            "smart_construction_core.config_center_label_migration",
        )
        self.assertEqual(
            allowed_by_boundary[
                ("addons/smart_core/handlers/menu_configuration.py", "menu_config_policy_runtime_configuration")
            ]["expected_source"],
            "smart_core.lowcode.menu_config",
        )

    def test_boundary_document_lists_allowed_writer_paths(self):
        report = guard.build_report()
        document = DOC_PATH.read_text(encoding="utf-8")

        for row in report["writers"]:
            self.assertIn(row["path"], document)
            self.assertIn(row["boundary"], document)
            self.assertIn(str(row["expected_source"]), document)


if __name__ == "__main__":
    unittest.main()
