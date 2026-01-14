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

        project_vals = {"privacy_visibility": "followers"}
        cls.project_read = cls.env["project.project"].create(
            dict(project_vals, name="RR Project Read", user_id=cls.user_project_read.id)
        )
        cls.project_user = cls.env["project.project"].create(
            dict(project_vals, name="RR Project User", user_id=cls.user_project_user.id)
        )
        cls.project_other = cls.env["project.project"].create(
            dict(project_vals, name="RR Project Other", user_id=cls.user_project_manager.id)
        )

        cls.task_read = cls.env["project.task"].create(
            {"name": "RR Task Read", "project_id": cls.project_read.id}
        )
        cls.task_user = cls.env["project.task"].create(
            {"name": "RR Task User", "project_id": cls.project_user.id}
        )
        cls.task_other = cls.env["project.task"].create(
            {"name": "RR Task Other", "project_id": cls.project_other.id}
        )

        # Ensure denied records do not inherit follower-based access.
        partners = [
            cls.user_project_read.partner_id.id,
            cls.user_project_user.partner_id.id,
        ]
        cls.project_other.message_unsubscribe(partner_ids=partners)
        cls.task_other.message_unsubscribe(partner_ids=partners)

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
