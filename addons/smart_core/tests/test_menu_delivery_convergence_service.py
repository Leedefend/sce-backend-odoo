# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.delivery.menu_delivery_convergence_service import MenuDeliveryConvergenceService


@tagged("post_install", "-at_install", "smart_core", "menu_delivery")
class TestMenuDeliveryConvergenceService(TransactionCase):
    def setUp(self):
        super().setUp()
        self.service = MenuDeliveryConvergenceService()

    def _classify(self, label, path=None, *, is_admin=False, is_business_config_admin=False):
        return self.service._classify_leaf(
            label,
            path or ["智能施工 2.0", label],
            is_admin=is_admin,
            is_business_config_admin=is_business_config_admin,
        )

    def test_business_config_visible_only_to_business_or_platform_admin(self):
        path = ["智能施工 2.0", "业务配置", "数据字典"]

        self.assertEqual(self._classify("数据字典", path), "hidden_business_config")
        self.assertEqual(
            self._classify("数据字典", path, is_business_config_admin=True),
            "delivery_business_config",
        )
        self.assertEqual(
            self._classify("数据字典", path, is_admin=True),
            "delivery_business_config",
        )

    def test_menu_convergence_declares_legacy_token_policy_boundary(self):
        source = self.service.source_authority_contract()
        legacy_source = self.service.legacy_token_policy_source_authority_contract()

        self.assertEqual(source.get("kind"), "menu_delivery_convergence_projection")
        self.assertTrue(source.get("no_business_fact_authority"))
        self.assertEqual(source.get("legacy_token_policy"), "legacy_construction_menu_token_policy")
        self.assertEqual(legacy_source.get("kind"), "legacy_construction_menu_token_policy")
        self.assertTrue(legacy_source.get("legacy_compatibility"))

    def test_apply_report_includes_source_authority(self):
        _fact, _explained, report = self.service.apply(
            {"tree": [], "flat": []},
            {"tree": [], "flat": []},
            is_admin=False,
        )

        self.assertEqual((report.get("source_authority") or {}).get("kind"), "menu_delivery_convergence_projection")
        self.assertEqual(
            ((report.get("legacy_token_policy_source_authority") or {}).get("kind")),
            "legacy_construction_menu_token_policy",
        )

    def test_system_config_visible_only_to_platform_admin(self):
        path = ["智能施工 2.0", "系统配置", "工作流"]

        self.assertEqual(self._classify("工作流", path), "hidden_governance")
        self.assertEqual(
            self._classify("工作流", path, is_business_config_admin=True),
            "hidden_governance",
        )
        self.assertEqual(
            self._classify("工作流", path, is_admin=True),
            "delivery_system_config",
        )

    def test_low_level_technical_entries_remain_hidden_for_admin_profiles(self):
        path = ["智能施工 2.0", "系统配置", "菜单项"]

        self.assertEqual(self._classify("菜单项", path, is_admin=True), "hidden_technical")

    def test_business_processing_entry_remains_visible_to_ordinary_user(self):
        self.assertEqual(
            self._classify("项目台账", ["智能施工 2.0", "项目管理", "项目台账"]),
            "delivery_user",
        )

    def test_company_operation_summary_report_remains_visible_to_user(self):
        self.assertEqual(
            self._classify("公司经营情况表", ["智能施工 2.0", "统计分析", "公司经营情况表"]),
            "delivery_user",
        )
