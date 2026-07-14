# -*- coding: utf-8 -*-
import base64

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.handlers.payment_request_approval import (
    PaymentRequestApproveHandler,
    PaymentRequestSubmitHandler,
)


@tagged(
    "post_install",
    "-at_install",
    "sc_gate",
    "e2e_fixed_journey",
    "payment_domain_permission_isolation",
)
class TestPaymentDomainPermissionIsolation(TransactionCase):
    """Fixed evidence for payment-domain entry, ORM, action and Intent boundaries."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.ref("base.main_company")
        cls.company_b = cls.env["res.company"].create(
            {
                "name": "T2 Company B",
                "currency_id": cls.company_a.currency_id.id,
                "country_id": cls.company_a.country_id.id,
            }
        )
        cls.finance_user = cls._role_user(
            "t2_finance_user",
            [
                "smart_construction_core.group_sc_cap_project_read",
                "smart_construction_core.group_sc_cap_contract_read",
                "smart_construction_core.group_sc_cap_finance_user",
                "smart_construction_core.group_sc_cap_settlement_user",
            ],
            [cls.company_a, cls.company_b],
        )
        cls.project_a_member = cls._role_user(
            "t2_project_a_member",
            [
                "smart_construction_core.group_sc_cap_project_read",
                "smart_construction_core.group_sc_cap_contract_read",
                "smart_construction_core.group_sc_cap_business_initiator",
            ],
            [cls.company_a],
        )
        cls.project_b_member = cls._role_user(
            "t2_project_b_member",
            [
                "smart_construction_core.group_sc_cap_project_read",
                "smart_construction_core.group_sc_cap_contract_read",
                "smart_construction_core.group_sc_cap_business_initiator",
            ],
            [cls.company_a],
        )
        cls.ordinary_user = cls._role_user(
            "t2_ordinary_internal_user",
            [],
            [cls.company_a],
        )

        cls.partner = cls.env["res.partner"].create({"name": "T2 Shared Supplier"})
        cls.project_a = cls._project("T2 Project A", cls.company_a)
        cls.project_b = cls._project("T2 Project B", cls.company_a)
        cls.project_c = cls._project("T2 Project C", cls.company_b)
        cls.project_a.message_subscribe(
            partner_ids=[cls.finance_user.partner_id.id, cls.project_a_member.partner_id.id]
        )
        cls.project_b.message_subscribe(partner_ids=[cls.project_b_member.partner_id.id])
        # Company switching is meaningful only if project membership itself permits C.
        cls.project_c.message_subscribe(partner_ids=[cls.finance_user.partner_id.id])

        cls.contract_a = cls._contract(cls.project_a)
        cls.contract_b = cls._contract(cls.project_b)
        cls.contract_c = cls._contract(cls.project_c)
        cls.settlement_a = cls._settlement(cls.project_a, cls.contract_a)
        cls.settlement_b = cls._settlement(cls.project_b, cls.contract_b)
        cls.settlement_c = cls._settlement(cls.project_c, cls.contract_c)
        cls.request_a = cls._request(cls.project_a, cls.contract_a, cls.settlement_a)
        cls.request_b = cls._request(cls.project_b, cls.contract_b, cls.settlement_b)
        cls.request_c = cls._request(cls.project_c, cls.contract_c, cls.settlement_c)
        cls.execution_a = cls._execution(cls.request_a)
        cls.execution_b = cls._execution(cls.request_b)
        cls.execution_c = cls._execution(cls.request_c)

    @classmethod
    def _role_user(cls, login, group_xmlids, companies):
        groups = cls.env["res.groups"].browse(
            [cls.env.ref("base.group_user").id]
            + [cls.env.ref(xmlid).id for xmlid in group_xmlids]
        )
        return cls.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": login.replace("_", " ").title(),
                "login": "%s@example.com" % login,
                "email": "%s@example.com" % login,
                "company_id": companies[0].id,
                "company_ids": [(6, 0, [company.id for company in companies])],
                "groups_id": [(6, 0, groups.ids)],
            }
        )

    @classmethod
    def _project(cls, name, company):
        return cls.env["project.project"].create(
            {
                "name": name,
                "company_id": company.id,
                "privacy_visibility": "followers",
                "user_id": cls.env.user.id,
                "manager_id": cls.env.user.id,
            }
        )

    @classmethod
    def _contract(cls, project):
        return cls.env["construction.contract"].create(
            {
                "subject": "%s Contract" % project.name,
                "type": "in",
                "project_id": project.id,
                "partner_id": cls.partner.id,
                "company_id": project.company_id.id,
                "currency_id": project.company_id.currency_id.id,
            }
        )

    @classmethod
    def _settlement(cls, project, contract):
        return cls.env["sc.settlement.order"].create(
            {
                "title": "%s Settlement" % project.name,
                "project_id": project.id,
                "partner_id": cls.partner.id,
                "contract_id": contract.id,
                "settlement_type": "out",
                "company_id": project.company_id.id,
                "currency_id": project.company_id.currency_id.id,
                "line_ids": [
                    (0, 0, {"name": "T2 fixed amount", "qty": 1.0, "price_unit": 100.0})
                ],
            }
        )

    @classmethod
    def _request(cls, project, contract, settlement, *, env=None):
        env = env or cls.env
        return env["payment.request"].create(
            {
                "type": "pay",
                "project_id": project.id,
                "partner_id": cls.partner.id,
                "contract_id": contract.id,
                "settlement_id": settlement.id,
                "amount": 100.0,
                "currency_id": project.company_id.currency_id.id,
            }
        )

    @classmethod
    def _execution(cls, request, *, env=None, overrides=None):
        env = env or cls.env
        values = {
            "project_id": request.project_id.id,
            "partner_id": request.partner_id.id,
            "contract_id": request.contract_id.id,
            "payment_request_id": request.id,
            "planned_amount": request.amount,
            "paid_amount": request.amount,
            "currency_id": request.currency_id.id,
        }
        values.update(overrides or {})
        return env["sc.payment.execution"].create(values)

    def _user_env(self, user, companies=None):
        companies = companies or [self.company_a]
        return self.env(
            user=user,
            context={**self.env.context, "allowed_company_ids": [c.id for c in companies]},
        )

    def _assert_readable_only(self, user, model_name, allowed, denied):
        model = self._user_env(user)[model_name]
        found = model.search([("id", "in", allowed.ids + denied.ids)])
        self.assertEqual(set(found.ids), set(allowed.ids))
        self.assertEqual(model.browse(allowed.id).read(["id"])[0]["id"], allowed.id)
        with self.assertRaises(AccessError):
            model.browse(denied.id).read(["id"])

    def _snapshot(self, record):
        record.invalidate_recordset()
        fields = [
            name
            for name in ("state", "amount", "project_id", "contract_id", "settlement_id", "payment_request_id")
            if name in record._fields
        ]
        return record.read(fields)[0]

    def _assert_rejected_unchanged(self, record, operation, errors=(AccessError, UserError, ValidationError)):
        before = self._snapshot(record)
        ledger_before = self.env["payment.ledger"].search_count([])
        with self.assertRaises(Exception) as caught, self.env.cr.savepoint():
            operation()
        self.assertIsInstance(caught.exception, errors)
        self.assertEqual(self._snapshot(record), before)
        self.assertEqual(self.env["payment.ledger"].search_count([]), ledger_before)

    def _assert_create_rejected_unchanged(self, model_name, operation):
        count_before = self.env[model_name].search_count([])
        ledger_before = self.env["payment.ledger"].search_count([])
        with self.assertRaises(Exception) as caught, self.env.cr.savepoint():
            operation()
        self.assertIsInstance(caught.exception, (AccessError, UserError, ValidationError))
        self.assertEqual(self.env[model_name].search_count([]), count_before)
        self.assertEqual(self.env["payment.ledger"].search_count([]), ledger_before)

    def test_01_menu_and_backend_capability_boundaries(self):
        # 1-2: finance entry is visible; an ordinary internal user has no entry.
        menu_ids = [
            self.env.ref("smart_construction_core.menu_sc_user_payment_apply_acceptance").id,
            self.env.ref("smart_construction_core.menu_sc_settlement_order").id,
            self.env.ref("smart_construction_core.menu_sc_payment_execution").id,
        ]
        finance_visible = self.env["ir.ui.menu"].with_user(self.finance_user)._visible_menu_ids()
        ordinary_visible = self.env["ir.ui.menu"].with_user(self.ordinary_user)._visible_menu_ids()
        self.assertTrue(
            set(menu_ids).issubset(finance_visible),
            "finance missing menus %s" % sorted(set(menu_ids) - set(finance_visible)),
        )
        self.assertFalse(set(menu_ids) & set(ordinary_visible))
        # 3-4: knowing a menu/action id does not bypass the target model ACL.
        self.env.ref("smart_construction_core.action_sc_payment_execution").with_user(
            self.project_a_member
        ).read(["res_model"])
        with self.assertRaises(AccessError):
            self._user_env(self.ordinary_user)["sc.payment.execution"].search([])

    def test_e2e_10_model_read_project_and_company_isolation(self):
        # 5-8: symmetric A/B project isolation for search/read/direct id access.
        for model_name, record_a, record_b in (
            ("payment.request", self.request_a, self.request_b),
            ("sc.settlement.order", self.settlement_a, self.settlement_b),
            ("sc.payment.execution", self.execution_a, self.execution_b),
        ):
            self._assert_readable_only(self.project_a_member, model_name, record_a, record_b)
            self._assert_readable_only(self.project_b_member, model_name, record_b, record_a)
        # 7: company B/C is denied even when an explicit record id is known.
        for model_name, record_c in (
            ("payment.request", self.request_c),
            ("sc.settlement.order", self.settlement_c),
            ("sc.payment.execution", self.execution_c),
        ):
            with self.assertRaises(AccessError):
                self._user_env(self.project_a_member)[model_name].browse(record_c.id).read(["id"])
        # 9: ordinary internal users have no sensitive-model ACL.
        for model_name in ("payment.request", "sc.settlement.order", "sc.payment.execution"):
            with self.assertRaises(AccessError):
                self._user_env(self.ordinary_user)[model_name].search([])
        # 10: finance sees its followed A project, not unfollowed B.
        for model_name, record_a, record_b in (
            ("payment.request", self.request_a, self.request_b),
            ("sc.settlement.order", self.settlement_a, self.settlement_b),
            ("sc.payment.execution", self.execution_a, self.execution_b),
        ):
            self._assert_readable_only(self.finance_user, model_name, record_a, record_b)

    def test_03_create_write_and_forged_links_are_rejected(self):
        env_a = self._user_env(self.project_a_member)
        # 11: a project A member cannot anchor a new request to B.
        self._assert_create_rejected_unchanged(
            "payment.request",
            lambda: self._request(self.project_b, self.contract_b, self.settlement_b, env=env_a),
        )
        # 12: an existing A request cannot be rebound to B; all anchors stay unchanged.
        before = self.request_a.read(["project_id", "contract_id", "settlement_id"])[0]
        with self.assertRaises(Exception) as caught, self.env.cr.savepoint():
            self.request_a.with_user(self.project_a_member).write({"project_id": self.project_b.id})
        self.assertIsInstance(caught.exception, (AccessError, ValidationError, UserError))
        self.assertEqual(self.request_a.read(["project_id", "contract_id", "settlement_id"])[0], before)
        # 13: mismatched request/contract anchors cannot be forged on an A execution.
        self._assert_create_rejected_unchanged(
            "sc.payment.execution",
            lambda: self._execution(
                self.request_a,
                env=env_a,
                overrides={"contract_id": self.contract_b.id},
            ),
        )
        # 14: company A context cannot create or rebind company B/C records.
        self._assert_create_rejected_unchanged(
            "payment.request",
            lambda: self._request(self.project_c, self.contract_c, self.settlement_c, env=env_a),
        )
        # 15: sudo is deliberately confined to neither role execution nor success assertions.
        self.assertNotEqual(env_a.uid, self.env.ref("base.user_root").id)

    def test_e2e_06_finance_actions_and_denial_are_atomic(self):
        # 16: finance may create and submit a request in its authorized project.
        finance_env = self._user_env(self.finance_user)
        request = self._request(self.project_a, self.contract_a, self.settlement_a, env=finance_env)
        self.env["ir.attachment"].create(
            {
                "name": "t2-payment-proof.txt",
                "type": "binary",
                "datas": base64.b64encode(b"T2 payment proof"),
                "res_model": request._name,
                "res_id": request.id,
                "mimetype": "text/plain",
            }
        )
        request.with_context(payment_soft_gate=True).action_submit()
        self.assertEqual(request.state, "submit")
        execution = self._execution(self.request_a, env=finance_env)
        self.assertEqual(execution.project_id, self.project_a)
        # 17: A member cannot submit or approve B; state remains unchanged.
        self._assert_rejected_unchanged(
            self.request_b,
            lambda: self.request_b.with_user(self.project_a_member).action_submit(),
        )
        before = self._snapshot(self.request_b)
        with self.assertRaises(AccessError):
            PaymentRequestApproveHandler(
                self._user_env(self.project_a_member), payload={}
            ).handle({"id": self.request_b.id, "request_id": "t2-approve-b"})
        self.assertEqual(self._snapshot(self.request_b), before)
        # 18: A member cannot create an execution for B.
        self._assert_create_rejected_unchanged(
            "sc.payment.execution",
            lambda: self._execution(self.request_b, env=self._user_env(self.project_a_member)),
        )
        # 19: registration/reversal against B fails without changing state or ledger.
        self._assert_rejected_unchanged(
            self.execution_b,
            lambda: self.execution_b.with_user(self.project_a_member).action_paid(),
        )
        self._assert_rejected_unchanged(
            self.execution_b,
            lambda: self.execution_b.with_user(self.project_a_member).action_cancel(),
        )

    def test_05_intent_and_model_scope_are_consistent_and_atomic(self):
        # 20-21: Intent enforces the same scope, including A context + B record id.
        before = self._snapshot(self.request_b)
        ledger_before = self.env["payment.ledger"].search_count([])
        handler = PaymentRequestSubmitHandler(
            self.env(
                user=self.finance_user,
                context={
                    **self.env.context,
                    "allowed_company_ids": [self.company_a.id],
                    "current_project_id": self.project_a.id,
                },
            ),
            payload={},
        )
        result = handler.handle({"id": self.request_b.id, "request_id": "t2-submit-b"})
        self.assertFalse(result.get("ok"))
        self.assertIn(int(result.get("code") or 0), (403, 404))
        self.assertEqual(self._snapshot(self.request_b), before)
        # 22: A record id plus B project context is rejected too.
        before_a = self._snapshot(self.request_a)
        handler = PaymentRequestSubmitHandler(
            self.env(
                user=self.finance_user,
                context={
                    **self.env.context,
                    "allowed_company_ids": [self.company_a.id],
                    "current_project_id": self.project_b.id,
                },
            ),
            payload={},
        )
        result = handler.handle({"id": self.request_a.id, "request_id": "t2-submit-a-context-b"})
        self.assertFalse(result.get("ok"))
        self.assertEqual(int(result.get("code") or 0), 403)
        # 23-24: denial is explicit and leaves state, amount, ledger and links unchanged.
        self.assertTrue((result.get("error") or {}).get("reason_code"))
        self.assertEqual(self._snapshot(self.request_b), before)
        self.assertEqual(self._snapshot(self.request_a), before_a)
        self.assertEqual(self.env["payment.ledger"].search_count([]), ledger_before)

    def test_06_cross_company_context_is_recomputed(self):
        finance_a = self._user_env(self.finance_user, [self.company_a])
        # 25-26: company A context rejects explicit company B/C ids.
        for model_name, record_c in (
            ("payment.request", self.request_c),
            ("sc.settlement.order", self.settlement_c),
            ("sc.payment.execution", self.execution_c),
        ):
            with self.assertRaises(AccessError):
                finance_a[model_name].browse(record_c.id).read(["id"])
        # 27: changing allowed companies recomputes rules and permits followed C.
        finance_b = self._user_env(self.finance_user, [self.company_b])
        for model_name, record_c in (
            ("payment.request", self.request_c),
            ("sc.settlement.order", self.settlement_c),
            ("sc.payment.execution", self.execution_c),
        ):
            self.assertEqual(finance_b[model_name].browse(record_c.id).read(["id"])[0]["id"], record_c.id)
        # 28: project membership alone cannot override allowed_company_ids.
        with self.assertRaises(AccessError):
            finance_a["project.project"].browse(self.project_c.id).read(["id"])
