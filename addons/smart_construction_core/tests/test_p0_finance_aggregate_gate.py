# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_gate")
class TestP0FinanceAggregateGate(TransactionCase):
    """P0 gate for finance aggregation paths (read_group)."""

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

        cls.user_finance_user = _create_user(
            "p0_fin_agg_user",
            ["smart_construction_core.group_sc_cap_finance_user"],
        )
        cls.user_finance_read = _create_user(
            "p0_fin_agg_read",
            ["smart_construction_core.group_sc_cap_finance_read"],
        )
        cls.user_finance_manager = _create_user(
            "p0_fin_agg_manager",
            ["smart_construction_core.group_sc_cap_finance_manager"],
        )
        cls.user_no_access = _create_user(
            "p0_fin_agg_none",
            ["base.group_user"],
        )

        cls.project_same = _ctx("project.project").create(
            {
                "name": "P0 Finance Agg Project Same",
                "privacy_visibility": "followers",
                "user_id": cls.user_finance_user.id,
            }
        )
        cls.project_same.message_subscribe(
            partner_ids=[
                cls.user_finance_user.partner_id.id,
                cls.user_finance_read.partner_id.id,
            ]
        )
        cls.project_other = _ctx("project.project").create(
            {
                "name": "P0 Finance Agg Project Other",
                "privacy_visibility": "followers",
                "user_id": cls.user_no_access.id,
            }
        )

        cls.partner = _ctx("res.partner").create({"name": "P0 Finance Agg Partner"})
        cls.partner_other = _ctx("res.partner").create(
            {"name": "P0 Finance Agg Partner Other"}
        )

        cls.settlement_same = _ctx("sc.settlement.order").create(
            {
                "project_id": cls.project_same.id,
                "partner_id": cls.partner.id,
                "line_ids": [(0, 0, {"name": "P0 Agg Line", "amount": 120.0})],
            }
        )
        cls.settlement_other = _ctx("sc.settlement.order").create(
            {
                "project_id": cls.project_other.id,
                "partner_id": cls.partner_other.id,
                "line_ids": [(0, 0, {"name": "P0 Agg Line Other", "amount": 80.0})],
            }
        )
        cls.settlement_same.write({"state": "approve"})
        cls.settlement_other.write({"state": "approve"})

        cls.payment_same = _ctx("payment.request").create(
            {
                "project_id": cls.project_same.id,
                "partner_id": cls.partner.id,
                "settlement_id": cls.settlement_same.id,
                "amount": 120.0,
                "type": "pay",
            }
        )
        cls.payment_other = _ctx("payment.request").create(
            {
                "project_id": cls.project_other.id,
                "partner_id": cls.partner_other.id,
                "settlement_id": cls.settlement_other.id,
                "amount": 80.0,
                "type": "pay",
            }
        )

        cls.env.cr.execute(
            "UPDATE payment_request SET state=%s, validation_status=%s WHERE id in %s",
            ("approved", "validated", (cls.payment_same.id, cls.payment_other.id)),
        )
        cls.env.invalidate_all()

        cls.ledger_same = cls.payment_same.sudo()._ensure_payment_ledger()
        cls.ledger_other = cls.payment_other.sudo()._ensure_payment_ledger()

        cls.treasury_same = (
            _ctx("sc.treasury.ledger")
            .with_context(allow_ledger_auto=True)
            .create(
                {
                    "project_id": cls.project_same.id,
                    "partner_id": cls.partner.id,
                    "settlement_id": cls.settlement_same.id,
                    "payment_request_id": cls.payment_same.id,
                    "amount": 120.0,
                }
            )
        )
        cls.treasury_other = (
            _ctx("sc.treasury.ledger")
            .with_context(allow_ledger_auto=True)
            .create(
                {
                    "project_id": cls.project_other.id,
                    "partner_id": cls.partner_other.id,
                    "settlement_id": cls.settlement_other.id,
                    "payment_request_id": cls.payment_other.id,
                    "amount": 80.0,
                }
            )
        )

    def _project_ids_from_groups(self, groups):
        return {g.get("project_id")[0] for g in groups if g.get("project_id")}

    def _read_group_project_ids(self, model, user):
        groups = (
            self.env[model]
            .with_user(user)
            .read_group([], ["id:count"], ["project_id"])
        )
        return self._project_ids_from_groups(groups)

    def _sum_read_group_count(self, model, user, domain, groupby="project_id"):
        groups = (
            self.env[model]
            .with_user(user)
            .read_group(domain, ["id:count"], [groupby])
        )
        total = 0
        for group in groups:
            if "__count" in group:
                total += group["__count"]
                continue
            if "id_count" in group:
                total += group["id_count"]
                continue
            for key, value in group.items():
                if key.endswith("_count") and isinstance(value, int):
                    total += value
                    break
        return total

    def _assert_aggregate_consistency(self, model, user, domain, groupby="project_id"):
        count = self.env[model].with_user(user).search_count(domain)
        rg_total = self._sum_read_group_count(model, user, domain, groupby=groupby)
        self.assertEqual(
            count,
            rg_total,
            f"aggregate mismatch on {model}: search_count={count} read_group_sum={rg_total}",
        )

    def test_read_group_denied_non_finance(self):
        for model in [
            "payment.request",
            "sc.settlement.order",
            "payment.ledger",
            "sc.treasury.ledger",
        ]:
            with self.assertRaises(AccessError):
                self._read_group_project_ids(model, self.user_no_access)

    def test_search_count_denied_non_finance(self):
        for model in [
            "payment.request",
            "sc.settlement.order",
            "payment.ledger",
            "sc.treasury.ledger",
        ]:
            with self.assertRaises(AccessError):
                self.env[model].with_user(self.user_no_access).search_count([])

    def test_read_group_scope_finance_read(self):
        expected = {self.project_same.id}
        for model in [
            "payment.request",
            "sc.settlement.order",
            "payment.ledger",
            "sc.treasury.ledger",
        ]:
            project_ids = self._read_group_project_ids(model, self.user_finance_read)
            self.assertEqual(project_ids, expected)

    def test_read_group_scope_finance_manager(self):
        expected = {self.project_same.id, self.project_other.id}
        for model in [
            "payment.request",
            "sc.settlement.order",
            "payment.ledger",
            "sc.treasury.ledger",
        ]:
            project_ids = self._read_group_project_ids(
                model, self.user_finance_manager
            )
            self.assertTrue(expected.issubset(project_ids))

    def test_aggregate_consistency_finance_read(self):
        for model in [
            "payment.request",
            "sc.settlement.order",
            "payment.ledger",
            "sc.treasury.ledger",
        ]:
            self._assert_aggregate_consistency(
                model, self.user_finance_read, [], groupby="project_id"
            )

    def test_aggregate_consistency_finance_manager(self):
        for model in [
            "payment.request",
            "sc.settlement.order",
            "payment.ledger",
            "sc.treasury.ledger",
        ]:
            self._assert_aggregate_consistency(
                model, self.user_finance_manager, [], groupby="project_id"
            )
