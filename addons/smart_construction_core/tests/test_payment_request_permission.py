# -*- coding: utf-8 -*-

import base64

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

    def test_business_initiator_can_submit_without_funding_baseline_acl(self):
        user = self._create_user(
            login="u_payment_initiator",
            group_xmlids=[
                "base.group_user",
                "smart_construction_core.group_sc_cap_business_initiator",
            ],
        )
        partner = self.env["res.partner"].create({"name": "Permission Vendor"})
        project = self.env["project.project"].sudo().create(
            {
                "name": "Permission Project",
                "code": "PERM-PAY",
                "funding_enabled": True,
                "user_id": user.id,
            }
        )
        project.message_subscribe(partner_ids=[user.partner_id.id])
        self.env["project.funding.baseline"].sudo().create(
            {"project_id": project.id, "total_amount": 1000.0, "state": "active"}
        )
        contract = self.env["construction.contract"].sudo().create(
            {
                "subject": "Permission Contract",
                "type": "in",
                "project_id": project.id,
                "partner_id": partner.id,
            }
        )
        request = self.env["payment.request"].sudo().create(
            {
                "name": "PERM-PAY-001",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "amount": 100.0,
                "state": "draft",
            }
        )
        self.env["ir.attachment"].sudo().create(
            {
                "name": "permission-payment.txt",
                "type": "binary",
                "datas": base64.b64encode(b"permission payment").decode("ascii"),
                "res_model": request._name,
                "res_id": request.id,
                "mimetype": "text/plain",
            }
        )

        request.with_user(user).action_submit()

        self.assertEqual(request.state, "submit")
