# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_gate", "sc_perm", "rr_gate")
class TestRecordRuleBehaviorGate(TransactionCase):
    """P0 record rule behavior gate: verify allowed/denied boundaries on key models."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.ref("base.main_company")
        ctx = dict(
            cls.env.context,
            mail_create_nosubscribe=True,
            mail_notify_noemail=True,
            mail_auto_subscribe_no_notify=True,
            tracking_disable=True,
        )
        def _ctx(model):
            return cls.env[model].with_context(ctx)

        def _create_user(login, group_xmlids):
            groups = [(6, 0, [cls.env.ref(x).id for x in group_xmlids])]
            return cls.env["res.users"].with_context(no_reset_password=True).create(
                {
                    "name": login,
                    "login": login,
                    "email": f"{login}@example.com",
                    "company_id": company.id,
                    "company_ids": [(6, 0, [company.id])],
                    "groups_id": groups,
                }
            )

        cls.user_project_read = _create_user(
            "rr_project_read",
            ["smart_construction_core.group_sc_cap_project_read"],
        )
        cls.user_project_user = _create_user(
            "rr_project_user",
            ["smart_construction_core.group_sc_cap_project_user"],
        )
        cls.user_project_manager = _create_user(
            "rr_project_manager",
            ["smart_construction_core.group_sc_cap_project_manager"],
        )
        cls.user_finance_read = _create_user(
            "rr_finance_read",
            ["smart_construction_core.group_sc_cap_finance_read"],
        )
        cls.user_finance_user = _create_user(
            "rr_finance_user",
            ["smart_construction_core.group_sc_cap_finance_user"],
        )
        cls.user_settlement_read = _create_user(
            "rr_settlement_read",
            ["smart_construction_core.group_sc_cap_settlement_read"],
        )
        cls.user_settlement_user = _create_user(
            "rr_settlement_user",
            ["smart_construction_core.group_sc_cap_settlement_user"],
        )

        project_vals = {"privacy_visibility": "followers"}
        cls.project_read = _ctx("project.project").create(
            dict(project_vals, name="RR Project Read", user_id=cls.user_project_read.id)
        )
        cls.project_user = _ctx("project.project").create(
            dict(project_vals, name="RR Project User", user_id=cls.user_project_user.id)
        )
        cls.project_other = _ctx("project.project").create(
            dict(project_vals, name="RR Project Other", user_id=cls.user_project_manager.id)
        )
        cls.project_finance = _ctx("project.project").create(
            dict(project_vals, name="RR Project Finance", user_id=cls.user_finance_user.id)
        )
        cls.project_finance_read = _ctx("project.project").create(
            dict(project_vals, name="RR Project Finance Read", user_id=cls.user_finance_read.id)
        )
        cls.project_settlement = _ctx("project.project").create(
            dict(project_vals, name="RR Project Settlement", user_id=cls.user_settlement_user.id)
        )
        cls.project_settlement_read = _ctx("project.project").create(
            dict(project_vals, name="RR Project Settlement Read", user_id=cls.user_settlement_read.id)
        )

        cls.task_read = _ctx("project.task").create(
            {"name": "RR Task Read", "project_id": cls.project_read.id}
        )
        cls.task_user = _ctx("project.task").create(
            {"name": "RR Task User", "project_id": cls.project_user.id}
        )
        cls.task_other = _ctx("project.task").create(
            {"name": "RR Task Other", "project_id": cls.project_other.id}
        )

        cls.partner = _ctx("res.partner").create({"name": "RR Partner"})

        tax = cls.env["account.tax"].search([], limit=1)
        if not tax:
            tax = _ctx("account.tax").create(
                {
                    "name": "RR Contract Tax",
                    "amount": 0.0,
                    "amount_type": "percent",
                    "type_tax_use": "sale",
                }
            )

        def _create_contract(name, project):
            return _ctx("construction.contract").create(
                {
                    "subject": name,
                    "type": "out",
                    "project_id": project.id,
                    "partner_id": cls.partner.id,
                    "tax_id": tax.id,
                }
            )

        cls.contract_settlement_read = _create_contract(
            "RR Contract Settlement Read", cls.project_settlement_read
        )
        cls.contract_settlement_user = _create_contract(
            "RR Contract Settlement User", cls.project_settlement
        )
        cls.contract_settlement_other = _create_contract(
            "RR Contract Settlement Other", cls.project_other
        )

        cls.payment_req_read = _ctx("payment.request").create(
            {
                "project_id": cls.project_finance_read.id,
                "partner_id": cls.partner.id,
                "amount": 10.0,
                "type": "pay",
            }
        )
        cls.payment_req_user = _ctx("payment.request").create(
            {
                "project_id": cls.project_finance.id,
                "partner_id": cls.partner.id,
                "amount": 20.0,
                "type": "pay",
            }
        )
        cls.payment_req_other = _ctx("payment.request").create(
            {
                "project_id": cls.project_other.id,
                "partner_id": cls.partner.id,
                "amount": 30.0,
                "type": "pay",
            }
        )

        cls.settlement_read = _ctx("sc.settlement.order").create(
            {
                "project_id": cls.project_settlement_read.id,
                "partner_id": cls.partner.id,
                "contract_id": cls.contract_settlement_read.id,
                "line_ids": [(0, 0, {"name": "RR Line Read", "amount": 10.0})],
            }
        )
        cls.settlement_user = _ctx("sc.settlement.order").create(
            {
                "project_id": cls.project_settlement.id,
                "partner_id": cls.partner.id,
                "contract_id": cls.contract_settlement_user.id,
                "line_ids": [(0, 0, {"name": "RR Line User", "amount": 20.0})],
            }
        )
        cls.settlement_other = _ctx("sc.settlement.order").create(
            {
                "project_id": cls.project_other.id,
                "partner_id": cls.partner.id,
                "contract_id": cls.contract_settlement_other.id,
                "line_ids": [(0, 0, {"name": "RR Line Other", "amount": 30.0})],
            }
        )

        # Ensure denied records do not inherit follower-based access.
        partners = [
            cls.user_project_read.partner_id.id,
            cls.user_project_user.partner_id.id,
            cls.user_finance_read.partner_id.id,
            cls.user_finance_user.partner_id.id,
            cls.user_settlement_read.partner_id.id,
            cls.user_settlement_user.partner_id.id,
        ]
        cls.project_other.message_unsubscribe(partner_ids=partners)
        cls.task_other.message_unsubscribe(partner_ids=partners)
        cls.payment_req_other.project_id.message_unsubscribe(partner_ids=partners)
        cls.settlement_other.project_id.message_unsubscribe(partner_ids=partners)

    def _can_read(self, user, record):
        Model = self.env[record._name].with_user(user)
        return bool(Model.search_count([("id", "=", record.id)]))

    def _assert_write_allowed(self, user, record, values):
        record.with_user(user).write(values)

    def _assert_write_denied(self, user, record, values):
        with self.assertRaises(AccessError):
            record.with_user(user).write(values)

    def test_project_project_rules(self):
        # Read-only role: can read own project, cannot see others.
        self.assertTrue(self._can_read(self.user_project_read, self.project_read))
        self.assertFalse(self._can_read(self.user_project_read, self.project_other))

        # User role: can write own project, denied on others.
        self._assert_write_allowed(
            self.user_project_user, self.project_user, {"name": "RR Project User Updated"}
        )
        self._assert_write_denied(
            self.user_project_user, self.project_other, {"name": "RR Project Other Updated"}
        )

        # Manager role: can read and write all.
        self.assertTrue(self._can_read(self.user_project_manager, self.project_other))
        self._assert_write_allowed(
            self.user_project_manager, self.project_other, {"name": "RR Project Other Manager"}
        )

    def test_project_task_rules(self):
        # Read-only role: can read tasks on own project, cannot see others.
        self.assertTrue(self._can_read(self.user_project_read, self.task_read))
        self.assertFalse(self._can_read(self.user_project_read, self.task_other))

        # User role: can write tasks on own project, denied on others.
        self._assert_write_allowed(
            self.user_project_user, self.task_user, {"name": "RR Task User Updated"}
        )
        self._assert_write_denied(
            self.user_project_user, self.task_other, {"name": "RR Task Other Updated"}
        )

        # Manager role: can read and write all tasks.
        self.assertTrue(self._can_read(self.user_project_manager, self.task_other))
        self._assert_write_allowed(
            self.user_project_manager, self.task_other, {"name": "RR Task Other Manager"}
        )

    def test_payment_request_rules(self):
        # Finance read: can read own project, cannot see others.
        self.assertTrue(self._can_read(self.user_finance_read, self.payment_req_read))
        self.assertFalse(self._can_read(self.user_finance_read, self.payment_req_other))

        # Finance user: can write own project, denied on others.
        self._assert_write_allowed(
            self.user_finance_user,
            self.payment_req_user,
            {"note": "RR Payment User Updated"},
        )
        self._assert_write_denied(
            self.user_finance_user,
            self.payment_req_other,
            {"note": "RR Payment Other Updated"},
        )

    def test_settlement_order_rules(self):
        # Settlement read: can read own project, cannot see others.
        self.assertTrue(self._can_read(self.user_settlement_read, self.settlement_read))
        self.assertFalse(self._can_read(self.user_settlement_read, self.settlement_other))

        # Settlement user: can write own project, denied on others.
        self._assert_write_allowed(
            self.user_settlement_user,
            self.settlement_user,
            {"note": "RR Settlement User Updated"},
        )
        self._assert_write_denied(
            self.user_settlement_user,
            self.settlement_other,
            {"note": "RR Settlement Other Updated"},
        )
