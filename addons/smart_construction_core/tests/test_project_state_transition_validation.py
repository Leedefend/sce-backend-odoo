# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_gate", "project_state")
class TestProjectStateTransitionValidation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.uom_unit = self.env.ref("uom.product_uom_unit")

    def _create_boq(self, project):
        self.env["project.boq.line"].create(
            {
                "project_id": project.id,
                "code": "BOQ-001",
                "name": "BOQ Item",
                "uom_id": self.uom_unit.id,
                "quantity": 1.0,
                "price": 1.0,
            }
        )

    def test_draft_submit_requires_fields(self):
        project = self.env["project.project"].create({"name": "Draft Project"})
        self._create_boq(project)
        with self.assertRaises(ValidationError):
            project.action_set_lifecycle_state("in_progress")

        owner = self.env["res.partner"].create({"name": "Owner"})
        project.write(
            {
                "owner_id": owner.id,
                "manager_id": self.env.user.id,
                "location": "Test Location",
            }
        )
        project.action_set_lifecycle_state("in_progress")
        self.assertEqual(project.lifecycle_state, "in_progress")
