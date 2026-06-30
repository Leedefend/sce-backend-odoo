# -*- coding: utf-8 -*-
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.smart_construction_core.core_extension import smart_core_api_data_search_fields
from odoo.addons.smart_construction_core.models.support.p1_daily_business_visible_alias_fields import _alias_field_name


@tagged("api_data_search_fields_extension")
class TestApiDataSearchFieldsExtension(TransactionCase):
    def test_tender_guarantee_projection_search_fields_include_remark(self):
        fields = smart_core_api_data_search_fields(self.env, "tender.guarantee")

        self.assertIn("remark", fields)
        self.assertIn("legacy_visible_project_name", fields)
        self.assertIn("project_id", fields)

    def test_user_acceptance_visible_fields_contribute_source_fields(self):
        fields = smart_core_api_data_search_fields(self.env, "sc.settlement.order")

        self.assertIn("settlement_unit_id", fields)
        self.assertIn("source_created_by", fields)

    def test_search_fields_are_driven_by_explicit_contract_not_field_strings(self):
        fields = smart_core_api_data_search_fields(None, "payment.request")

        self.assertIn("accepted_amount_uppercase", fields)
        self.assertIn("legacy_visible_amount_uppercase", fields)
        self.assertIn("amount_uppercase", fields)
        self.assertEqual(
            self.env["payment.request"]._fields["accepted_amount_uppercase"].string,
            "用户确认金额大写",
        )

    def test_model_specific_override_labels_are_searchable_without_p1_labels(self):
        fields = smart_core_api_data_search_fields(None, "sc.legacy.direct.acceptance.fact")

        self.assertIn("attachment_ids", fields)
        self.assertIn("attachment_ref", fields)

    def test_runtime_search_fields_are_existing_model_fields(self):
        for model_name in (
            "payment.request",
            "tender.guarantee",
            "sc.settlement.order",
            "sc.legacy.direct.acceptance.fact",
        ):
            fields = smart_core_api_data_search_fields(self.env, model_name)
            model_fields = self.env[model_name]._fields

            self.assertTrue(fields)
            self.assertFalse([field_name for field_name in fields if field_name not in model_fields])

    def test_p1_visible_alias_fields_are_searchable(self):
        field_name = _alias_field_name("收款单位")
        field = self.env["tender.guarantee"]._fields[field_name]

        self.assertTrue(field.search)

    def test_direct_acceptance_legacy_visible_fields_are_searchable(self):
        field = self.env["sc.legacy.direct.acceptance.fact"]._fields["legacy_visible_05"]

        self.assertTrue(field.search)

    def test_contract_visible_projection_fields_have_namespaced_labels(self):
        contract_fields = self.env["construction.contract"]._fields
        legacy_visible_fields = [
            name
            for name in contract_fields
            if name.startswith("legacy_visible_")
        ]
        p1_visible_fields = [
            name
            for name in contract_fields
            if name.startswith("p1_visible_")
        ]

        self.assertTrue(legacy_visible_fields)
        self.assertTrue(p1_visible_fields)
        self.assertTrue(all(contract_fields[name].string.startswith("历史") for name in legacy_visible_fields))
        self.assertTrue(all(contract_fields[name].string.startswith("P1可见") for name in p1_visible_fields))

    def test_contract_formal_labels_are_not_taken_by_projection_fields(self):
        contract_fields = self.env["construction.contract"]._fields
        projection_fields = [
            name
            for name in contract_fields
            if name.startswith(("legacy_visible_", "p1_visible_"))
        ]
        reserved_labels = {"单据状态", "单据编号", "项目名称", "合同金额", "录入人", "录入时间", "附件"}
        duplicate_projection_labels = {
            contract_fields[name].string
            for name in projection_fields
            if contract_fields[name].string in reserved_labels
        }

        self.assertFalse(duplicate_projection_labels)

    def test_user_confirmed_projection_fields_have_namespaced_labels(self):
        contract_expense_fields = self.env["construction.contract.expense"]._fields
        formal_fields = [
            name
            for name in contract_expense_fields
            if name.startswith("uc_formal_")
        ]
        settlement_fields = self.env["sc.settlement.order"]._fields
        user_acceptance_fields = [
            name
            for name in settlement_fields
            if name.startswith("user_acceptance_")
        ]
        fuel_card_fields = self.env["sc.legacy.fuel.card.fact"]._fields
        accepted_visible_fields = [
            name
            for name in fuel_card_fields
            if name.startswith("accepted_visible_")
        ]

        self.assertTrue(formal_fields)
        self.assertTrue(user_acceptance_fields)
        self.assertTrue(accepted_visible_fields)
        self.assertTrue(all(contract_expense_fields[name].string.startswith("用户确认") for name in formal_fields))
        self.assertTrue(all(settlement_fields[name].string.startswith("用户验收") for name in user_acceptance_fields))
        self.assertTrue(all(fuel_card_fields[name].string.startswith("验收可见") for name in accepted_visible_fields))

    def test_known_duplicate_model_labels_are_namespaced(self):
        expectations = {
            "project.project": {
                "sc_partner_display_name": "关联单位显示名称",
            },
            "res.partner": {
                "sc_supplier_type_label": "供应商类型汇总",
            },
            "res.users": {
                "sc_supplier_type_label": "供应商类型汇总",
            },
            "sc.legacy.direct.acceptance.fact": {
                "attachment_ref": "历史附件引用",
            },
            "sc.legacy.payment.residual.fact": {
                "attachment_links": "历史附件链接",
            },
            "sc.material.settlement": {
                "payment_request_ids": "关联付款申请",
            },
            "sc.settlement.order": {
                "settlement_category_display": "结算分类显示",
                "settlement_stage": "结算阶段编码",
                "payment_request_ids": "关联付款申请",
            },
            "payment.request": {
                "accepted_amount_uppercase": "用户确认金额大写",
            },
        }
        for model_name, expected_fields in expectations.items():
            fields = self.env[model_name]._fields
            for field_name, expected_label in expected_fields.items():
                self.assertEqual(fields[field_name].string, expected_label)
