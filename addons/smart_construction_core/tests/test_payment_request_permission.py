# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.handlers.payment_request_approval import (
    PaymentRequestSubmitHandler,
)


@tagged("sc_smoke", "payment_request_permission")
class TestPaymentRequestPermission(TransactionCase):
    def _create_user(self, *, login: str, group_xmlids: list[str]):
        groups = []
        for xmlid in group_xmlids:
            group = self.env.ref(xmlid, raise_if_not_found=False)
            if group:
                groups.append(group.id)
        return self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": login,
                "login": login,
                "email": f"{login}@example.com",
                "groups_id": [(6, 0, groups)],
            }
        )

    def test_submit_denied_for_non_approver(self):
        user = self._create_user(
            login="u_non_approver",
            group_xmlids=["base.group_user"],
        )
        handler = PaymentRequestSubmitHandler(self.env(user=user.id), payload={})
        with self.assertRaises(AccessError):
            handler.run(payload={"params": {"id": 1}})

    def test_submit_allowed_for_finance_approver(self):
        user = self._create_user(
            login="u_fin_approver",
            group_xmlids=["base.group_user", "smart_core.group_smart_core_finance_approver"],
        )
        handler = PaymentRequestSubmitHandler(self.env(user=user.id), payload={})
        result = handler.run(payload={"params": {}})
        self.assertIsInstance(result, dict)
        self.assertFalse(result.get("ok"))
        self.assertEqual(int(result.get("code") or 0), 400)
