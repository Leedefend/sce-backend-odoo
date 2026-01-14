# -*- coding: utf-8 -*-
import csv
import logging
import os

from odoo.tests.common import TransactionCase, tagged

_logger = logging.getLogger(__name__)

OPS = ("read", "create", "write", "unlink")

# P0 roles for ACL gate coverage.
ACL_ROLES = {
    "project_read": ["smart_construction_core.group_sc_cap_project_read"],
    "project_manager": ["smart_construction_core.group_sc_cap_project_manager"],
    "cost_manager": ["smart_construction_core.group_sc_cap_cost_manager"],
    "contract_user": ["smart_construction_core.group_sc_cap_contract_user"],
    "contract_manager": ["smart_construction_core.group_sc_cap_contract_manager"],
    "finance_read": ["smart_construction_core.group_sc_cap_finance_read"],
    "finance_user": ["smart_construction_core.group_sc_cap_finance_user"],
    "finance_manager": ["smart_construction_core.group_sc_cap_finance_manager"],
    "material_manager": ["smart_construction_core.group_sc_cap_material_manager"],
    "data_read": ["smart_construction_core.group_sc_cap_data_read"],
    "config_admin": ["smart_construction_core.group_sc_cap_config_admin"],
    "settlement_read": ["smart_construction_core.group_sc_cap_settlement_read"],
    "settlement_user": ["smart_construction_core.group_sc_cap_settlement_user"],
    "settlement_manager": ["smart_construction_core.group_sc_cap_settlement_manager"],
}

# P0 models for audit output and expectations.
ACL_AUDIT_MODELS = [
    "project.project",
    "project.boq.line",
    "construction.contract",
    "construction.contract.line",
    "payment.request",
    "project.material.plan",
    "project.material.plan.line",
    "project.dictionary",
    "sc.treasury.ledger",
    "sc.settlement.order",
    "sc.settlement.order.line",
]

# Models that are intentionally excluded from P0 ACL expectations and tracked as P1.
ACL_P1_MODELS = [
    "project.task",
]

ACL_EXPECTATIONS = [
    {"role": "project_read", "model": "project.project", "rights": {"read": True, "create": False, "write": False, "unlink": False}},
    {"role": "project_manager", "model": "project.project", "rights": {"read": True, "create": True, "write": True, "unlink": True}},
    {"role": "project_read", "model": "project.boq.line", "rights": {"read": True, "create": False, "write": False, "unlink": False}},
    {"role": "cost_manager", "model": "project.boq.line", "rights": {"read": True, "create": True, "write": True, "unlink": True}},
    {"role": "contract_user", "model": "construction.contract", "rights": {"read": True, "create": True, "write": True, "unlink": False}},
    {"role": "contract_manager", "model": "construction.contract", "rights": {"read": True, "create": True, "write": True, "unlink": True}},
    {"role": "finance_read", "model": "construction.contract", "rights": {"read": True, "create": False, "write": False, "unlink": False}},
    {"role": "contract_user", "model": "construction.contract.line", "rights": {"read": True, "create": True, "write": True, "unlink": False}},
    {"role": "contract_manager", "model": "construction.contract.line", "rights": {"read": True, "create": True, "write": True, "unlink": True}},
    {"role": "finance_read", "model": "payment.request", "rights": {"read": True, "create": False, "write": False, "unlink": False}},
    {"role": "finance_user", "model": "payment.request", "rights": {"read": True, "create": True, "write": True, "unlink": False}},
    {"role": "finance_manager", "model": "payment.request", "rights": {"read": True, "create": True, "write": True, "unlink": True}},
    {"role": "material_manager", "model": "project.material.plan", "rights": {"read": True, "create": True, "write": True, "unlink": True}},
    {"role": "material_manager", "model": "project.material.plan.line", "rights": {"read": True, "create": True, "write": True, "unlink": True}},
    {"role": "data_read", "model": "project.dictionary", "rights": {"read": True, "create": False, "write": False, "unlink": False}},
    {"role": "config_admin", "model": "project.dictionary", "rights": {"read": True, "create": True, "write": True, "unlink": True}},
    {"role": "finance_read", "model": "sc.treasury.ledger", "rights": {"read": True, "create": False, "write": False, "unlink": False}},
    {"role": "finance_user", "model": "sc.treasury.ledger", "rights": {"read": True, "create": False, "write": False, "unlink": False}},
    {"role": "finance_manager", "model": "sc.treasury.ledger", "rights": {"read": True, "create": True, "write": True, "unlink": True}},
    {"role": "settlement_read", "model": "sc.settlement.order", "rights": {"read": True, "create": False, "write": False, "unlink": False}},
    {"role": "settlement_user", "model": "sc.settlement.order", "rights": {"read": True, "create": True, "write": True, "unlink": False}},
    {"role": "settlement_manager", "model": "sc.settlement.order", "rights": {"read": True, "create": True, "write": True, "unlink": True}},
    {"role": "settlement_read", "model": "sc.settlement.order.line", "rights": {"read": True, "create": False, "write": False, "unlink": False}},
    {"role": "settlement_user", "model": "sc.settlement.order.line", "rights": {"read": True, "create": True, "write": True, "unlink": False}},
    {"role": "settlement_manager", "model": "sc.settlement.order.line", "rights": {"read": True, "create": True, "write": True, "unlink": True}},
]


