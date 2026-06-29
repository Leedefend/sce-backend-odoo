# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

from odoo.addons.smart_construction_core.core_extension import smart_core_api_data_search_fields
from odoo.addons.smart_construction_core.models.support.p1_daily_business_visible_alias_fields import _alias_field_name


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

    def test_p1_visible_alias_fields_are_searchable(self):
        field_name = _alias_field_name("收款单位")
        field = self.env["tender.guarantee"]._fields[field_name]

        self.assertTrue(field.search)

    def test_direct_acceptance_legacy_visible_fields_are_searchable(self):
        field = self.env["sc.legacy.direct.acceptance.fact"]._fields["legacy_visible_05"]

        self.assertTrue(field.search)
