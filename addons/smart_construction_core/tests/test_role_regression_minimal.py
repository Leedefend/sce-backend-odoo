# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase
from odoo.tests.common import tagged


@tagged("post_install", "-at_install", "sc_gate", "sc_perm", "role_regression_minimal")
class TestRoleRegressionMinimal(TransactionCase):
    """
    最小角色回归：验证典型角色对关键域动作的允许/拒绝。
    关注 action.groups_id 与用户组交集，防止菜单不可见但 action 绕过。
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.ref("base.main_company")

        def _create(login, group_xmlids):
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

        cls.user_project_manager = _create(
            "role_project_manager",
            ["smart_construction_core.group_sc_cap_project_manager"],
        )
        cls.user_finance_user = _create(
            "role_finance_user",
            ["smart_construction_core.group_sc_cap_finance_user"],
        )
        cls.user_finance_manager = _create(
            "role_finance_manager",
            ["smart_construction_core.group_sc_cap_finance_manager"],
        )
        cls.user_material_manager = _create(
            "role_material_manager",
            ["smart_construction_core.group_sc_cap_material_manager"],
        )
        cls.user_config_admin = _create(
            "role_config_admin",
            ["smart_construction_core.group_sc_cap_config_admin"],
        )
        cls.user_contract_user = _create(
            "role_contract_user",
            ["smart_construction_core.group_sc_cap_contract_user"],
        )

    def _allowed(self, user, action_xmlid):
        action = self.env.ref(action_xmlid)
        if not hasattr(action, "groups_id"):
            return True
        return bool(action.groups_id & user.groups_id)

    def test_role_action_matrix(self):
        cases = [
            # 项目域
            (self.user_project_manager, "smart_construction_core.action_project_wbs", True),
            (self.user_finance_user, "smart_construction_core.action_project_wbs", False),
            # 财务域
            (self.user_finance_user, "smart_construction_core.action_payment_request", True),
            (self.user_project_manager, "smart_construction_core.action_payment_request", False),
            # 物资域
            (self.user_material_manager, "smart_construction_core.action_project_material_plan", True),
            (self.user_finance_manager, "smart_construction_core.action_project_material_plan", False),
            # 合同域
            (self.user_contract_user, "smart_construction_core.action_construction_contract", True),
            (self.user_finance_user, "smart_construction_core.action_construction_contract", False),
            # 配置/工作流
            (self.user_config_admin, "smart_construction_core.action_sc_workflow_def", True),
            (self.user_finance_user, "smart_construction_core.action_sc_workflow_def", False),
            # 数据中心（只读组未包含在财务）
            (self.user_finance_manager, "smart_construction_core.action_project_dictionary", False),
        ]

        failures = []
        for user, action_xmlid, expected in cases:
            allowed = self._allowed(user, action_xmlid)
            if allowed != expected:
                failures.append(f"{user.login} vs {action_xmlid} expected {expected} got {allowed}")
        self.assertFalse(failures, "角色动作矩阵越权/缺权: %s" % "; ".join(failures))
