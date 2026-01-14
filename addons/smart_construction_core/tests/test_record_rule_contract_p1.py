# -*- coding: utf-8 -*-
import csv
import os

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_perm", "rr_p1")
class TestRecordRuleContractP1(TransactionCase):
    """P1 audit: record-rule visibility behavior for construction.contract."""

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
        Env = cls.env.with_context(ctx)

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
            "rr_contract_project_read",
            ["smart_construction_core.group_sc_cap_project_read"],
        )
        cls.user_contract_user = _create_user(
            "rr_contract_user",
            ["smart_construction_core.group_sc_cap_contract_user"],
        )
        cls.user_contract_manager = _create_user(
            "rr_contract_manager",
            ["smart_construction_core.group_sc_cap_contract_manager"],
        )

        project_vals = {"privacy_visibility": "followers"}
        cls.project_read = Env["project.project"].create(
            dict(project_vals, name="RR Contract Project Read", user_id=cls.user_project_read.id)
        )
        cls.project_user = Env["project.project"].create(
            dict(project_vals, name="RR Contract Project User", user_id=cls.user_contract_user.id)
        )
        cls.project_other = Env["project.project"].create(
            dict(project_vals, name="RR Contract Project Other", user_id=cls.user_contract_manager.id)
        )

        cls.partner = Env["res.partner"].create({"name": "RR Contract Partner"})
        cls.tax = Env["account.tax"].create(
            {
                "name": "RR Contract VAT 9%",
                "amount": 9.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "price_include": False,
                "company_id": company.id,
            }
        )

        cls.contract_read = Env["construction.contract"].create(
            {
                "subject": "RR Contract Read",
                "type": "in",
                "project_id": cls.project_read.id,
                "partner_id": cls.partner.id,
                "tax_id": cls.tax.id,
            }
        )
        cls.contract_user = Env["construction.contract"].create(
            {
                "subject": "RR Contract User",
                "type": "in",
                "project_id": cls.project_user.id,
                "partner_id": cls.partner.id,
                "tax_id": cls.tax.id,
            }
        )
        cls.contract_other = Env["construction.contract"].create(
            {
                "subject": "RR Contract Other",
                "type": "in",
                "project_id": cls.project_other.id,
                "partner_id": cls.partner.id,
                "tax_id": cls.tax.id,
            }
        )

        partners = [
            cls.user_project_read.partner_id.id,
            cls.user_contract_user.partner_id.id,
            cls.user_contract_manager.partner_id.id,
        ]
        cls.project_other.message_unsubscribe(partner_ids=partners)

    def _can_read(self, user, record):
        Model = self.env[record._name].with_user(user)
        return bool(Model.search_count([("id", "=", record.id)]))

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
                return os.path.join(docs_dir, "rr_contract_p1.csv")
            except OSError:
                pass
        return "/tmp/rr_contract_p1.csv"

    def test_contract_read_visibility_audit(self):
        rules = self.env["ir.rule"].sudo().search([("model_id.model", "=", "construction.contract")])
        rule_xmlids = []
        for rule in rules:
            xmlid = rule.get_external_id().get(rule.id) or ""
            if xmlid:
                rule_xmlids.append(xmlid)

        rows = [
            {
                "role": "project_read",
                "same_project_read": self._can_read(self.user_project_read, self.contract_read),
                "other_project_read": self._can_read(self.user_project_read, self.contract_other),
            },
            {
                "role": "contract_user",
                "same_project_read": self._can_read(self.user_contract_user, self.contract_user),
                "other_project_read": self._can_read(self.user_contract_user, self.contract_other),
            },
            {
                "role": "contract_manager",
                "same_project_read": self._can_read(self.user_contract_manager, self.contract_user),
                "other_project_read": self._can_read(self.user_contract_manager, self.contract_other),
            },
        ]

        target = self._audit_path()
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["role", "same_project_read", "other_project_read", "rule_xmlids"],
            )
            writer.writeheader()
            for row in rows:
                row["rule_xmlids"] = ",".join(rule_xmlids)
                writer.writerow(row)
