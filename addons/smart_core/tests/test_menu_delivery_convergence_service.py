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
            path or ["平台", label],
            is_admin=is_admin,
            is_business_config_admin=is_business_config_admin,
        )

    def test_business_config_visible_only_to_business_or_platform_admin(self):
        path = ["平台", "业务配置", "数据字典"]

        self.assertEqual(self._classify("数据字典", path), "hidden_business_config")
        self.assertEqual(
            self._classify("数据字典", path, is_business_config_admin=True),
            "delivery_business_config",
        )
        self.assertEqual(
            self._classify("数据字典", path, is_admin=True),
            "delivery_business_config",
        )

    def test_config_center_group_is_not_ordinary_user_product_surface(self):
        path = ["平台", "配置中心", "客户"]

        self.assertEqual(self._classify("客户", path), "hidden_business_config")
        self.assertEqual(
            self._classify("客户", path, is_business_config_admin=True),
            "delivery_business_config",
        )

    def test_form_field_configuration_is_business_config_surface(self):
        path = ["平台", "配置中心", "字段策略台账"]

        self.assertEqual(self._classify("字段策略台账", path), "hidden_business_config")
        self.assertEqual(
            self._classify("字段策略台账", path, is_business_config_admin=True),
            "delivery_business_config",
        )
        self.assertEqual(
            self._classify("新增表单字段", ["平台", "配置中心", "新增表单字段"], is_admin=True),
            "delivery_business_config",
        )

    def test_menu_convergence_declares_token_policy_boundary(self):
        source = self.service.source_authority_contract()
        policy_source = self.service.token_policy_source_authority_contract()

        self.assertEqual(source.get("kind"), "menu_delivery_convergence_projection")
        self.assertTrue(source.get("no_business_fact_authority"))
        self.assertEqual(source.get("token_policy"), "menu_delivery_token_policy")
        self.assertEqual(policy_source.get("kind"), "menu_delivery_token_policy")
        self.assertTrue(policy_source.get("extension_policy"))

    def test_apply_report_includes_source_authority(self):
        _fact, _explained, report = self.service.apply(
            {"tree": [], "flat": []},
            {"tree": [], "flat": []},
            is_admin=False,
        )

        self.assertEqual((report.get("source_authority") or {}).get("kind"), "menu_delivery_convergence_projection")
        self.assertEqual(
            ((report.get("token_policy_source_authority") or {}).get("kind")),
            "menu_delivery_token_policy",
        )

    def test_system_config_visible_only_to_platform_admin(self):
        path = ["平台", "系统配置", "工作流"]

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
        path = ["平台", "系统配置", "菜单项"]

        self.assertEqual(self._classify("菜单项", path, is_admin=True), "hidden_technical")

    def test_core_default_does_not_embed_construction_backend_menu_token(self):
        self.assertNotIn("项目管理（后台）", self.service.always_hidden_technical_tokens)

    def test_extension_policy_can_hide_construction_backend_menu_token(self):
        service = MenuDeliveryConvergenceService(
            token_policy={"always_hidden_technical_tokens": ["项目管理（后台）"]}
        )

        self.assertEqual(
            service._classify_leaf("项目管理（后台）", ["平台", "项目管理（后台）"], is_admin=True),
            "hidden_technical",
        )

    def test_platform_processing_entry_remains_visible_to_ordinary_user(self):
        self.assertEqual(
            self._classify("我的待办", ["平台", "我的工作", "我的待办"]),
            "delivery_user",
        )

    def test_extension_policy_can_add_business_menu_tokens(self):
        service = MenuDeliveryConvergenceService(
            token_policy={
                "user_allowed_path_tokens": ["项目管理", "项目台账"],
                "rename_labels": {"项目台账（试点）": "项目台账"},
            }
        )
        self.assertEqual(
            service._classify_leaf("项目台账", ["施工产品", "项目管理", "项目台账"], is_admin=False),
            "delivery_user",
        )
        self.assertEqual(service.rename_labels.get("项目台账（试点）"), "项目台账")
