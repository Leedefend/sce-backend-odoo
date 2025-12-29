# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_smoke")
class TestSeedTaxDefaults(TransactionCase):
    def test_tax_defaults_seeded(self):
        env = self.env
        company = env.company

        sale_tax = env.ref("smart_construction_seed.tax_sale_9", raise_if_not_found=False)
        purchase_tax = env.ref("smart_construction_seed.tax_purchase_13", raise_if_not_found=False)

        for tax, amount, tax_use in (
            (sale_tax, 9.0, "sale"),
            (purchase_tax, 13.0, "purchase"),
        ):
            self.assertTrue(tax, f"默认税 XMLID 未找到: {tax_use}")
            self.assertEqual(tax.amount_type, "percent")
            self.assertFalse(tax.price_include)
            self.assertEqual(tax.type_tax_use, tax_use)
            self.assertEqual(tax.amount, amount)
            self.assertEqual(tax.company_id.id, company.id)
            self.assertTrue(tax.active)

        # 公司国家已补齐
        self.assertTrue(
            company.account_fiscal_country_id or company.partner_id.country_id,
            "公司未配置国家，seed 应已补齐",
        )

        # ICP 标记存在
        icp = env["ir.config_parameter"].sudo()
        self.assertEqual(icp.get_param("sc.seed.tax.seeded") or icp.get_param("sc.seed.tax_seeded"), "1")

