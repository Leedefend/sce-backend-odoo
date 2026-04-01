# -*- coding: utf-8 -*-
from lxml import etree

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_gate", "project_object_button_runtime")
class TestProjectObjectButtonRuntimeBackend(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.ref("base.main_company")
        cls.project = cls.env["project.project"].create({"name": "Object Button Runtime Project"})

        def _create(login, group_xmlids):
            groups = [(6, 0, [cls.env.ref(xmlid).id for xmlid in group_xmlids])]
            return cls.env["res.users"].with_context(no_reset_password=True).create(
                {
                    "name": login,
                    "login": login,
                    "company_id": company.id,
                    "company_ids": [(6, 0, [company.id])],
                    "groups_id": groups,
                }
            )

        cls.pm_user = _create(
            "project_object_pm",
            [
                "smart_construction_core.group_sc_cap_cost_user",
                "smart_construction_core.group_sc_cap_contract_manager",
            ],
        )
        cls.executive_user = _create(
            "project_object_executive",
            [
                "smart_construction_custom.group_sc_role_executive",
            ],
        )
        cls.super_admin_user = _create(
            "project_object_super_admin",
            [
                "smart_construction_core.group_sc_super_admin",
            ],
        )

    def test_project_financial_object_buttons_do_not_raise_action_view_acl_for_pm(self):
        project = self.project.with_user(self.pm_user)

        budget_action = project.action_open_project_budgets()
        contract_action = project.action_open_project_contracts()
        task_action = project.action_view_my_tasks()

        self.assertEqual(budget_action.get("res_model"), "project.budget")
        self.assertEqual(contract_action.get("res_model"), "construction.contract")
        self.assertEqual(task_action.get("res_model"), "project.task")

    def test_project_financial_object_buttons_do_not_raise_action_view_acl_for_executive(self):
        project = self.project.with_user(self.executive_user)

        budget_action = project.action_open_project_budgets()
        contract_action = project.action_open_project_contracts()
        task_action = project.action_view_my_tasks()

        self.assertEqual(budget_action.get("res_model"), "project.budget")
        self.assertEqual(contract_action.get("res_model"), "construction.contract")
        self.assertEqual(task_action.get("res_model"), "project.task")

    def test_stage_requirements_button_returns_unsaved_wizard_action(self):
        project = self.project.with_user(self.pm_user)

        action = project.action_view_stage_requirements()

        self.assertEqual(action.get("res_model"), "sc.project.stage.requirement.wizard")
        self.assertEqual(action.get("target"), "new")
        self.assertFalse(action.get("res_id"))
        ctx = action.get("context") or {}
        self.assertEqual(ctx.get("default_project_id"), self.project.id)
        self.assertEqual(ctx.get("default_lifecycle_state"), self.project.lifecycle_state)

    def test_stage_requirements_button_not_exposed_to_delivered_roles(self):
        view = (
            self.env["project.project"]
            .with_user(self.pm_user)
            .get_view(
                self.env.ref("smart_construction_core.view_project_overview_form").id,
                view_type="form",
            )
        )

        arch = etree.fromstring(view["arch"].encode())
        buttons = arch.xpath("//button[@name='action_view_stage_requirements']")
        self.assertFalse(buttons)

    def test_next_actions_do_not_expose_stage_requirements_fallback_to_delivered_roles(self):
        for user in (self.pm_user, self.executive_user):
            payload = self.project.with_user(user).sc_get_next_actions(limit=3)
            self.assertFalse(payload.get("fallback"))

    def test_next_actions_keep_stage_requirements_fallback_for_super_admin(self):
        payload = self.project.with_user(self.super_admin_user).sc_get_next_actions(limit=3)

        fallback = payload.get("fallback") or {}
        self.assertEqual(fallback.get("action_ref"), "action_view_stage_requirements")
        self.assertEqual(fallback.get("action_type"), "object_method")

    def test_execute_next_action_act_window_branch_works_for_delivered_roles(self):
        for user in (self.pm_user, self.executive_user):
            action = self.project.with_user(user).sc_execute_next_action(
                "act_window_xmlid",
                "smart_construction_core.action_sc_project_manage",
                {"project_id": self.project.id},
            )
            self.assertEqual(action.get("res_model"), "project.project")
            ctx = action.get("context") or {}
            self.assertEqual(ctx.get("default_project_id"), self.project.id)
            self.assertEqual(ctx.get("search_default_project_id"), self.project.id)

    def test_execute_next_action_object_method_branch_works_for_delivered_roles(self):
        for user in (self.pm_user, self.executive_user):
            action = self.project.with_user(user).sc_execute_next_action(
                "object_method",
                "action_view_my_tasks",
                {"project_id": self.project.id},
            )
            self.assertEqual(action.get("res_model"), "project.task")

    def test_execution_side_secondary_entrypoints_do_not_raise_action_view_acl(self):
        for user in (self.pm_user, self.executive_user):
            progress_action = self.project.with_user(user).action_open_project_progress_entry()
            self.assertEqual(progress_action.get("res_model"), "project.progress.entry")

            exec_action = self.env.ref(
                "smart_construction_core.action_exec_structure_entry"
            ).with_user(user).run()
            self.assertIn(exec_action.get("type"), ("ir.actions.act_window", "ir.actions.client"))

    def test_next_action_service_normalizes_multiline_condition_expr(self):
        self.project.lifecycle_state = "draft"

        payload = self.project.with_user(self.pm_user).sc_get_next_actions(limit=5)
        action_refs = [item.get("action_ref") for item in payload.get("actions") or []]

        self.assertIn("action_sc_submit", action_refs)

    def test_project_overview_service_reads_group_count_key(self):
        cost_code = self.env["project.cost.code"].create({"name": "Overview Cost", "code": "OVERVIEW-COST"})
        self.env["project.cost.ledger"].create(
            {
                "project_id": self.project.id,
                "cost_code_id": cost_code.id,
                "period": "2026-03",
                "amount": 100.0,
            }
        )

        overview = self.env["sc.project.overview.service"].get_overview([self.project.id])

        self.assertEqual(overview[self.project.id]["cost"]["count"], 1)

    def test_project_overview_service_counts_task_sc_state_in_progress(self):
        task = self.env["project.task"].create(
            {
                "name": "Overview In Progress Task",
                "project_id": self.project.id,
                "user_ids": [(6, 0, [self.pm_user.id])],
            }
        )

        task.action_prepare_task()
        task.action_start_task()

        overview = self.project.with_user(self.pm_user).env["sc.project.overview.service"].get_overview([self.project.id])

        self.assertEqual(task.sc_state, "in_progress")
        self.assertEqual(overview[self.project.id]["task"]["in_progress"], 1)

    def test_create_task_next_action_tolerates_bootstrap_root_task(self):
        update_cost_rule = self.env.ref("smart_construction_core.sc_next_action_update_cost")
        create_task_rule = self.env.ref("smart_construction_core.sc_next_action_create_task")

        self.assertEqual(update_cost_rule.sequence, 30)
        self.assertEqual(create_task_rule.sequence, 20)
        self.assertEqual(
            create_task_rule.condition_expr,
            "s.get('task', {}).get('count', 0) <= 1 and s.get('task', {}).get('in_progress', 0) == 0",
        )

        project = self.env["project.project"].create(
            {
                "name": "Create Task Recommendation Project",
                "lifecycle_state": "in_progress",
                "owner_id": self.pm_user.id,
                "manager_id": self.pm_user.id,
                "user_id": self.pm_user.id,
                "location": "Bootstrap Task Site",
            }
        )

        payload = project.with_user(self.pm_user).sc_get_next_actions(limit=5)
        titles = [item.get("title") for item in (payload.get("actions") or [])]
        overview = project.with_user(self.pm_user).env["sc.project.overview.service"].get_overview([project.id])

        self.assertEqual(overview[project.id]["task"]["count"], 1)
        self.assertEqual(overview[project.id]["task"]["in_progress"], 0)
        self.assertEqual(titles[0], "创建任务")
