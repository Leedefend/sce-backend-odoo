# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_smoke")
class TestSeedTaxDefaults(TransactionCase):
    def test_tax_defaults_seeded(self):
        env = self.env
        company = env.company

        expected_taxes = [
            ("smart_construction_seed.tax_1", "1%", 1.0),
            ("smart_construction_seed.tax_3", "3%", 3.0),
            ("smart_construction_seed.tax_6", "6%", 6.0),
            ("smart_construction_seed.tax_9", "9%", 9.0),
            ("smart_construction_seed.tax_13", "13%", 13.0),
        ]

        for xmlid, name, amount in expected_taxes:
            tax = env.ref(xmlid, raise_if_not_found=False)
            self.assertTrue(tax, f"默认税 XMLID 未找到: {xmlid}")
            self.assertEqual(tax.name, name)
            self.assertEqual(tax.amount_type, "percent")
            self.assertFalse(tax.price_include)
            self.assertEqual(tax.type_tax_use, "none")
            self.assertEqual(tax.amount, amount)
            self.assertEqual(tax.company_id.id, company.id)
            self.assertTrue(tax.active)

        self.assertEqual(env.ref("smart_construction_seed.tax_sale_9"), env.ref("smart_construction_seed.tax_9"))
        self.assertEqual(
            env.ref("smart_construction_seed.tax_purchase_13"),
            env.ref("smart_construction_seed.tax_13"),
        )

        # 公司国家已补齐
        self.assertTrue(
            company.account_fiscal_country_id or company.partner_id.country_id,
            "公司未配置国家，seed 应已补齐",
        )

        # ICP 标记存在
        icp = env["ir.config_parameter"].sudo()
        self.assertEqual(icp.get_param("sc.seed.tax.seeded") or icp.get_param("sc.seed.tax_seeded"), "1")
