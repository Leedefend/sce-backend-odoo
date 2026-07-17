# -*- coding: utf-8 -*-
from unittest.mock import patch

from datetime import timedelta
from dataclasses import fields as dataclass_fields

from odoo import fields
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
from odoo.addons.smart_core.handlers.form_field_configuration import (
    BusinessConfigAnalysisAuditHandler,
    BusinessConfigListSearchAuditHandler,
)
from odoo.addons.smart_core.app_config_engine.services.assemblers.page_assembler import PageAssembler
from odoo.addons.smart_core.model.ui_business_config_change_set import stable_payload_hash
from odoo.addons.smart_core.model.ui_business_config_contract import ViewOrchestrationContractProjection


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

    def _audit(self, handler_class, env, **params):
        handler = handler_class(env)
        handler.params = params
        return handler.handle()["data"]

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
        staged = self._stage(env, change_set, "test.change.set.preview")
        staged_context = staged["items"][0]["draft_payload"]["view_orchestration"]["context"]
        self.assertEqual(staged_context["source"], "smart_core.lowcode.business_config")
        self.assertEqual(staged_context["source_status"], "tenant_runtime")
        preview_item = env["ui.business.config.change.set.item"].sudo().search([
            ("change_set_id", "=", change_set["id"]),
        ])
        preview_item.write({
            "role_key": False,
            "draft_payload": {"view_orchestration": {
                "context": {"source": "smart_core.lowcode.business_config", "source_status": "tenant_runtime"},
                "views": {"form": {"fields": [{"name": "email", "visible": False}]}},
            }},
        })
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
        preview_projection = next(row for row in projected if str(row.name).startswith("preview:"))
        self.assertEqual(preview_projection.status, "preview")
        self.assertEqual(preview_projection.action_id, 0)
        self.assertEqual(preview_projection.view_id, 0)
        self.assertEqual(preview_projection.source_kind, "change_set_preview")
        data, _versions = PageAssembler(
            preview_env,
            preview_env["ir.model"].sudo().env,
        ).assemble_page_contract({"model": "res.partner", "view_types": ["form"]})
        applied = (((((data.get("governance") or {}).get("view_orchestration") or {}).get("views") or {}).get("form") or {}).get("business_config_contracts") or [])
        self.assertTrue(
            any(str(row.get("name") or "").startswith("preview:") for row in applied),
            applied,
        )
        summary = PageAssembler(preview_env, preview_env["ir.model"].sudo().env)._current_view_orchestration_config_summary(
            model="res.partner", view_type="form", action_id=0, view_id=0,
        )
        self.assertEqual(summary["items"][0]["status"], "preview")
        snapshot = BusinessConfigMutationAuditSnapshotHandler(env).handle()
        self.assertTrue(snapshot["ok"])
        self.assertIn("ui.business.config.contract", snapshot["data"]["formal_models"])

    def test_preview_projection_replaces_existing_contract_and_enforces_scope(self):
        expected_fields = {
            "id", "name", "contract_json", "view_type", "action_id", "view_id", "role_key",
            "priority", "version_no", "status", "source_kind",
        }
        self.assertEqual({field.name for field in dataclass_fields(ViewOrchestrationContractProjection)}, expected_fields)
        env, change_set = self._open()
        action = self.env["ir.actions.act_window"].sudo().create({
            "name": "Preview Projection Scope", "res_model": "res.partner", "view_mode": "form",
        })
        view = self.env["ir.ui.view"].sudo().search([("model", "=", "res.partner"), ("type", "=", "form")], limit=1)
        contract = self.env["ui.business.config.contract"].sudo().create({
            "name": "test.change.set.preview.existing", "model": "res.partner", "view_type": "form",
            "action_id": action.id, "view_id": view.id, "role_key": "config_admin",
            "company_id": self.env.company.id, "contract_json": self._payload("name"), "status": "published",
        })
        staged = BusinessConfigChangeSetStageHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin", "config_type": "form",
            "target_key": contract.name, "model": "res.partner", "view_type": "form",
            "action_id": action.id, "view_id": view.id, "current_contract_id": contract.id,
            "draft_payload": self._payload("email"),
        }})
        self.assertTrue(staged["ok"], staged)
        preview = BusinessConfigChangeSetPreviewHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin",
        }})
        self.assertTrue(preview["ok"], preview)

        def projections(target_env, *, action_value=action.id, view_value=view.id, role_value="config_admin"):
            return target_env["ui.business.config.contract"]._effective_view_orchestration_contracts(
                "res.partner", view_type="form", action_id=action_value, view_id=view_value, role_key=role_value,
            )

        context = {
            **env.context,
            "business_config_preview_token": preview["data"]["preview"]["token"],
            "business_config_preview_user_id": self.admin.id,
            "business_config_preview_role_key": "config_admin",
        }
        preview_env = env(context=context)
        matching = projections(preview_env)
        self.assertEqual(len([row for row in matching if row.source_kind == "change_set_preview"]), 1)
        self.assertFalse(any(row.id == contract.id for row in matching))
        self.assertFalse(any(row.source_kind == "change_set_preview" for row in projections(preview_env, action_value=action.id + 1)))
        wrong_role_env = env(context={
            **context, "business_config_preview_role_key": "platform_admin",
        })
        self.assertFalse(any(row.source_kind == "change_set_preview" for row in projections(wrong_role_env, role_value="platform_admin")))
        other_user_env = self._env(self.other_admin)(context={
            **context, "business_config_preview_user_id": self.other_admin.id,
        })
        self.assertFalse(any(row.source_kind == "change_set_preview" for row in projections(other_user_env)))

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

    def test_concurrent_empty_publish_rejects_stale_base_hash(self):
        env_a, change_set_a = self._open()
        env_b = self._env(self.other_admin)
        opened_b = BusinessConfigChangeSetOpenHandler(env_b).handle(payload={"params": {"role_key": "config_admin"}})
        self.assertTrue(opened_b["ok"], opened_b)
        change_set_b = opened_b["data"]
        original = {"view_orchestration": {"views": {"tree": {"columns": [{"name": "name"}]}}}}
        contract = self.env["ui.business.config.contract"].sudo().create({
            "name": "test.change.set.concurrent.empty", "model": "res.partner", "view_type": "tree",
            "role_key": "config_admin", "company_id": self.env.company.id,
            "contract_json": original, "status": "published",
        })
        empty = {"view_orchestration": {"views": {"tree": {"columns": []}}}}
        for target_env, change_set in ((env_a, change_set_a), (env_b, change_set_b)):
            staged = BusinessConfigChangeSetStageHandler(target_env).handle(payload={"params": {
                "change_set_token": change_set["token"], "role_key": "config_admin", "config_type": "list",
                "target_key": contract.name, "model": "res.partner", "view_type": "tree",
                "current_contract_id": contract.id, "current_payload_hash": stable_payload_hash(original),
                "draft_payload": empty,
            }})
            self.assertTrue(staged["ok"], staged)
            validated = BusinessConfigChangeSetValidateHandler(target_env).handle(payload={"params": {
                "change_set_token": change_set["token"], "role_key": "config_admin",
            }})
            self.assertEqual(validated["data"]["state"], "ready", validated)
        published = BusinessConfigChangeSetPublishHandler(env_a).handle(payload={"params": {
            "change_set_token": change_set_a["token"], "role_key": "config_admin", "request_id": "empty-concurrent-a",
        }})
        self.assertTrue(published["ok"], published)
        stale = BusinessConfigChangeSetPublishHandler(env_b).handle(payload={"params": {
            "change_set_token": change_set_b["token"], "role_key": "config_admin", "request_id": "empty-concurrent-b",
        }})
        self.assertFalse(stale["ok"], stale)
        self.assertEqual(stale["code"], 409)
        self.assertEqual(stale["error"]["reason_code"], "CHANGE_SET_VERSION_CONFLICT")

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

    def test_explicit_empty_list_search_payloads_publish_and_rollback(self):
        env, change_set = self._open()
        Contract = self.env["ui.business.config.contract"].sudo()
        original_list = {"view_orchestration": {"views": {"tree": {"columns": [{"name": "name"}]}}}}
        original_search = {"view_orchestration": {"views": {"search": {
            "filters": [{"name": "name"}], "group_by": [{"name": "company_id"}],
        }}}}
        original_pivot = {"view_orchestration": {"views": {"pivot": {
            "measures": [{"name": "id"}], "dimensions": [{"name": "company_id"}],
        }}}}
        original_graph = {"view_orchestration": {"views": {"graph": {
            "measures": [{"name": "id"}], "dimensions": [{"name": "company_id"}], "type": "bar",
        }}}}
        list_contract = Contract.create({
            "name": "test.change.set.empty.list", "model": "res.partner", "view_type": "tree",
            "company_id": self.env.company.id, "contract_json": original_list, "status": "published",
        })
        search_contract = Contract.create({
            "name": "test.change.set.empty.search", "model": "res.partner", "view_type": "search",
            "company_id": self.env.company.id, "contract_json": original_search, "status": "published",
        })
        pivot_contract = Contract.create({
            "name": "test.change.set.empty.pivot", "model": "res.partner", "view_type": "pivot",
            "company_id": self.env.company.id, "contract_json": original_pivot, "status": "published",
        })
        graph_contract = Contract.create({
            "name": "test.change.set.empty.graph", "model": "res.partner", "view_type": "graph",
            "company_id": self.env.company.id, "contract_json": original_graph, "status": "published",
        })
        empty_payloads = (
            ("list", "tree", list_contract, {"view_orchestration": {"views": {"tree": {"columns": []}}}}),
            ("search", "search", search_contract, {"view_orchestration": {"views": {"search": {"filters": [], "group_by": []}}}}),
            ("analysis", "pivot", pivot_contract, {"view_orchestration": {"views": {"pivot": {"measures": [], "dimensions": []}}}}),
            ("analysis", "graph", graph_contract, {"view_orchestration": {"views": {"graph": {"measures": [], "dimensions": [], "type": "bar"}}}}),
        )
        for config_type, view_type, contract, draft_payload in empty_payloads:
            staged = BusinessConfigChangeSetStageHandler(env).handle(payload={"params": {
                "change_set_token": change_set["token"], "role_key": "config_admin",
                "config_type": config_type, "target_key": contract.name, "model": "res.partner",
                "view_type": view_type, "current_contract_id": contract.id, "draft_payload": draft_payload,
            }})
            self.assertTrue(staged["ok"], staged)
        validated = BusinessConfigChangeSetValidateHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin",
        }})
        self.assertEqual(validated["data"]["state"], "ready", validated)
        published = BusinessConfigChangeSetPublishHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin", "request_id": "empty-config-publish",
        }})
        self.assertTrue(published["ok"], published)
        self.assertTrue(published["data"]["publish_result"]["ok"])
        list_contract.invalidate_recordset(["contract_json"])
        search_contract.invalidate_recordset(["contract_json"])
        pivot_contract.invalidate_recordset(["contract_json"])
        graph_contract.invalidate_recordset(["contract_json"])
        self.assertEqual(list_contract.contract_json["view_orchestration"]["views"]["tree"]["columns"], [])
        self.assertEqual(search_contract.contract_json["view_orchestration"]["views"]["search"]["filters"], [])
        self.assertEqual(search_contract.contract_json["view_orchestration"]["views"]["search"]["group_by"], [])
        self.assertEqual(pivot_contract.contract_json["view_orchestration"]["views"]["pivot"]["measures"], [])
        self.assertEqual(pivot_contract.contract_json["view_orchestration"]["views"]["pivot"]["dimensions"], [])
        self.assertEqual(graph_contract.contract_json["view_orchestration"]["views"]["graph"]["measures"], [])
        self.assertEqual(graph_contract.contract_json["view_orchestration"]["views"]["graph"]["dimensions"], [])
        version_count = self.env["ui.business.config.contract.version"].sudo().search_count([
            ("contract_id", "in", [list_contract.id, search_contract.id, pivot_contract.id, graph_contract.id]),
        ])
        for _index in range(2):
            list_audit = self._audit(
                BusinessConfigListSearchAuditHandler, env, model="res.partner", role_key="config_admin",
            )
            analysis_audit = self._audit(
                BusinessConfigAnalysisAuditHandler, env, model="res.partner", role_key="config_admin",
            )
            self.assertTrue(list_audit["has_business_list_config"])
            self.assertTrue(list_audit["has_business_search_config"])
            self.assertEqual(list_audit["business_config_list_columns"], [])
            self.assertEqual(list_audit["business_config_search_filters"], [])
            self.assertEqual(list_audit["business_config_search_group_by"], [])
            self.assertTrue(analysis_audit["has_business_pivot_config"])
            self.assertTrue(analysis_audit["has_business_graph_config"])
            self.assertEqual(analysis_audit["pivot_measures"], [])
            self.assertEqual(analysis_audit["pivot_dimensions"], [])
            self.assertEqual(analysis_audit["graph_measures"], [])
            self.assertEqual(analysis_audit["graph_dimensions"], [])
        self.assertEqual(version_count, self.env["ui.business.config.contract.version"].sudo().search_count([
            ("contract_id", "in", [list_contract.id, search_contract.id, pivot_contract.id, graph_contract.id]),
        ]))
        rolled_back = BusinessConfigChangeSetRollbackHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin", "request_id": "empty-config-rollback",
        }})
        self.assertTrue(rolled_back["ok"], rolled_back)
        list_contract.invalidate_recordset(["contract_json"])
        search_contract.invalidate_recordset(["contract_json"])
        pivot_contract.invalidate_recordset(["contract_json"])
        graph_contract.invalidate_recordset(["contract_json"])
        self.assertEqual(list_contract.contract_json, original_list)
        self.assertEqual(search_contract.contract_json, original_search)
        self.assertEqual(pivot_contract.contract_json, original_pivot)
        self.assertEqual(graph_contract.contract_json, original_graph)

    def test_empty_contract_audit_scope_and_lifecycle_isolation(self):
        action = self.env["ir.actions.act_window"].sudo().create({
            "name": "Empty Contract Audit Scope", "res_model": "res.currency", "view_mode": "tree",
        })
        other_action = self.env["ir.actions.act_window"].sudo().create({
            "name": "Empty Contract Audit Other Scope", "res_model": "res.currency", "view_mode": "tree",
        })
        Contract = self.env["ui.business.config.contract"].sudo()
        empty = {"view_orchestration": {"views": {"tree": {"columns": []}}}}
        Contract.create({
            "name": "test.empty.audit.scope.published", "model": "res.currency", "view_type": "tree",
            "action_id": action.id, "role_key": "config_admin", "company_id": self.env.company.id,
            "contract_json": empty, "status": "published",
        })
        Contract.create({
            "name": "test.empty.audit.scope.draft", "model": "res.currency", "view_type": "tree",
            "action_id": other_action.id, "role_key": "config_admin", "company_id": self.env.company.id,
            "contract_json": empty, "status": "draft",
        })
        Contract.create({
            "name": "test.empty.audit.scope.inactive", "model": "res.currency", "view_type": "tree",
            "action_id": other_action.id, "role_key": "config_admin", "company_id": self.env.company.id,
            "contract_json": empty, "status": "published", "active": False,
        })
        matching = self._audit(
            BusinessConfigListSearchAuditHandler, self._env(self.admin),
            model="res.currency", action_id=action.id, role_key="config_admin",
        )
        wrong_action = self._audit(
            BusinessConfigListSearchAuditHandler, self._env(self.admin),
            model="res.currency", action_id=other_action.id, role_key="config_admin",
        )
        wrong_role = self._audit(
            BusinessConfigListSearchAuditHandler, self._env(self.admin),
            model="res.currency", action_id=action.id, role_key="platform_admin",
        )
        self.assertTrue(matching["has_business_list_config"])
        self.assertEqual(matching["business_config_list_columns"], [])
        self.assertFalse(wrong_action["has_business_list_config"])
        self.assertFalse(wrong_role["has_business_list_config"])

    def test_effective_contracts_require_actual_view_presence_and_keep_apply_order(self):
        Contract = self.env["ui.business.config.contract"].sudo().with_context(active_test=False)

        def create(name, *, view_type=False, views=None, role_key="presence_final", action_id=False, view_id=False,
                   company_id=None, status="published", active=True, source="", priority=100):
            context = {"source": source} if source else {"source_status": "product_release"}
            return Contract.create({
                "name": name,
                "model": "res.partner",
                "view_type": view_type,
                "action_id": action_id,
                "view_id": view_id,
                "role_key": role_key,
                "company_id": company_id or self.env.company.id,
                "status": status,
                "active": active,
                "priority": priority,
                "contract_json": {"view_orchestration": {"context": context, "views": views or {}}},
            })

        create("presence.form.tenant", views={"form": {"fields": []}}, source="smart_core.lowcode.business_config", priority=999)
        create("presence.tree.product", views={"tree": {"columns": []}}, priority=999)
        create("presence.tree.tenant", view_type="tree", views={"tree": {"columns": [{"name": "name"}]}},
               source="smart_core.lowcode.business_config", priority=1)
        create("presence.multi.product", views={"form": {}, "tree": {}, "search": {}})
        create("presence.search.only", views={"search": {"filters": []}})
        create("presence.pivot.only", views={"pivot": {"measures": []}})
        create("presence.graph.only", views={"graph": {"dimensions": []}})
        create("presence.draft.tree", view_type="tree", views={"tree": {}}, status="draft")
        create("presence.inactive.tree", view_type="tree", views={"tree": {}}, active=False)
        create("presence.wrong.role", view_type="tree", views={"tree": {}}, role_key="other_role")
        wrong_action = self.env["ir.actions.act_window"].create({"name": "Presence wrong action", "res_model": "res.partner"})
        create("presence.wrong.action", view_type="tree", views={"tree": {}}, action_id=wrong_action.id)
        wrong_view = self.env["ir.ui.view"].create({
            "name": "presence.wrong.view", "model": "res.partner", "type": "tree", "arch": "<tree><field name='name'/></tree>",
        })
        create("presence.wrong.view", view_type="tree", views={"tree": {}}, view_id=wrong_view.id)
        other_company = self.env["res.company"].create({"name": "Presence Other Company"})
        create("presence.wrong.company", view_type="tree", views={"tree": {}}, company_id=other_company.id)

        def names(view_type):
            return [item.name for item in Contract._effective_view_orchestration_contracts(
                "res.partner", view_type=view_type, role_key="presence_final",
            )]

        tree_names = names("tree")
        for excluded in (
            "presence.form.tenant", "presence.draft.tree", "presence.inactive.tree",
            "presence.wrong.role", "presence.wrong.action", "presence.wrong.view", "presence.wrong.company",
        ):
            self.assertNotIn(excluded, tree_names)
        self.assertLess(tree_names.index("presence.tree.product"), tree_names.index("presence.tree.tenant"))
        self.assertIn("presence.multi.product", tree_names)
        self.assertIn("presence.multi.product", names("form"))
        self.assertIn("presence.multi.product", names("search"))
        self.assertNotIn("presence.tree.tenant", names("search"))
        self.assertEqual([name for name in names("pivot") if name.startswith("presence.")], ["presence.pivot.only"])
        self.assertEqual([name for name in names("graph") if name.startswith("presence.")], ["presence.graph.only"])

    def test_form_only_generic_contract_does_not_hide_suggestions_or_write(self):
        env = self._env(self.admin)
        Contract = env["ui.business.config.contract"].sudo()
        Contract.create({
            "name": "presence.audit.form.only", "model": "res.country", "view_type": False,
            "company_id": env.company.id, "role_key": "presence_audit",
            "contract_json": {"view_orchestration": {"views": {"form": {"fields": []}}}},
            "status": "published",
        })
        before = BusinessConfigMutationAuditSnapshotHandler(env).handle()["data"]["count"]
        absent = self._audit(
            BusinessConfigListSearchAuditHandler, env, model="res.country", role_key="presence_audit",
        )
        after = BusinessConfigMutationAuditSnapshotHandler(env).handle()["data"]["count"]
        self.assertFalse(absent["has_business_list_config"])
        self.assertFalse(absent["has_business_search_config"])
        self.assertTrue(absent["suggested_list_columns"] or absent["suggested_search_filters"])
        self.assertEqual(before, after)

        Contract.create({
            "name": "presence.audit.empty.tree", "model": "res.country", "view_type": "tree",
            "company_id": env.company.id, "role_key": "presence_audit",
            "contract_json": {"view_orchestration": {"views": {"tree": {"columns": []}}}},
            "status": "published",
        })
        Contract.create({
            "name": "presence.audit.empty.search", "model": "res.country", "view_type": "search",
            "company_id": env.company.id, "role_key": "presence_audit",
            "contract_json": {"view_orchestration": {"views": {"search": {"filters": [], "group_by": []}}}},
            "status": "published",
        })
        explicit_empty = self._audit(
            BusinessConfigListSearchAuditHandler, env, model="res.country", role_key="presence_audit",
        )
        self.assertTrue(explicit_empty["has_business_list_config"])
        self.assertTrue(explicit_empty["has_business_search_config"])
        self.assertEqual(explicit_empty["business_config_list_columns"], [])
        self.assertEqual(explicit_empty["business_config_search_filters"], [])
        self.assertEqual(explicit_empty["business_config_search_group_by"], [])
        self.assertEqual(explicit_empty["suggested_list_columns"], [])
        self.assertEqual(explicit_empty["suggested_search_filters"], [])

    def test_expired_published_batch_remains_rollback_capable_and_idempotent(self):
        env, change_set = self._open()
        self._stage(env, change_set, "test.change.set.long.term.rollback")
        validated = BusinessConfigChangeSetValidateHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin",
        }})
        self.assertEqual(validated["data"]["state"], "ready")
        published = BusinessConfigChangeSetPublishHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin", "request_id": "long-term-publish",
        }})
        self.assertTrue(published["ok"], published)
        record = env["ui.business.config.change.set"].browse(change_set["id"])
        record.write({"expires_at": fields.Datetime.now() - timedelta(hours=1)})
        get_result = BusinessConfigChangeSetGetHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin",
        }})
        self.assertEqual(get_result["data"]["state"], "published")
        other_user_result = BusinessConfigChangeSetRollbackHandler(self._env(self.other_admin)).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin", "request_id": "other-user-rollback",
        }})
        self.assertEqual(other_user_result["code"], 404)
        with self.assertRaises(ValidationError):
            BusinessConfigChangeSetRollbackHandler(env).handle(payload={"params": {
                "change_set_token": change_set["token"], "role_key": "platform_admin", "request_id": "other-role-rollback",
            }})
        other_company = self.env["res.company"].sudo().create({"name": "Change Set Isolation Company"})
        self.admin.sudo().write({"company_ids": [(4, other_company.id)]})
        other_company_env = self._env(self.admin)["res.users"].with_company(other_company).env
        other_company_result = BusinessConfigChangeSetRollbackHandler(other_company_env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin", "request_id": "other-company-rollback",
        }})
        self.assertEqual(other_company_result["code"], 404)
        record.write({"database_name": "other_database"})
        database_result = BusinessConfigChangeSetRollbackHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin", "request_id": "other-database-rollback",
        }})
        self.assertEqual(database_result["code"], 404)
        record.write({"database_name": self.env.cr.dbname})
        params = {"change_set_token": change_set["token"], "role_key": "config_admin", "request_id": "long-term-rollback"}
        first = BusinessConfigChangeSetRollbackHandler(env).handle(payload={"params": params})
        second = BusinessConfigChangeSetRollbackHandler(env).handle(payload={"params": params})
        self.assertTrue(first["ok"], first)
        self.assertEqual(second["data"]["id"], first["data"]["id"])
        self.assertEqual(self.env["ui.business.config.change.set"].sudo().search_count([
            ("publish_request_id", "=", "long-term-rollback"),
        ]), 1)

    def test_expired_draft_and_preview_are_rejected(self):
        env, change_set = self._open()
        self._stage(env, change_set, "test.change.set.expired.preview")
        record = env["ui.business.config.change.set"].browse(change_set["id"])
        record.write({"expires_at": fields.Datetime.now() - timedelta(minutes=1)})
        with self.assertRaises(ValidationError):
            record.assert_owner_scope(role_key="config_admin")
        record.write({"expires_at": fields.Datetime.now() + timedelta(hours=1)})
        preview = BusinessConfigChangeSetPreviewHandler(env).handle(payload={"params": {
            "change_set_token": change_set["token"], "role_key": "config_admin",
        }})
        self.assertTrue(preview["ok"], preview)
        record.write({"preview_expires_at": fields.Datetime.now() - timedelta(minutes=1)})
        preview_env = env(context={
            **env.context,
            "business_config_preview_token": preview["data"]["preview"]["token"],
            "business_config_preview_user_id": self.admin.id,
            "business_config_preview_role_key": "config_admin",
        })
        projected = preview_env["ui.business.config.contract"]._effective_view_orchestration_contracts(
            "res.partner", view_type="form", role_key="config_admin",
        )
        self.assertFalse(any(row.source_kind == "change_set_preview" for row in projected))

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
