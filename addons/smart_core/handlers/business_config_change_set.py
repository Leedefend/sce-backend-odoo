# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo import fields
from odoo.exceptions import AccessError, ValidationError

from ..core.base_handler import BaseIntentHandler
from ..model.ui_business_config_change_set import ACTIVE_CHANGE_SET_STATES, stable_payload_hash
from ..utils.backend_contract_boundaries import (
    BUSINESS_CONFIG_INTENTS,
    LOWCODE_SOURCE_STATUS_TENANT_RUNTIME,
    VIEW_ORCHESTRATION_SOURCE_TENANT_LOWCODING,
    ensure_view_orchestration_source,
)


BUSINESS_CONFIG_GROUP = "smart_core.group_smart_core_business_config_admin"
PLATFORM_ADMIN_GROUP = "smart_core.group_smart_core_admin"
CHANGE_SET_MODEL = "ui.business.config.change.set"
ITEM_MODEL = "ui.business.config.change.set.item"
MUTATION_AUDIT_MODEL = "ui.business.config.mutation.audit"
FORMAL_MUTATION_MODELS = (
    "ui.business.config.contract",
    "ui.business.config.contract.version",
    "ui.menu.config.policy",
    "ui.form.field.policy",
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _integer(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except Exception:
        return 0


class _ChangeSetBase(BaseIntentHandler):
    REQUIRED_GROUPS = [BUSINESS_CONFIG_GROUP]
    ACL_MODE = "explicit_check"
    SOURCE_AUTHORITIES = (CHANGE_SET_MODEL, ITEM_MODEL, "ui.business.config.contract")
    NO_BUSINESS_FACT_AUTHORITY = True

    def _ensure_access(self):
        user = self.env.user
        if int(getattr(user, "id", 0) or 0) == 1:
            return
        if user.has_group(BUSINESS_CONFIG_GROUP) or user.has_group(PLATFORM_ADMIN_GROUP):
            return
        raise AccessError("只有业务配置管理员或平台管理员可以操作配置变更集。")

    def _ok(self, data: dict) -> dict:
        return {
            "ok": True,
            "data": data,
            "meta": {
                "intent": self.INTENT_TYPE,
                "source_authority": {
                    "kind": "ui_business_config_change_set",
                    "authorities": list(self.SOURCE_AUTHORITIES),
                    "projection_only": False,
                    "write_proxy": True,
                    "no_business_fact_authority": True,
                    "runtime_carrier": self.INTENT_TYPE,
                },
            },
        }

    def _err(self, status: int, code: str, message: str, details: dict | None = None) -> dict:
        return {
            "ok": False,
            "code": status,
            "error": {"code": code, "reason_code": code, "message": message, "details": details or {}},
        }

    def _params(self, payload) -> dict:
        params = (payload or {}).get("params") if isinstance(payload, dict) else self.params
        return params if isinstance(params, dict) else {}

    def _owned(self, params: dict, *, required: bool = True):
        self._ensure_access()
        token = _text(params.get("change_set_token") or params.get("token"))
        change_set_id = _integer(params.get("change_set_id"))
        domain = [
            ("user_id", "=", self.env.user.id),
            ("company_id", "=", self.env.company.id),
            ("database_name", "=", self.env.cr.dbname),
        ]
        if token:
            domain.append(("token", "=", token))
        elif change_set_id:
            domain.append(("id", "=", change_set_id))
        elif required:
            return None
        record = self.env[CHANGE_SET_MODEL].sudo().search(domain, limit=1)
        if record:
            record.with_env(self.env).assert_owner_scope(role_key=_text(params.get("role_key")))
        return record

    def _target_contract(self, params: dict):
        Contract = self.env["ui.business.config.contract"].sudo()
        target_contract_id = _integer(params.get("current_contract_id"))
        if target_contract_id:
            return Contract.browse(target_contract_id).exists()
        domain = [
            ("name", "=", _text(params.get("contract_name") or params.get("target_key"))),
            ("company_id", "=", self.env.company.id),
        ]
        return Contract.search(domain, limit=1)

    def _menu_state_hash(self, draft_payload: dict, company_id: int) -> str:
        rows = draft_payload.get("rows") if isinstance(draft_payload, dict) else []
        menu_ids = sorted({_integer(row.get("menu_id")) for row in rows if isinstance(row, dict) and _integer(row.get("menu_id"))})
        policies = self.env["ui.menu.config.policy"].sudo().with_context(active_test=False).search([
            ("company_id", "=", company_id), ("menu_id", "in", menu_ids),
        ])
        by_menu = {int(policy.menu_id.id): policy for policy in policies}
        snapshot = []
        for menu_id in menu_ids:
            policy = by_menu.get(menu_id)
            snapshot.append({
                "menu_id": menu_id,
                "exists": bool(policy),
                "target_parent_menu_id": int(policy.target_parent_menu_id.id or 0) if policy else 0,
                "custom_label": str(policy.custom_label or "") if policy else "",
                "sequence_override": int(policy.sequence_override or 0) if policy else 0,
                "visible": bool(policy.visible) if policy else True,
                "role_group_ids": sorted(policy.role_group_ids.ids) if policy else [],
                "note": str(policy.note or "") if policy else "",
                "active": bool(policy.active) if policy else False,
            })
        return stable_payload_hash(snapshot)


class BusinessConfigChangeSetOpenHandler(_ChangeSetBase):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["change_set_open"]
    NON_IDEMPOTENT_ALLOWED = "creates or resumes an owner-scoped draft change set"

    def handle(self, payload=None, ctx=None):
        del ctx
        params = self._params(payload)
        self._ensure_access()
        role_key = _text(params.get("role_key"))
        ChangeSet = self.env[CHANGE_SET_MODEL].sudo()
        record = ChangeSet.search([
            ("user_id", "=", self.env.user.id),
            ("company_id", "=", self.env.company.id),
            ("database_name", "=", self.env.cr.dbname),
            ("role_key", "=", role_key or False),
            ("state", "in", list(ACTIVE_CHANGE_SET_STATES)),
            ("expires_at", ">", fields.Datetime.now()),
        ], order="id desc", limit=1)
        if not record:
            record = ChangeSet.create({
                "name": _text(params.get("name")) or "未发布配置变更",
                "user_id": self.env.user.id,
                "company_id": self.env.company.id,
                "role_key": role_key or False,
                "database_name": self.env.cr.dbname,
            })
        return self._ok(record.with_env(self.env).serialize())


class BusinessConfigChangeSetGetHandler(_ChangeSetBase):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["change_set_get"]

    def handle(self, payload=None, ctx=None):
        del ctx
        params = self._params(payload)
        record = self._owned(params)
        if not record:
            return self._err(404, "CHANGE_SET_NOT_FOUND", "未找到当前配置变更集。")
        return self._ok(record.with_env(self.env).serialize())


class BusinessConfigChangeSetStageHandler(_ChangeSetBase):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["change_set_stage"]
    NON_IDEMPOTENT_ALLOWED = "stores reversible draft payload without publishing runtime contracts"

    def handle(self, payload=None, ctx=None):
        del ctx
        params = self._params(payload)
        record = self._owned(params)
        if not record:
            return self._err(404, "CHANGE_SET_NOT_FOUND", "未找到当前配置变更集。")
        if record.state not in ACTIVE_CHANGE_SET_STATES:
            return self._err(409, "CHANGE_SET_NOT_EDITABLE", "当前变更集不可继续编辑。")
        config_type = _text(params.get("config_type"))
        if config_type not in {"form", "list", "search", "analysis", "menu"}:
            return self._err(400, "HIGH_RISK_OPERATION_REQUIRED", "该操作不属于可逆批量发布，请使用独立高风险操作。")
        draft_payload = params.get("draft_payload") if isinstance(params.get("draft_payload"), dict) else {}
        if not draft_payload:
            return self._err(422, "EMPTY_DRAFT_PAYLOAD", "草稿配置不能为空。")
        if config_type != "menu":
            draft_payload = ensure_view_orchestration_source(
                draft_payload,
                VIEW_ORCHESTRATION_SOURCE_TENANT_LOWCODING,
                LOWCODE_SOURCE_STATUS_TENANT_RUNTIME,
            )
        target_key = _text(params.get("target_key"))
        model = _text(params.get("model"))
        if not target_key or not model:
            return self._err(400, "MISSING_SCOPE", "变更项缺少页面或配置目标。")
        contract = self._target_contract(params)
        current_payload = contract.contract_json if contract else {}
        current_hash = self._menu_state_hash(draft_payload, record.company_id.id) if config_type == "menu" else stable_payload_hash(current_payload)
        requested_hash = _text(params.get("current_payload_hash"))
        if requested_hash and requested_hash != current_hash:
            return self._err(409, "STALE_CONFIG_HASH", "当前配置已被其他管理员更新。", {
                "expected_hash": requested_hash,
                "current_hash": current_hash,
            })
        values = {
            "change_set_id": record.id,
            "config_type": config_type,
            "target_key": target_key,
            "model": model,
            "view_type": _text(params.get("view_type")) or False,
            "action_id": _integer(params.get("action_id")),
            "view_id": _integer(params.get("view_id")),
            "role_key": _text(params.get("role_key")) or False,
            "target_contract_id": contract.id if contract else False,
            "base_version_no": int(contract.version_no or 0) if contract else 0,
            "base_payload_hash": current_hash,
            "draft_payload": draft_payload,
            "diff_summary": params.get("diff_summary") if isinstance(params.get("diff_summary"), dict) else {},
            "reversible": True,
            "risk_level": _text(params.get("risk_level")) if _text(params.get("risk_level")) in {"low", "medium", "high"} else "low",
            "validation_result": {},
            "publish_result": {},
        }
        Item = self.env[ITEM_MODEL].sudo()
        item = Item.search([("change_set_id", "=", record.id), ("target_key", "=", target_key)], limit=1)
        if item:
            item.write(values)
        else:
            item = Item.create(values)
        record.write({"state": "draft", "failure_message": False, "preview_token": False, "preview_expires_at": False})
        return self._ok(record.with_env(self.env).serialize())


class BusinessConfigChangeSetValidateHandler(_ChangeSetBase):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["change_set_validate"]
    NON_IDEMPOTENT_ALLOWED = "records validation results on owner-scoped draft items"

    def _validate_item(self, item) -> dict:
        errors = []
        payload = item.draft_payload if isinstance(item.draft_payload, dict) else {}
        if item.model not in self.env:
            errors.append("业务对象不存在")
        if item.config_type == "menu":
            rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
            if not rows:
                errors.append("菜单草稿没有可发布项")
        else:
            orchestration = payload.get("view_orchestration")
            if not isinstance(orchestration, dict):
                errors.append("草稿缺少正式页面编排契约")
            elif item.model in self.env:
                try:
                    Contract = self.env["ui.business.config.contract"]
                    Contract._check_view_orchestration_payload(payload)
                    unknown = Contract._unknown_view_orchestration_fields(payload, self.env[item.model]._fields)
                    if unknown:
                        errors.append("草稿引用不可用字段：%s" % ", ".join(unknown))
                except ValidationError as exc:
                    errors.append(str(exc))
        result = {"ok": not errors, "errors": errors}
        item.write({"validation_result": result})
        return result

    def handle(self, payload=None, ctx=None):
        del ctx
        params = self._params(payload)
        record = self._owned(params)
        if not record:
            return self._err(404, "CHANGE_SET_NOT_FOUND", "未找到当前配置变更集。")
        record.write({"state": "validating", "failure_message": False})
        results = [self._validate_item(item) for item in record.item_ids]
        ready = bool(results) and all(result["ok"] for result in results)
        record.write({"state": "ready" if ready else "failed", "failure_message": False if ready else "存在未通过校验的配置项"})
        return self._ok(record.with_env(self.env).serialize())


class BusinessConfigChangeSetPreviewHandler(BusinessConfigChangeSetValidateHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["change_set_preview"]
    NON_IDEMPOTENT_ALLOWED = "issues an expiring owner-scoped preview token without changing published contracts"

    def handle(self, payload=None, ctx=None):
        del ctx
        params = self._params(payload)
        trace_id = "preview-%s" % fields.Datetime.now().strftime("%Y%m%d%H%M%S%f")
        self.env = self.env(context={**self.env.context, "business_config_audit_trace": trace_id})
        record = self._owned(params)
        if not record:
            return self._err(404, "CHANGE_SET_NOT_FOUND", "未找到当前配置变更集。")
        results = [self._validate_item(item) for item in record.item_ids]
        if not results or not all(result["ok"] for result in results):
            record.write({"state": "failed", "failure_message": "草稿预览校验失败"})
            return self._err(422, "CHANGE_SET_VALIDATION_FAILED", "草稿校验未通过，不能预览。")
        record.write({"state": "ready", "failure_message": False})
        token = record.with_env(self.env).issue_preview_token()
        mutation_rows = self.env["ui.business.config.mutation.audit"].sudo().search([("trace_id", "=", trace_id)])
        contract_mutations = mutation_rows.filtered(lambda row: row.target_model == "ui.business.config.contract")
        version_mutations = mutation_rows.filtered(lambda row: row.target_model == "ui.business.config.contract.version")
        return self._ok({
            **record.with_env(self.env).serialize(),
            "preview": {
                "token": token,
                "expires_at": fields.Datetime.to_string(record.preview_expires_at),
                "creator_only": True,
                "company_id": int(record.company_id.id),
                "role_key": str(record.role_key or ""),
                "device": _text(params.get("device")) if _text(params.get("device")) in {"desktop", "tablet", "mobile"} else "desktop",
                "formal_contract_write_count": len(contract_mutations),
                "formal_version_write_count": len(version_mutations),
                "formal_config_mutation_count": len(mutation_rows),
                "mutation_trace_id": trace_id,
                "items": [item.serialize(include_payload=True) for item in record.item_ids],
            },
        })


class BusinessConfigChangeSetPublishHandler(_ChangeSetBase):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["change_set_publish"]
    NON_IDEMPOTENT_ALLOWED = "atomically publishes validated reversible configuration contracts"

    def _current_hash(self, item) -> str:
        if item.config_type == "menu":
            return self._menu_state_hash(item.draft_payload or {}, item.change_set_id.company_id.id)
        contract = item.target_contract_id.exists()
        return stable_payload_hash(contract.contract_json if contract else {})

    def _lock_publish_scope(self, record) -> None:
        self.env.cr.execute("SELECT id FROM ui_business_config_change_set WHERE id = %s FOR UPDATE", [record.id])
        for target_key in sorted(set(record.item_ids.mapped("target_key"))):
            self.env.cr.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ["ui.business.config:%s" % target_key])

    def _snapshot(self, record) -> dict:
        contracts = []
        menu_targets = set()
        for item in record.item_ids:
            contract = item.target_contract_id.exists()
            contracts.append({
                "item_id": int(item.id),
                "contract_id": int(contract.id or 0),
                "exists": bool(contract),
                "values": {
                    "contract_json": contract.contract_json or {},
                    "status": str(contract.status or "draft"),
                    "version_no": int(contract.version_no or 1),
                    "published_at": fields.Datetime.to_string(contract.published_at) if contract.published_at else False,
                } if contract else {},
            })
            if item.config_type == "menu":
                rows = item.draft_payload.get("rows") if isinstance(item.draft_payload, dict) else []
                menu_ids = [_integer(row.get("menu_id")) for row in rows if isinstance(row, dict)]
                menu_targets.update((record.company_id.id, menu_id) for menu_id in menu_ids if menu_id)
        Policy = self.env["ui.menu.config.policy"].sudo().with_context(active_test=False)
        policy_rows = []
        for company_id, menu_id in sorted(menu_targets):
            policy = Policy.search([("company_id", "=", company_id), ("menu_id", "=", menu_id)], limit=1)
            policy_rows.append({
                "id": int(policy.id or 0),
                "company_id": int(company_id),
                "menu_id": int(menu_id),
                "exists": bool(policy),
                "values": {
                    "target_parent_menu_id": int(policy.target_parent_menu_id.id or 0) or False,
                    "custom_label": str(policy.custom_label or "") or False,
                    "sequence_override": int(policy.sequence_override or 0),
                    "visible": bool(policy.visible),
                    "active": bool(policy.active),
                    "role_group_ids": [(6, 0, policy.role_group_ids.ids)],
                    "note": str(policy.note or "") or False,
                } if policy else {},
            })
        return {
            "contracts": contracts,
            "menu_policies": policy_rows,
        }

    def _publish_contract_item(self, item):
        Contract = self.env["ui.business.config.contract"].sudo()
        contract = item.target_contract_id.exists()
        values = {
            "name": item.target_key,
            "model": item.model,
            "view_type": item.view_type or False,
            "action_id": item.action_id or False,
            "view_id": item.view_id or False,
            "role_key": item.role_key or False,
            "company_id": item.change_set_id.company_id.id,
            "contract_json": item.draft_payload or {},
            "status": "draft",
        }
        if contract:
            contract.write(values)
        else:
            contract = Contract.create(values)
            item.write({"target_contract_id": contract.id})
        contract.action_publish()
        return {"contract_id": int(contract.id), "version_no": int(contract.version_no), "payload_hash": stable_payload_hash(contract.contract_json)}

    def _publish_menu_item(self, item):
        from .menu_configuration import MenuConfigurationSaveHandler

        params = item.draft_payload if isinstance(item.draft_payload, dict) else {}
        result = MenuConfigurationSaveHandler(env=self.env, payload={"params": params}).handle(payload={"params": params})
        if not isinstance(result, dict) or result.get("ok") is not True:
            error = result.get("error") if isinstance(result, dict) else {}
            raise ValidationError(_text((error or {}).get("message")) or "菜单配置发布失败")
        return result.get("data") or {}

    def _verify_runtime_item(self, item) -> bool:
        if item.config_type != "menu":
            contract = item.target_contract_id.exists()
            return bool(contract and contract.status == "published" and stable_payload_hash(contract.contract_json) == stable_payload_hash(item.draft_payload))
        Policy = self.env["ui.menu.config.policy"].sudo().with_context(active_test=False)
        rows = item.draft_payload.get("rows") if isinstance(item.draft_payload, dict) else []
        for row in rows:
            if not isinstance(row, dict):
                return False
            policy = Policy.search([
                ("company_id", "=", item.change_set_id.company_id.id),
                ("menu_id", "=", _integer(row.get("menu_id"))),
            ], limit=1)
            if not policy:
                return False
            if _integer(row.get("target_parent_menu_id")) != int(policy.target_parent_menu_id.id or 0):
                return False
            if _text(row.get("custom_label")) != _text(policy.custom_label):
                return False
            if _integer(row.get("sequence_override")) != int(policy.sequence_override or 0):
                return False
            if bool(row.get("visible", True)) != bool(policy.visible):
                return False
            if sorted({_integer(value) for value in (row.get("role_group_ids") or []) if _integer(value)}) != sorted(policy.role_group_ids.ids):
                return False
        return True

    def handle(self, payload=None, ctx=None):
        del ctx
        params = self._params(payload)
        record = self._owned(params)
        if not record:
            return self._err(404, "CHANGE_SET_NOT_FOUND", "未找到当前配置变更集。")
        request_id = _text(params.get("request_id"))
        if not request_id:
            return self._err(400, "REQUEST_ID_REQUIRED", "发布需要幂等请求ID。")
        if record.state == "published" and record.publish_request_id == request_id:
            return self._ok(record.with_env(self.env).serialize())
        if record.state != "ready":
            return self._err(409, "CHANGE_SET_NOT_READY", "请先完成变更集校验。")
        self._lock_publish_scope(record)
        record.invalidate_recordset(["state", "publish_request_id"])
        if record.state == "published" and record.publish_request_id == request_id:
            return self._ok(record.with_env(self.env).serialize())
        if record.state != "ready":
            return self._err(409, "CHANGE_SET_NOT_READY", "当前变更集已被其他发布请求处理。")
        conflicts = []
        for item in record.item_ids:
            current_hash = self._current_hash(item)
            if current_hash != item.base_payload_hash:
                conflicts.append({
                    "item_id": int(item.id), "target_key": item.target_key,
                    "diff_summary": item.diff_summary or {},
                    "expected_hash": item.base_payload_hash, "current_hash": current_hash,
                })
        if conflicts:
            return self._err(409, "CHANGE_SET_VERSION_CONFLICT", "配置已被其他管理员更新。", {"conflicts": conflicts})
        snapshot = self._snapshot(record)
        try:
            results = []
            with self.env.cr.savepoint():
                record.write({"state": "publishing", "publish_request_id": request_id, "failure_message": False})
                for item in record.item_ids.sorted("id"):
                    result = self._publish_menu_item(item) if item.config_type == "menu" else self._publish_contract_item(item)
                    if item.config_type != "menu":
                        for row in snapshot["contracts"]:
                            if int(row.get("item_id") or 0) == item.id and not row.get("exists"):
                                row["contract_id"] = int(result.get("contract_id") or 0)
                                break
                    runtime_verified = self._verify_runtime_item(item)
                    if not runtime_verified:
                        raise ValidationError("发布后运行态投影验证失败：%s" % item.target_key)
                    post_publish_hash = self._current_hash(item)
                    item.write({"publish_result": {**result, "post_publish_hash": post_publish_hash, "runtime_verified": True}})
                    results.append({"item_id": int(item.id), "config_type": item.config_type, "result": result, "post_publish_hash": post_publish_hash, "runtime_verified": True})
                record.write({
                    "state": "published",
                    "published_at": fields.Datetime.now(),
                    "rollback_snapshot_json": snapshot,
                    "publish_result_json": {"ok": True, "request_id": request_id, "items": results, "runtime_verified": True},
                })
        except Exception as exc:
            record.write({"state": "failed", "failure_message": str(exc), "publish_request_id": False})
            return self._err(422, "CHANGE_SET_ATOMIC_PUBLISH_FAILED", "发布失败，全部可逆配置均未生效。", {"message": str(exc)})
        return self._ok(record.with_env(self.env).serialize())


class BusinessConfigChangeSetRollbackHandler(_ChangeSetBase):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["change_set_rollback"]
    NON_IDEMPOTENT_ALLOWED = "creates a new rollback batch while preserving published history"

    def handle(self, payload=None, ctx=None):
        del ctx
        params = self._params(payload)
        request_id = _text(params.get("request_id"))
        if not request_id:
            return self._err(400, "REQUEST_ID_REQUIRED", "回滚需要幂等请求ID。")
        record = self._owned(params)
        if not record:
            return self._err(404, "CHANGE_SET_NOT_FOUND", "未找到当前配置变更集。")
        existing = self.env[CHANGE_SET_MODEL].sudo().search([
            ("user_id", "=", self.env.user.id),
            ("company_id", "=", self.env.company.id),
            ("database_name", "=", self.env.cr.dbname),
            ("publish_request_id", "=", request_id),
        ], limit=1)
        if existing:
            existing.with_env(self.env).assert_owner_scope(role_key=_text(params.get("role_key")))
            rollback_of = _integer((existing.publish_result_json or {}).get("rollback_of_change_set_id"))
            if rollback_of == record.id:
                return self._ok(existing.with_env(self.env).serialize())
            return self._err(409, "REQUEST_ID_REUSED", "回滚请求ID已用于其他操作。")
        if record.state != "published":
            return self._err(409, "CHANGE_SET_NOT_PUBLISHED", "只有已发布变更集可以回滚。")
        publish_handler = BusinessConfigChangeSetPublishHandler(env=self.env)
        conflicts = []
        for item in record.item_ids:
            expected_hash = _text((item.publish_result or {}).get("post_publish_hash"))
            current_hash = publish_handler._current_hash(item)
            if expected_hash and current_hash != expected_hash:
                conflicts.append({"item_id": int(item.id), "target_key": item.target_key, "expected_hash": expected_hash, "current_hash": current_hash})
        if conflicts:
            return self._err(409, "CHANGE_SET_ROLLBACK_CONFLICT", "配置已在发布后被更新，不能直接回滚。", {"conflicts": conflicts})
        snapshot = record.rollback_snapshot_json if isinstance(record.rollback_snapshot_json, dict) else {}
        restored = []
        with self.env.cr.savepoint():
            for row in snapshot.get("contracts") or []:
                contract_id = _integer(row.get("contract_id"))
                contract = self.env["ui.business.config.contract"].sudo().browse(contract_id).exists()
                if contract and row.get("exists"):
                    values = row.get("values") if isinstance(row.get("values"), dict) else {}
                    contract.write({"contract_json": values.get("contract_json") or {}, "status": "draft"})
                    contract.action_publish()
                    restored.append({"contract_id": contract_id, "version_no": int(contract.version_no)})
                elif contract and not row.get("exists"):
                    contract.write({"active": False})
                    restored.append({"contract_id": contract_id, "deactivated": True})
            for row in snapshot.get("menu_policies") or []:
                Policy = self.env["ui.menu.config.policy"].sudo().with_context(active_test=False)
                policy = Policy.browse(_integer(row.get("id"))).exists()
                if not policy:
                    policy = Policy.search([
                        ("company_id", "=", _integer(row.get("company_id"))),
                        ("menu_id", "=", _integer(row.get("menu_id"))),
                    ], limit=1)
                if policy and row.get("exists"):
                    policy.write(row.get("values") or {})
                elif policy and not row.get("exists"):
                    policy.unlink()
            rollback_batch = self.env[CHANGE_SET_MODEL].sudo().create({
                "name": "回滚：%s" % record.name,
                "user_id": self.env.user.id,
                "company_id": self.env.company.id,
                "role_key": record.role_key or False,
                "database_name": self.env.cr.dbname,
                "state": "published",
                "published_at": fields.Datetime.now(),
                "publish_request_id": request_id,
                "publish_result_json": {"ok": True, "rollback_of_change_set_id": int(record.id), "restored": restored, "runtime_verified": True},
            })
            record.write({"state": "superseded"})
        return self._ok(rollback_batch.with_env(self.env).serialize())


class BusinessConfigChangeSetDiscardHandler(_ChangeSetBase):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["change_set_discard"]
    NON_IDEMPOTENT_ALLOWED = "discards only owner-scoped unpublished draft state"

    def handle(self, payload=None, ctx=None):
        del ctx
        params = self._params(payload)
        record = self._owned(params)
        if not record:
            return self._err(404, "CHANGE_SET_NOT_FOUND", "未找到当前配置变更集。")
        if record.state in {"published", "superseded"}:
            return self._err(409, "CHANGE_SET_ALREADY_PUBLISHED", "已发布变更集不能放弃，只能回滚。")
        record.write({"state": "discarded", "preview_token": False, "preview_expires_at": False})
        return self._ok(record.with_env(self.env).serialize())


class BusinessConfigMutationAuditSnapshotHandler(_ChangeSetBase):
    """Read-only mutation counter used by browser safety acceptance."""

    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["mutation_audit_snapshot"]
    SOURCE_AUTHORITIES = (MUTATION_AUDIT_MODEL,)
    NO_BUSINESS_FACT_AUTHORITY = True

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        self._ensure_access()
        domain = [
            ("company_id", "=", self.env.company.id),
            ("target_model", "in", list(FORMAL_MUTATION_MODELS)),
        ]
        Audit = self.env[MUTATION_AUDIT_MODEL].sudo()
        rows = Audit.read_group(domain, ["target_model", "operation"], ["target_model", "operation"], lazy=False)
        counts = {
            "%s:%s" % (row.get("target_model") or "", row.get("operation") or ""): int(row.get("__count") or 0)
            for row in rows
        }
        latest = Audit.search(domain, order="id desc", limit=1)
        return self._ok({
            "company_id": int(self.env.company.id),
            "formal_models": list(FORMAL_MUTATION_MODELS),
            "count": int(Audit.search_count(domain)),
            "latest_id": int(latest.id or 0),
            "counts": counts,
        })
