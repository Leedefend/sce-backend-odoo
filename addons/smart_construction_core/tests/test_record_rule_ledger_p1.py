# -*- coding: utf-8 -*-
import csv
import os

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_perm", "rr_p1")
class TestRecordRuleLedgerP1(TransactionCase):
    """P1 audit: record-rule visibility behavior for ledger models."""

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

        cls.user_finance_read = _create_user(
            "rr_ledger_fin_read",
            ["smart_construction_core.group_sc_cap_finance_read"],
        )
        cls.user_finance_user = _create_user(
            "rr_ledger_fin_user",
            ["smart_construction_core.group_sc_cap_finance_user"],
        )
        cls.user_finance_manager = _create_user(
            "rr_ledger_fin_manager",
            ["smart_construction_core.group_sc_cap_finance_manager"],
        )
        cls.user_no_access = _create_user(
            "rr_ledger_no_access",
            ["base.group_user"],
        )

        project_vals = {"privacy_visibility": "followers"}
        cls.project_same = _ctx("project.project").create(
            dict(project_vals, name="RR Ledger Project Same", user_id=cls.user_finance_user.id)
        )
        cls.project_other = _ctx("project.project").create(
            dict(project_vals, name="RR Ledger Project Other", user_id=cls.user_finance_manager.id)
        )

        cls.partner = _ctx("res.partner").create({"name": "RR Ledger Partner"})

        tax = cls.env["account.tax"].search(
            [
                ("type_tax_use", "=", "purchase"),
                ("amount_type", "=", "percent"),
                ("price_include", "=", False),
            ],
            limit=1,
        )
        if not tax:
            tax = _ctx("account.tax").create(
                {
                    "name": "RR Ledger Tax",
                    "amount": 0.0,
                    "amount_type": "percent",
                    "type_tax_use": "purchase",
                    "price_include": False,
                }
            )

        def _create_contract(name, project):
            return _ctx("construction.contract").create(
                {
                    "subject": name,
                    "type": "in",
                    "project_id": project.id,
                    "partner_id": cls.partner.id,
                    "tax_id": tax.id,
                }
            )

        cls.contract_same = _create_contract(
            "RR Ledger Contract Same", cls.project_same
        )
        cls.contract_other = _create_contract(
            "RR Ledger Contract Other", cls.project_other
        )

        cls.settlement_same = _ctx("sc.settlement.order").create(
            {
                "project_id": cls.project_same.id,
                "partner_id": cls.partner.id,
                "contract_id": cls.contract_same.id,
                "line_ids": [(0, 0, {"name": "RR Ledger Line Same", "amount": 10.0})],
            }
        )
        cls.settlement_other = _ctx("sc.settlement.order").create(
            {
                "project_id": cls.project_other.id,
                "partner_id": cls.partner.id,
                "contract_id": cls.contract_other.id,
                "line_ids": [(0, 0, {"name": "RR Ledger Line Other", "amount": 20.0})],
            }
        )

        cls.payment_req_same = _ctx("payment.request").create(
            {
                "project_id": cls.project_same.id,
                "partner_id": cls.partner.id,
                "contract_id": cls.contract_same.id,
                "settlement_id": cls.settlement_same.id,
                "amount": 10.0,
                "type": "pay",
            }
        )
        cls.payment_req_other = _ctx("payment.request").create(
            {
                "project_id": cls.project_other.id,
                "partner_id": cls.partner.id,
                "contract_id": cls.contract_other.id,
                "settlement_id": cls.settlement_other.id,
                "amount": 20.0,
                "type": "pay",
            }
        )

        cls.treasury_same = _ctx("sc.treasury.ledger").with_context(allow_ledger_auto=True).create(
            {
                "project_id": cls.project_same.id,
                "partner_id": cls.partner.id,
                "settlement_id": cls.settlement_same.id,
                "payment_request_id": cls.payment_req_same.id,
                "direction": "out",
                "amount": 10.0,
            }
        )
        cls.treasury_other = _ctx("sc.treasury.ledger").with_context(allow_ledger_auto=True).create(
            {
                "project_id": cls.project_other.id,
                "partner_id": cls.partner.id,
                "settlement_id": cls.settlement_other.id,
                "payment_request_id": cls.payment_req_other.id,
                "direction": "out",
                "amount": 20.0,
            }
        )

        partners = [
            cls.user_finance_read.partner_id.id,
            cls.user_finance_user.partner_id.id,
            cls.user_finance_manager.partner_id.id,
        ]
        cls.project_other.message_unsubscribe(partner_ids=partners)

        cls.settlement_same.sudo().write({"state": "approve"})
        cls.settlement_other.sudo().write({"state": "approve"})
        cls.env.cr.execute(
            "UPDATE payment_request SET state=%s, validation_status=%s WHERE id in %s",
            ("approved", "validated", (cls.payment_req_same.id, cls.payment_req_other.id)),
        )
        cls.env.invalidate_all()

        cls.demo_payment_ledger = cls.env["payment.ledger"].sudo().search(
            [("ref", "=like", "RR-LEDGER-P1%")],
            limit=1,
        )
        if not cls.demo_payment_ledger:
            cls.demo_payment_ledger = (
                cls.payment_req_same.sudo()
                .with_context(allow_payment_ledger_create=True)
                ._ensure_payment_ledger(ref="RR-LEDGER-P1-AUTO")
            )
        if cls.demo_payment_ledger.payment_request_id.state != "approved":
            raise AssertionError("P1 ledger sample payment.request must be approved.")

    def _can_read(self, user, record):
        Model = self.env[record._name].with_user(user)
        try:
            return bool(Model.search_count([("id", "=", record.id)]))
        except AccessError:
            return False

    def _rule_xmlids(self, model_name):
        rules = self.env["ir.rule"].sudo().search([("model_id.model", "=", model_name)])
        xmlids = []
        for rule in rules:
            xmlid = rule.get_external_id().get(rule.id) or ""
            if xmlid:
                xmlids.append(xmlid)
        return ",".join(xmlids)

    def _audit_path(self):
        repo_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir)
        )
        docs_dir = os.path.join(repo_root, "docs", "audit")
        if os.path.isdir(docs_dir):
            probe = os.path.join(docs_dir, ".write_test")
            try:
                with open(probe, "w", encoding="utf-8") as handle:
                    handle.write("ok")
                os.unlink(probe)
                return os.path.join(docs_dir, "rr_ledger_p1.csv")
            except OSError:
                pass
        return "/tmp/rr_ledger_p1.csv"

    def test_ledger_visibility_audit(self):
        rows = []

        for role, user in (
            ("finance_read", self.user_finance_read),
            ("finance_user", self.user_finance_user),
            ("finance_manager", self.user_finance_manager),
        ):
            rows.append(
                {
                    "model": "sc.treasury.ledger",
                    "role": role,
                    "same_project_read": self._can_read(user, self.treasury_same),
                    "other_project_read": self._can_read(user, self.treasury_other),
                    "rule_xmlids": self._rule_xmlids("sc.treasury.ledger"),
                    "note": "",
                }
            )

            # payment.ledger creation requires approved payment requests; audit rules only.
            rows.append(
                {
                    "model": "payment.ledger",
                    "role": role,
                    "same_project_read": self._can_read(self.user_finance_read, self.demo_payment_ledger),
                    "other_project_read": self._can_read(self.user_no_access, self.demo_payment_ledger),
                    "rule_xmlids": self._rule_xmlids("payment.ledger"),
                    "note": "no_access_user",
                }
            )

        target = self._audit_path()
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "model",
                    "role",
                    "same_project_read",
                    "other_project_read",
                    "rule_xmlids",
                    "note",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)
