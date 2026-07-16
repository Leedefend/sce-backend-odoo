# -*- coding: utf-8 -*-

import base64

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.services.payment_request_work_item_service import (
    PaymentRequestWorkItemService,
)
from odoo.addons.smart_construction_core.handlers.my_work_summary import MyWorkSummaryHandler


@tagged("sc_smoke", "payment_request_work_item_service")
class TestPaymentRequestWorkItemService(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create({"name": "Work Item Vendor"})
        cls.project = cls.env["project.project"].create(
            {
                "name": "Work Item Project",
                "code": "WORK-ITEM",
                "company_id": cls.company.id,
                "funding_enabled": True,
            }
        )
        cls.env["project.funding.baseline"].create(
            {"project_id": cls.project.id, "total_amount": 1000.0, "state": "active"}
        )
        cls.contract = cls.env["construction.contract"].create(
            {
                "subject": "Work Item Contract",
                "type": "in",
                "project_id": cls.project.id,
                "partner_id": cls.partner.id,
            }
        )
        cls.finance = cls._user(
            "work_item_finance",
            ["smart_construction_core.group_sc_cap_finance_manager"],
        )
        cls.executive = cls._user(
            "work_item_executive",
            ["smart_construction_core.group_sc_cap_finance_manager"],
        )
        cls.member = cls._user(
            "work_item_member",
            ["smart_construction_core.group_sc_cap_project_read"],
        )
        cls.project.message_subscribe(partner_ids=[cls.member.partner_id.id])
        cls.draft = cls.env["payment.request"].create(
            {
                "name": "WORK-ITEM-DRAFT-001",
                "type": "pay",
                "project_id": cls.project.id,
                "contract_id": cls.contract.id,
                "partner_id": cls.partner.id,
                "amount": 100.0,
                "state": "draft",
            }
        )
        cls.submitted = cls.env["payment.request"].create(
            {
                "name": "WORK-ITEM-SUBMIT-001",
                "type": "pay",
                "project_id": cls.project.id,
                "contract_id": cls.contract.id,
                "partner_id": cls.partner.id,
                "amount": 80.0,
                # The work-item projection is the unit under test.  Establish
                # the submitted starting state below without coupling this
                # fixture to the independent funding-gate workflow.
                "state": "draft",
            }
        )
        cls.env["ir.attachment"].create(
            {
                "name": "work-item.txt",
                "type": "binary",
                "datas": base64.b64encode(b"work item").decode("ascii"),
                "res_model": "payment.request",
                "res_id": cls.draft.id,
            }
        )
        cls.env.cr.execute(
            """UPDATE payment_request
                  SET create_uid=%s,
                      state=CASE WHEN id=%s THEN 'submit' ELSE state END
                WHERE id IN %s""",
            (cls.finance.id, cls.submitted.id, tuple([cls.draft.id, cls.submitted.id])),
        )
        (cls.draft | cls.submitted).invalidate_recordset(["create_uid", "state"])

    @classmethod
    def _user(cls, login, group_xmlids):
        group_ids = [cls.env.ref("base.group_user").id]
        group_ids.extend(cls.env.ref(xmlid).id for xmlid in group_xmlids)
        return cls.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": login,
                "login": login,
                "email": "%s@example.com" % login,
                "company_id": cls.company.id,
                "company_ids": [(6, 0, [cls.company.id])],
                "groups_id": [(6, 0, group_ids)],
            }
        )

    def _workspace(self, user):
        service = PaymentRequestWorkItemService(
            self.env(user=user.id),
            params={},
            context={},
        )
        if user == self.finance:
            service._group_xmlids.add("smart_construction_custom.group_sc_role_finance")
        if user == self.executive:
            service._group_xmlids.add("smart_construction_custom.group_sc_role_executive")
        return service.build()

    def test_finance_sees_submit_and_own_items_with_matching_counts(self):
        workspace = self._workspace(self.finance)
        by_key = {row["key"]: row for row in workspace["sections"]}
        todo_names = {item["record"]["label"] for item in by_key["todo"]["items"]}
        initiated_names = {item["record"]["label"] for item in by_key["initiated"]["items"]}
        self.assertTrue(any("WORK-ITEM-DRAFT-001" in name for name in todo_names))
        self.assertFalse(any("WORK-ITEM-SUBMIT-001" in name for name in todo_names))
        self.assertTrue(any("WORK-ITEM-DRAFT-001" in name for name in initiated_names))
        self.assertTrue(any("WORK-ITEM-SUBMIT-001" in name for name in initiated_names))
        self.assertEqual(workspace["counts"]["todo"], len(by_key["todo"]["items"]))
        self.assertEqual(workspace["counts"]["initiated"], len(by_key["initiated"]["items"]))
        draft = next(item for item in by_key["todo"]["items"] if "WORK-ITEM-DRAFT-001" in item["record"]["label"])
        self.assertEqual([row["key"] for row in draft["actions"]], ["submit"])
        self.assertEqual(draft["amount"]["value"], 100.0)
        self.assertEqual(
            [row["label"] for row in draft["facts"]],
            ["项目", "公司", "往来方", "金额", "发起人", "发起时间"],
        )
        self.assertIn("WORK-ITEM-DRAFT-001", draft["search_text"])
        self.assertEqual(workspace["presentation"]["default_sort"], "updated_desc")
        self.assertEqual(workspace["presentation"]["quick_links"][0]["label"], "付款申请")
        self.assertTrue(workspace["presentation"]["quick_links"][0]["route"].startswith("/a/"))
        self.assertNotIn("model", draft["record"])

    def test_executive_only_gets_submitted_approval_item(self):
        workspace = self._workspace(self.executive)
        todo = next(row for row in workspace["sections"] if row["key"] == "todo")
        submitted = next(item for item in todo["items"] if "WORK-ITEM-SUBMIT-001" in item["record"]["label"])
        self.assertEqual({row["key"] for row in submitted["actions"]}, {"approve", "reject"})
        self.assertFalse(any("WORK-ITEM-DRAFT-001" in item["record"]["label"] for item in todo["items"]))

    def test_project_member_has_no_payment_work_item_or_sensitive_facts(self):
        workspace = self._workspace(self.member)
        self.assertEqual(workspace["counts"].get("todo"), 0)
        self.assertEqual(workspace["counts"].get("initiated"), 0)
        serialized = str(workspace)
        self.assertNotIn("WORK-ITEM-DRAFT-001", serialized)
        self.assertNotIn("100.0", serialized)
        self.assertEqual(workspace["presentation"]["quick_links"], [])

    def test_company_scope_is_part_of_query_contract(self):
        workspace = self._workspace(self.finance)
        self.assertEqual(workspace["query_scope"]["company_ids"], [self.company.id])
        for section in workspace["sections"]:
            self.assertEqual(section["count"], len(section["items"]))

    def test_service_source_contains_no_sudo(self):
        import inspect

        source = inspect.getsource(PaymentRequestWorkItemService)
        self.assertNotIn(".sudo(", source)

    def test_product_handler_does_not_execute_legacy_sudo_aggregation(self):
        handler = MyWorkSummaryHandler(self.env(user=self.finance.id), payload={})
        handler._safe_count = lambda *args, **kwargs: self.fail("legacy aggregation executed")
        result = handler.handle({"product_workspace": True})
        self.assertTrue(result.get("ok"))
        data = result.get("data") or {}
        self.assertEqual(data.get("items"), [])
        self.assertTrue((data.get("product_workspace") or {}).get("version"))