@tagged("post_install", "-at_install", "sc_gate", "sc_perm", "acl_gate")
class TestAclMatrixGate(TransactionCase):
    """ACL gate: enforce CRUD expectations on key models and emit audit matrix."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.ref("base.main_company")

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

        cls.users = {role: _create_user(role, groups) for role, groups in ACL_ROLES.items()}

    def _rights(self, user, model_name):
        if model_name not in self.env:
            return None
        model = self.env[model_name].with_user(user)
        return {op: bool(model.check_access_rights(op, raise_exception=False)) for op in OPS}

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
                return os.path.join(docs_dir, "acl_matrix.csv")
            except OSError:
                pass
        return "/tmp/acl_matrix.csv"

    def _write_audit_csv(self):
        target = self._audit_path()
        rows = []
        missing = []
        for model_name in ACL_AUDIT_MODELS:
            if model_name not in self.env:
                missing.append(model_name)
                continue
            for role, user in self.users.items():
                rights = self._rights(user, model_name)
                if rights is None:
                    continue
                rows.append(
                    {
                        "model": model_name,
                        "role": role,
                        "read": rights["read"],
                        "create": rights["create"],
                        "write": rights["write"],
                        "unlink": rights["unlink"],
                    }
                )

        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["model", "role", "read", "create", "write", "unlink"],
            )
            writer.writeheader()
            writer.writerows(rows)

        if missing:
            _logger.info("ACL audit skipped missing models: %s", ", ".join(missing))
        _logger.info("ACL audit matrix written to %s", target)

    def _write_p1_acl_sources(self):
        repo_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir)
        )
        docs_dir = os.path.join(repo_root, "docs", "audit")
        target = os.path.join(docs_dir, "acl_p1_sources.csv")
        if os.path.isdir(docs_dir):
            probe = os.path.join(docs_dir, ".write_test")
            try:
                with open(probe, "w", encoding="utf-8") as handle:
                    handle.write("ok")
                os.unlink(probe)
            except OSError:
                target = "/tmp/acl_p1_sources.csv"
        else:
            target = "/tmp/acl_p1_sources.csv"

        rows = []
        missing = []
        Access = self.env["ir.model.access"].sudo()
        for model_name in ACL_P1_MODELS:
            if model_name not in self.env:
                missing.append(model_name)
                continue
            access_recs = Access.search([("model_id.model", "=", model_name)])
            for acc in access_recs:
                if not (acc.perm_create or acc.perm_write or acc.perm_unlink):
                    continue
                group = acc.group_id
                xmlid = ""
                if group:
                    xmlid = group.get_external_id().get(group.id) or ""
                rows.append(
                    {
                        "model": model_name,
                        "group_xmlid": xmlid,
                        "group_name": group.name if group else "__all__",
                        "create": bool(acc.perm_create),
                        "write": bool(acc.perm_write),
                        "unlink": bool(acc.perm_unlink),
                    }
                )

        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["model", "group_xmlid", "group_name", "create", "write", "unlink"],
            )
            writer.writeheader()
            writer.writerows(rows)

        if missing:
            _logger.info("P1 ACL source audit skipped missing models: %s", ", ".join(missing))
        _logger.info("P1 ACL source audit written to %s", target)

    def test_acl_matrix_gate(self):
        failures = []
        missing = []

        for item in ACL_EXPECTATIONS:
            role = item["role"]
            model = item["model"]
            expected = item["rights"]
            if model not in self.env:
                missing.append(model)
                continue
            user = self.users[role]
            rights = self._rights(user, model)
            for op, exp in expected.items():
                got = rights.get(op)
                if got != exp:
                    failures.append(f"{role} {model} {op}: expected {exp} got {got}")

        self._write_audit_csv()
        self._write_p1_acl_sources()

        if missing:
            failures.append(f"Missing models: {', '.join(sorted(set(missing)))}")

        self.assertFalse(failures, "ACL matrix gate failures: %s" % "; ".join(failures))
