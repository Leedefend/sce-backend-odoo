# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

from odoo.addons.smart_construction_core.core_extension import smart_core_api_data_search_fields


class TestApiDataSearchFieldsExtension(TransactionCase):
    def test_tender_guarantee_projection_search_fields_include_remark(self):
        fields = smart_core_api_data_search_fields(self.env, "tender.guarantee")

        self.assertIn("remark", fields)
        self.assertIn("legacy_visible_project_name", fields)
        self.assertIn("project_id", fields)

