# -*- coding: utf-8 -*-
import csv
import os

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.handlers.payment_request_execute import (
    PaymentRequestExecuteHandler,
)

from .perm_matrix import PERM_MATRIX


@tagged("post_install", "-at_install", "sc_perm", "permission_isolation")
class TestPermissionProjectIsolationEvidence(TransactionCase):
    """Current evidence for role permissions, project isolation, and intent authorization."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.partner = cls.env["res.partner"].create({"name": "Permission Isolation Partner"})

        def _create_user(login, group_xmlids):
            groups = {
                cls.env.ref("base.group_user").id,
                *[cls.env.ref(xmlid).id for xmlid in group_xmlids],
            }
            return cls.env["res.users"].with_context(no_reset_password=True).create(
                {
                    "name": login,
                    "login": login,
                    "email": f"{login}@example.com",
                    "company_id": cls.company.id,
                    "company_ids": [(6, 0, [cls.company.id])],
                    "groups_id": [(6, 0, sorted(groups))],
                }
            )

        cls.users = {
            role: _create_user(f"perm_iso_{role}", config["groups"])
            for role, config in PERM_MATRIX.items()
        }
        cls.project_read_user = cls.users["project_read"]
        cls.project_user = _create_user(
            "perm_iso_project_user",
            ["smart_construction_core.group_sc_cap_project_user"],
        )
        cls.finance_read_user = cls.users["finance_read"]
        cls.finance_user = cls.users["finance_user"]
        cls.settlement_read_user = _create_user(
            "perm_iso_settlement_read",
            ["smart_construction_core.group_sc_cap_settlement_read"],
        )
        cls.settlement_user = _create_user(
            "perm_iso_settlement_user",
            ["smart_construction_core.group_sc_cap_settlement_user"],
        )

        ctx = {
            "mail_create_nosubscribe": True,
            "mail_notify_noemail": True,
            "mail_auto_subscribe_no_notify": True,
            "tracking_disable": True,
        }

        def _ctx(model):
            return cls.env[model].with_context(ctx)

        project_vals = {"privacy_visibility": "followers"}
        cls.project_read = _ctx("project.project").create(
            dict(project_vals, name="Permission Isolation Read", user_id=cls.project_read_user.id)
        )
        cls.project_user_scope = _ctx("project.project").create(
            dict(project_vals, name="Permission Isolation User", user_id=cls.project_user.id)
        )
        cls.project_finance_read = _ctx("project.project").create(
            dict(project_vals, name="Permission Isolation Finance Read", user_id=cls.finance_read_user.id)
        )
        cls.project_finance_user = _ctx("project.project").create(
            dict(project_vals, name="Permission Isolation Finance User", user_id=cls.finance_user.id)
        )
        cls.project_settlement_read = _ctx("project.project").create(
            dict(project_vals, name="Permission Isolation Settlement Read", user_id=cls.settlement_read_user.id)
        )
        cls.project_settlement_user = _ctx("project.project").create(
            dict(project_vals, name="Permission Isolation Settlement User", user_id=cls.settlement_user.id)
        )
        cls.project_other = _ctx("project.project").create(
            dict(project_vals, name="Permission Isolation Other")
        )

        cls.task_user = _ctx("project.task").create(
            {"name": "Permission Isolation Task User", "project_id": cls.project_user_scope.id}
        )
        cls.task_other = _ctx("project.task").create(
            {"name": "Permission Isolation Task Other", "project_id": cls.project_other.id}
        )

        cls.payment_read = _ctx("payment.request").create(
            {
                "project_id": cls.project_finance_read.id,
                "partner_id": cls.partner.id,
                "amount": 10.0,
                "type": "pay",
            }
        )
        cls.payment_user = _ctx("payment.request").create(
            {
                "project_id": cls.project_finance_user.id,
                "partner_id": cls.partner.id,
                "amount": 20.0,
                "type": "pay",
            }
        )
        cls.payment_other = _ctx("payment.request").create(
            {
                "project_id": cls.project_other.id,
                "partner_id": cls.partner.id,
                "amount": 30.0,
                "type": "pay",
            }
        )

        contract_read = cls._create_contract(_ctx, "Permission Isolation Settlement Read Contract", cls.project_settlement_read)
        contract_user = cls._create_contract(_ctx, "Permission Isolation Settlement User Contract", cls.project_settlement_user)
        contract_other = cls._create_contract(_ctx, "Permission Isolation Other Contract", cls.project_other)
        cls.settlement_read = cls._create_settlement(_ctx, cls.project_settlement_read, contract_read, 11.0)
        cls.settlement_user_record = cls._create_settlement(_ctx, cls.project_settlement_user, contract_user, 22.0)
        cls.settlement_other = cls._create_settlement(_ctx, cls.project_other, contract_other, 33.0)

        partner_ids = [
            cls.project_read_user.partner_id.id,
            cls.project_user.partner_id.id,
            cls.finance_read_user.partner_id.id,
            cls.finance_user.partner_id.id,
            cls.settlement_read_user.partner_id.id,
            cls.settlement_user.partner_id.id,
        ]
        for record in (
            cls.project_other,
            cls.task_other,
            cls.payment_other.project_id,
            cls.settlement_other.project_id,
        ):
            record.message_unsubscribe(partner_ids=partner_ids)

    @classmethod
    def _create_contract(cls, model_getter, subject, project):
        tax = cls.env["account.tax"].search([], limit=1)
        if not tax:
            tax = model_getter("account.tax").create(
                {
                    "name": "Permission Isolation Tax",
                    "amount": 0.0,
                    "amount_type": "percent",
                    "type_tax_use": "sale",
                    "company_id": cls.company.id,
                }
            )
        return model_getter("construction.contract").create(
            {
                "subject": subject,
                "type": "in",
                "project_id": project.id,
                "partner_id": cls.partner.id,
                "tax_id": tax.id,
            }
        )

    @classmethod
    def _create_settlement(cls, model_getter, project, contract, amount):
        return model_getter("sc.settlement.order").create(
            {
                "project_id": project.id,
                "partner_id": cls.partner.id,
                "contract_id": contract.id,
                "line_ids": [(0, 0, {"name": "Permission Isolation Settlement Line", "amount": amount})],
            }
        )

    def _audit_path(self):
        repo_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir)
        )
        docs_dir = os.path.join(repo_root, "docs", "audit")
        if os.path.isdir(docs_dir):
            return os.path.join(docs_dir, "permission_project_isolation_matrix.csv")
        return "/tmp/permission_project_isolation_matrix.csv"

    def _action_allowed(self, user, action_xmlid):
        action = self.env.ref(action_xmlid)
        if not getattr(action, "groups_id", None):
            return True
        return bool(action.groups_id & user.groups_id)

    def _menu_visible(self, user, menu_xmlid):
        menu = self.env.ref(menu_xmlid)
        current = menu
        while current:
            if current.groups_id and not (current.groups_id & user.groups_id):
                return False
            current = current.parent_id
        return True

    def _can_read(self, user, record):
        try:
            return bool(self.env[record._name].with_user(user).search_count([("id", "=", record.id)]))
        except AccessError:
            return False

    def _write_allowed(self, user, record, values):
        try:
            record.with_user(user).write(values)
        except AccessError:
            return False
        return True

    def _handler_env(self, user):
        return self.env["res.users"].with_user(user).env

    def _write_report(self, rows):
        target = self._audit_path()
        try:
            self._write_report_file(target, rows)
        except OSError:
            self._write_report_file("/tmp/permission_project_isolation_matrix.csv", rows)

    def _write_report_file(self, target, rows):
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["layer", "case", "allowed", "evidence"])
            writer.writeheader()
            writer.writerows(rows)

    def test_permission_project_isolation_matrix(self):
        rows = []
        failures = []

        for role, config in PERM_MATRIX.items():
            user = self.users[role]
            for menu_xmlid in config.get("menus_allow", []):
                allowed = self._menu_visible(user, menu_xmlid)
                rows.append({"layer": "menu", "case": f"{role}:{menu_xmlid}", "allowed": allowed, "evidence": "allow"})
                if not allowed:
                    failures.append(f"{role} should see {menu_xmlid}")
            for menu_xmlid in config.get("menus_deny", []):
                allowed = self._menu_visible(user, menu_xmlid)
                rows.append({"layer": "menu", "case": f"{role}:{menu_xmlid}", "allowed": allowed, "evidence": "deny"})
                if allowed:
                    failures.append(f"{role} should not see {menu_xmlid}")
            for action_xmlid in config.get("actions_allow", []):
                allowed = self._action_allowed(user, action_xmlid)
                rows.append({"layer": "action", "case": f"{role}:{action_xmlid}", "allowed": allowed, "evidence": "allow"})
                if not allowed:
                    failures.append(f"{role} should execute {action_xmlid}")
            for action_xmlid in config.get("actions_deny", []):
                allowed = self._action_allowed(user, action_xmlid)
                rows.append({"layer": "action", "case": f"{role}:{action_xmlid}", "allowed": allowed, "evidence": "deny"})
                if allowed:
                    failures.append(f"{role} should not execute {action_xmlid}")

        record_cases = [
            ("project_read_same", self._can_read(self.project_read_user, self.project_read), True),
            ("project_read_other", self._can_read(self.project_read_user, self.project_other), False),
            ("project_user_task_same_write", self._write_allowed(self.project_user, self.task_user, {"name": "Permission Isolation Task User Updated"}), True),
            ("project_user_task_other_write", self._write_allowed(self.project_user, self.task_other, {"name": "Permission Isolation Task Other Updated"}), False),
            ("finance_read_payment_same", self._can_read(self.finance_read_user, self.payment_read), True),
            ("finance_read_payment_other", self._can_read(self.finance_read_user, self.payment_other), False),
            ("finance_user_payment_same_write", self._write_allowed(self.finance_user, self.payment_user, {"note": "Permission Isolation Payment User"}), True),
            ("finance_user_payment_other_write", self._write_allowed(self.finance_user, self.payment_other, {"note": "Permission Isolation Payment Other"}), False),
            ("settlement_read_same", self._can_read(self.settlement_read_user, self.settlement_read), True),
            ("settlement_read_other", self._can_read(self.settlement_read_user, self.settlement_other), False),
            ("settlement_user_same_write", self._write_allowed(self.settlement_user, self.settlement_user_record, {"note": "Permission Isolation Settlement User"}), True),
            ("settlement_user_other_write", self._write_allowed(self.settlement_user, self.settlement_other, {"note": "Permission Isolation Settlement Other"}), False),
        ]
        for case, allowed, expected in record_cases:
            rows.append({"layer": "record_rule", "case": case, "allowed": allowed, "evidence": f"expected={expected}"})
            if allowed is not expected:
                failures.append(f"{case} expected {expected} got {allowed}")

        with self.assertRaises(AccessError):
            PaymentRequestExecuteHandler(
                self._handler_env(self.project_read_user),
                payload={"intent": "payment.request.execute", "params": {"action": "submit"}},
            ).run()
        rows.append(
            {
                "layer": "intent",
                "case": "payment.request.execute:project_read",
                "allowed": False,
                "evidence": "AccessError",
            }
        )

        finance_result = PaymentRequestExecuteHandler(
            self._handler_env(self.finance_user),
            payload={"intent": "payment.request.execute", "params": {"action": "submit"}},
        ).run()
        finance_allowed = isinstance(finance_result, dict) and finance_result.get("ok") is False
        rows.append(
            {
                "layer": "intent",
                "case": "payment.request.execute:finance_user",
                "allowed": finance_allowed,
                "evidence": "entered_handler_and_returned_validation_response",
            }
        )
        if not finance_allowed:
            failures.append("finance_user should pass intent role gate and return validation response")

        self._write_report(rows)
        self.assertFalse(failures, "; ".join(failures))
