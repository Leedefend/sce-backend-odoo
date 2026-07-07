# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_bundle.core_extension import (
    smart_core_resolve_startup_delivery_identity,
)


@tagged("post_install", "-at_install")
class TestStartupDeliveryIdentity(TransactionCase):
    def test_bundle_resolves_construction_identity_by_default(self):
        identity = smart_core_resolve_startup_delivery_identity(self.env, {})

        self.assertEqual(identity.get("product_key"), "construction.standard")
        self.assertEqual(identity.get("base_product_key"), "construction")
        self.assertEqual(identity.get("edition_key"), "standard")
        self.assertEqual(identity.get("source"), "smart_construction_bundle")
        self.assertTrue(identity.get("no_business_fact_authority"))

    def test_bundle_can_be_bypassed_for_other_bundle_context(self):
        identity = smart_core_resolve_startup_delivery_identity(self.env, {"sc.bundle": "platform"})

        self.assertIsNone(identity)
