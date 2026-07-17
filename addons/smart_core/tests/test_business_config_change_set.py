# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.handlers.business_config_change_set import (
    BusinessConfigChangeSetGetHandler,
    BusinessConfigChangeSetOpenHandler,
    BusinessConfigChangeSetPreviewHandler,
    BusinessConfigChangeSetPublishHandler,
    BusinessConfigChangeSetRollbackHandler,
    BusinessConfigChangeSetStageHandler,
    BusinessConfigChangeSetValidateHandler,
    BusinessConfigMutationAuditSnapshotHandler,
)
from odoo.addons.smart_core.model.ui_business_config_change_set import stable_payload_hash


@tagged("post_install", "-at_install", "smart_core", "business_config_change_set")
class TestBusinessConfigChangeSet(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_user = cls.env.ref("base.group_user")
        group_config = cls.env.ref("smart_core.group_smart_core_business_config_admin")
        cls.admin = cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Change Set Admin", "login": "change_set_admin", "email": "change-set-admin@example.test",
            "groups_id": [(6, 0, [group_user.id, group_config.id])],
        })
        cls.other_admin = cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Other Change Set Admin", "login": "other_change_set_admin", "email": "other-change-set-admin@example.test",
            "groups_id": [(6, 0, [group_user.id, group_config.id])],
        })
        cls.ordinary = cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Ordinary User", "login": "ordinary_change_set_user", "email": "ordinary-change-set@example.test",
            "groups_id": [(6, 0, [group_user.id])],
        })

    def _env(self, user):
        return self.env(user=user, context={**self.env.context, "allowed_company_ids": [self.env.company.id]})

    def _open(self, role_key="config_admin"):
        env = self._env(self.admin)
        result = BusinessConfigChangeSetOpenHandler(env).handle(payload={"params": {"role_key": role_key}})
        self.assertTrue(result["ok"], result)
        return env, result["data"]

    def _payload(self, field_name="name"):
        return {"view_orchestration": {"views": {"form": {"fields": [{"name": field_name}]}}}}

    def _stage(self, env, change_set, target):
        result = BusinessConfigChangeSetStageHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin", "config_type": "form",
            "target_key": target, "model": "res.partner", "view_type": "form", "draft_payload": self._payload(),
            "diff_summary": {"summary": "测试配置"},
        }})
        self.assertTrue(result["ok"], result)
        return result["data"]

    def test_owner_role_and_ordinary_user_isolation(self):
        env, change_set = self._open()
        with self.assertRaises(AccessError):
            BusinessConfigChangeSetGetHandler(self._env(self.ordinary)).handle(payload={"params": {"change_set_token": change_set["token"], "role_key": "config_admin"}})
        hidden = BusinessConfigChangeSetGetHandler(self._env(self.other_admin)).handle(payload={"params": {"change_set_token": change_set["token"], "role_key": "config_admin"}})
        self.assertEqual(hidden["code"], 404)
        change_set_record = env["ui.business.config.change.set"].browse(change_set["id"])
        env["ui.business.config.change.set.item"].create({
            "change_set_id": change_set_record.id, "config_type": "form", "target_key": "test.owner.rule",
            "model": "res.partner", "base_payload_hash": stable_payload_hash({}), "draft_payload": self._payload(),
        })
        other_env = self._env(self.other_admin)
        self.assertFalse(other_env["ui.business.config.change.set"].search([("id", "=", change_set_record.id)]))
        self.assertFalse(other_env["ui.business.config.change.set.item"].search([("change_set_id", "=", change_set_record.id)]))
        with self.assertRaises(ValidationError):
            self.env["ui.business.config.change.set"].sudo().browse(change_set["id"]).with_env(self._env(self.admin)).assert_owner_scope(role_key="platform_admin")

    def test_stage_rejects_stale_payload_hash(self):
        env, change_set = self._open()
        result = BusinessConfigChangeSetStageHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin", "config_type": "form",
            "target_key": "test.change.set.stale", "model": "res.partner", "view_type": "form",
            "current_payload_hash": "stale", "draft_payload": self._payload(),
        }})
        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 409)
        self.assertEqual(result["error"]["reason_code"], "STALE_CONFIG_HASH")

    def test_preview_has_zero_formal_contract_or_version_writes(self):
        env, change_set = self._open()
        self._stage(env, change_set, "test.change.set.preview")
        Contract = self.env["ui.business.config.contract"].sudo().with_context(active_test=False)
        Version = self.env["ui.business.config.contract.version"].sudo()
        before = (Contract.search_count([]), Version.search_count([]))
        result = BusinessConfigChangeSetPreviewHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin", "device": "mobile",
        }})
        self.assertTrue(result["ok"], result)
        self.assertEqual(before, (Contract.search_count([]), Version.search_count([])))
        self.assertEqual(result["data"]["preview"]["device"], "mobile")
        self.assertEqual(result["data"]["preview"]["formal_contract_write_count"], 0)
        self.assertEqual(result["data"]["preview"]["formal_version_write_count"], 0)
        self.assertEqual(result["data"]["preview"]["formal_config_mutation_count"], 0)
        self.assertFalse(self.env["ui.business.config.mutation.audit"].sudo().search([
            ("trace_id", "=", result["data"]["preview"]["mutation_trace_id"]),
        ]))
        preview_env = env(context={
            **env.context,
            "business_config_preview_token": result["data"]["preview"]["token"],
            "business_config_preview_user_id": self.admin.id,
            "business_config_preview_role_key": "config_admin",
        })
        projected = preview_env["ui.business.config.contract"]._effective_view_orchestration_contracts(
            "res.partner", view_type="form", role_key="config_admin",
        )
        self.assertTrue(any(str(row.name).startswith("preview:") for row in projected))
        snapshot = BusinessConfigMutationAuditSnapshotHandler(env).handle()
        self.assertTrue(snapshot["ok"])
        self.assertIn("ui.business.config.contract", snapshot["data"]["formal_models"])

    def test_high_risk_operation_is_rejected_from_batch(self):
        env, change_set = self._open()
        result = BusinessConfigChangeSetStageHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin",
            "config_type": "approval", "target_key": "test.high.risk", "model": "res.partner",
            "draft_payload": {"steps": []},
        }})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["reason_code"], "HIGH_RISK_OPERATION_REQUIRED")

    def test_publish_detects_concurrent_contract_update(self):
        env, change_set = self._open()
        self._stage(env, change_set, "test.change.set.conflict")
        validated = BusinessConfigChangeSetValidateHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin",
        }})
        self.assertEqual(validated["data"]["state"], "ready")
        item = self.env["ui.business.config.change.set.item"].sudo().search([
            ("change_set_id", "=", change_set["id"]),
        ], limit=1)
        contract = self.env["ui.business.config.contract"].sudo().create({
            "name": "test.change.set.conflict", "model": "res.partner", "view_type": "form",
            "company_id": self.env.company.id, "contract_json": self._payload("email"), "status": "published",
        })
        item.write({"target_contract_id": contract.id})
        result = BusinessConfigChangeSetPublishHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin", "request_id": "conflict-batch",
        }})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["reason_code"], "CHANGE_SET_VERSION_CONFLICT")

    def test_publish_is_idempotent_and_batch_rollback_reverses_new_contracts(self):
        env, change_set = self._open()
        for suffix in ("one", "two"):
            self._stage(env, change_set, f"test.change.set.success.{suffix}")
        validated = BusinessConfigChangeSetValidateHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin",
        }})
        self.assertEqual(validated["data"]["state"], "ready")
        params = {"change_set_token": change_set["token"], "role_key": "config_admin", "request_id": "successful-batch"}
        published = BusinessConfigChangeSetPublishHandler(env).handle(payload={"params": params})
        repeated = BusinessConfigChangeSetPublishHandler(env).handle(payload={"params": params})
        self.assertTrue(published["ok"], published)
        self.assertEqual(repeated["data"]["id"], published["data"]["id"])
        Contract = self.env["ui.business.config.contract"].sudo().with_context(active_test=False)
        contracts = Contract.search([("name", "like", "test.change.set.success.%")])
        self.assertEqual(len(contracts), 2)
        rolled_back = BusinessConfigChangeSetRollbackHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin", "request_id": "rollback-successful-batch",
        }})
        self.assertTrue(rolled_back["ok"], rolled_back)
        self.assertNotEqual(rolled_back["data"]["id"], published["data"]["id"])
        self.assertFalse(contracts.exists().filtered("active"))

    def test_publish_failure_rolls_back_all_contract_items(self):
        env, change_set_data = self._open()
        change_set = self.env["ui.business.config.change.set"].sudo().browse(change_set_data["id"])
        Item = self.env["ui.business.config.change.set.item"].sudo()
        for suffix in ("one", "two"):
            Item.create({
                "change_set_id": change_set.id, "config_type": "form", "target_key": f"test.change.set.atomic.{suffix}",
                "model": "res.partner", "view_type": "form", "role_key": "config_admin",
                "base_payload_hash": stable_payload_hash({}), "draft_payload": self._payload(), "validation_result": {"ok": True},
            })
        change_set.write({"state": "ready"})
        original = BusinessConfigChangeSetPublishHandler._publish_contract_item
        calls = {"count": 0}

        def fail_second(handler, item):
            calls["count"] += 1
            if calls["count"] == 2:
                raise ValidationError("injected atomic failure")
            return original(handler, item)

        with patch.object(BusinessConfigChangeSetPublishHandler, "_publish_contract_item", new=fail_second):
            result = BusinessConfigChangeSetPublishHandler(env).handle(payload={"params": {
                "change_set_token": change_set.token, "role_key": "config_admin", "request_id": "atomic-failure-request",
            }})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["reason_code"], "CHANGE_SET_ATOMIC_PUBLISH_FAILED")
        self.assertFalse(self.env["ui.business.config.contract"].sudo().search([("name", "like", "test.change.set.atomic.%")]))
