# -*- coding: utf-8 -*-
"""Contract-backed form field configuration intents."""

from __future__ import annotations

import re
import time

from odoo.exceptions import ValidationError

from ..core.base_handler import BaseIntentHandler
from ..core.request_params import parse_non_negative_int
from ..utils.reason_codes import REASON_MISSING_PARAMS, REASON_NOT_FOUND, REASON_OK, REASON_USER_ERROR


def _optional_non_negative_int(params: dict, *keys: str):
    raw = None
    for key in keys:
        if key in params:
            raw = params.get(key)
            break
    value, error = parse_non_negative_int(raw, allow_empty=True)
    if error:
        return None, keys[0]
    return int(value or 0), None


class FormFieldPolicySetHandler(BaseIntentHandler):
    INTENT_TYPE = "ui.form_field_policy.set"
    DESCRIPTION = "Set current form field visibility policy from a contract action."
    REQUIRED_GROUPS = ["smart_core.group_smart_core_admin"]
    SOURCE_KIND = "ui_form_field_policy_contract_action"
    SOURCE_AUTHORITIES = ("ui.form.field.policy", "ir.model.fields", "ir.actions.act_window", "ir.ui.view")
    NON_IDEMPOTENT_ALLOWED = "field policy writes configuration state"

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "write_proxy": True,
            "no_business_fact_authority": True,
            "runtime_carrier": self.INTENT_TYPE,
        }

    def _model_record(self, model_name: str):
        return self.env["ir.model"].search([("model", "=", model_name)], limit=1)

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = str(params.get("model") or "").strip()
        field_name = str(params.get("field_name") or params.get("fieldName") or "").strip()
        if not model or not field_name:
            return self._err(400, "缺少 model 或 field_name", REASON_MISSING_PARAMS)
        action_id, invalid_field = _optional_non_negative_int(params, "action_id", "actionId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        view_id, invalid_field = _optional_non_negative_int(params, "view_id", "viewId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        if model not in self.env:
            return self._err(404, "模型不存在：%s" % model, REASON_NOT_FOUND)
        if field_name not in self.env[model]._fields:
            return self._err(404, "字段不存在：%s.%s" % (model, field_name), REASON_NOT_FOUND)
        model_rec = self._model_record(model)
        if not model_rec or model_rec.transient:
            return self._err(400, "临时模型不能配置表单字段：%s" % model, REASON_USER_ERROR)
        field_rec = self.env["ir.model.fields"].search([("model", "=", model), ("name", "=", field_name)], limit=1)
        if field_rec and field_rec.ttype == "binary":
            return self._err(400, "二进制字段不能作为业务表单字段配置：%s.%s" % (model, field_name), REASON_USER_ERROR)

        visible = params.get("visible")
        visible = str(visible).strip().lower() not in {"0", "false", "no", "hide", "hidden"}
        label = str(params.get("label") or (field_rec.field_description if field_rec else field_name) or field_name).strip()

        Policy = self.env["ui.form.field.policy"]
        Policy.check_access_rights("create")
        domain = [
            ("active", "=", True),
            ("model", "=", model),
            ("field_name", "=", field_name),
            ("company_id", "=", self.env.company.id),
            ("action_id", "=", action_id or False),
            ("view_id", "=", view_id or False),
        ]
        policy = Policy.search(domain, limit=1)
        vals = {
            "active": True,
            "model_id": model_rec.id,
            "model": model,
            "field_id": field_rec.id if field_rec else False,
            "field_name": field_name,
            "label": label,
            "visible": bool(visible),
            "company_id": self.env.company.id,
            "action_id": action_id or False,
            "view_id": view_id or False,
        }
        if policy:
            policy.check_access_rights("write")
            policy.write(vals)
        else:
            policy = Policy.create(vals)
        return {
            "ok": True,
            "data": {
                "id": int(policy.id),
                "model": model,
                "field_name": field_name,
                "visible": bool(policy.visible),
            },
            "meta": {"intent": self.INTENT_TYPE, "reason_code": REASON_OK, "source_authority": self._source_authority_contract()},
        }


class FormCustomFieldCreateHandler(BaseIntentHandler):
    INTENT_TYPE = "ui.form_custom_field.create"
    DESCRIPTION = "Create a safe custom form field from a contract action."
    REQUIRED_GROUPS = ["smart_core.group_smart_core_admin"]
    SOURCE_KIND = "ui_form_custom_field_contract_action"
    SOURCE_AUTHORITIES = ("ui.form.custom.field.wizard", "ir.model.fields", "ui.form.field.policy")
    NON_IDEMPOTENT_ALLOWED = "custom field creation changes configuration metadata"

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "write_proxy": True,
            "no_business_fact_authority": True,
            "runtime_carrier": self.INTENT_TYPE,
        }

    def _suggest_field_name(self, model: str, label: str) -> str:
        ascii_slug = re.sub(r"[^a-z0-9_]+", "_", str(label or "").lower()).strip("_")
        if not ascii_slug or not re.match(r"^[a-z]", ascii_slug):
            ascii_slug = "custom_field"
        ascii_slug = re.sub(r"_+", "_", ascii_slug)[:40].strip("_") or "custom_field"
        base = "x_%s" % ascii_slug
        candidate = base
        index = 2
        Field = self.env["ir.model.fields"].sudo()
        while (
            candidate in self.env[model]._fields
            or Field.search_count([("model", "=", model), ("name", "=", candidate)])
        ):
            candidate = "%s_%s" % (base[:48], index)
            index += 1
            if index > 200:
                candidate = "%s_%s" % (base[:42], int(time.time()) % 100000)
                if (
                    candidate not in self.env[model]._fields
                    and not Field.search_count([("model", "=", model), ("name", "=", candidate)])
                ):
                    break
        return candidate[:56]

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = str(params.get("model") or "").strip()
        label = str(params.get("label") or "").strip()
        if not model or not label:
            return self._err(400, "缺少 model 或 label", REASON_MISSING_PARAMS)
        action_id, invalid_field = _optional_non_negative_int(params, "action_id", "actionId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        view_id, invalid_field = _optional_non_negative_int(params, "view_id", "viewId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        sequence, invalid_field = _optional_non_negative_int(params, "sequence")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        model_rec = self.env["ir.model"].search([("model", "=", model)], limit=1)
        if not model_rec or model not in self.env:
            return self._err(404, "模型不存在：%s" % model, REASON_NOT_FOUND)
        if model_rec.transient:
            return self._err(400, "临时模型不能新增业务字段：%s" % model, REASON_USER_ERROR)
        field_name = str(params.get("field_name") or params.get("fieldName") or "").strip()
        if not field_name or field_name in {"x_", "x_custom_field"}:
            field_name = self._suggest_field_name(model, label)
        Wizard = self.env["ui.form.custom.field.wizard"]
        Wizard.check_access_rights("create")
        wizard = Wizard.create({
            "model_id": model_rec.id,
            "field_name": field_name,
            "label": label,
            "ttype": str(params.get("ttype") or "char").strip() or "char",
            "action_id": action_id or False,
            "view_id": view_id or False,
            "group_title": str(params.get("group_title") or "业务配置字段").strip() or "业务配置字段",
            "sequence": sequence if sequence > 0 else 100,
            "active_policy": True,
            "company_id": self.env.company.id,
        })
        try:
            result = wizard.action_create_field_policy()
        except ValidationError as exc:
            return self._err(400, str(exc), REASON_USER_ERROR)
        try:
            self.env.registry.signal_changes()
        except Exception:
            pass
        policy_id = int(result.get("res_id") or 0) if isinstance(result, dict) else 0
        policy = self.env["ui.form.field.policy"].browse(policy_id).exists() if policy_id else self.env["ui.form.field.policy"]
        return {
            "ok": True,
            "data": {
                "policy_id": int(policy.id or 0),
                "field_name": str(policy.field_name or wizard.field_name or ""),
                "model": model,
            },
            "meta": {"intent": self.INTENT_TYPE, "reason_code": REASON_OK, "source_authority": self._source_authority_contract()},
        }


class FormFieldOrderSetHandler(BaseIntentHandler):
    INTENT_TYPE = "ui.form_field_order.set"
    DESCRIPTION = "Set form field order for current form scope from contract action."
    REQUIRED_GROUPS = ["smart_core.group_smart_core_admin"]
    SOURCE_KIND = "ui_form_field_order_contract_action"
    SOURCE_AUTHORITIES = ("ui.form.field.policy", "ir.model.fields", "ir.actions.act_window", "ir.ui.view")
    NON_IDEMPOTENT_ALLOWED = "field order writes configuration state"

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "write_proxy": True,
            "no_business_fact_authority": True,
            "runtime_carrier": self.INTENT_TYPE,
        }

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = str(params.get("model") or "").strip()
        if not model:
            return self._err(400, "缺少 model", REASON_MISSING_PARAMS)
        action_id, invalid_field = _optional_non_negative_int(params, "action_id", "actionId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        view_id, invalid_field = _optional_non_negative_int(params, "view_id", "viewId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        raw_field_order = params.get("field_order") or params.get("fieldOrder")
        if not isinstance(raw_field_order, list) or not raw_field_order:
            return self._err(400, "field_order 必须是非空数组", REASON_USER_ERROR)
        field_order = [str(name or "").strip() for name in raw_field_order]
        field_order = [name for name in field_order if name]
        if not field_order:
            return self._err(400, "field_order 不能为空", REASON_USER_ERROR)
        if model not in self.env:
            return self._err(404, "模型不存在：%s" % model, REASON_NOT_FOUND)
        unknown = [name for name in field_order if name not in self.env[model]._fields]
        if unknown:
            return self._err(404, "字段不存在：%s.%s" % (model, unknown[0]), REASON_NOT_FOUND)
        model_rec = self.env["ir.model"].search([("model", "=", model)], limit=1)
        if not model_rec or model_rec.transient:
            return self._err(400, "临时模型不能配置表单字段：%s" % model, REASON_USER_ERROR)

        Field = self.env["ir.model.fields"]
        field_rows = Field.search([("model", "=", model), ("name", "in", field_order)])
        field_map = {str(row.name or "").strip(): row for row in field_rows}
        Policy = self.env["ui.form.field.policy"]
        Policy.check_access_rights("create")
        policies = Policy.search([
            ("active", "=", True),
            ("model", "=", model),
            ("field_name", "in", field_order),
            ("company_id", "=", self.env.company.id),
            ("action_id", "=", action_id or False),
            ("view_id", "=", view_id or False),
        ])
        policy_map = {str(row.field_name or "").strip(): row for row in policies}
        for index, field_name in enumerate(field_order):
            sequence = (index + 1) * 10
            policy = policy_map.get(field_name)
            if policy:
                policy.check_access_rights("write")
                policy.write({"sequence": sequence})
                continue
            field_rec = field_map.get(field_name)
            label = str((field_rec.field_description if field_rec else field_name) or field_name).strip()
            Policy.create({
                "active": True,
                "model_id": model_rec.id,
                "model": model,
                "field_id": field_rec.id if field_rec else False,
                "field_name": field_name,
                "label": label,
                "visible": True,
                "sequence": sequence,
                "company_id": self.env.company.id,
                "action_id": action_id or False,
                "view_id": view_id or False,
            })
        return {
            "ok": True,
            "data": {"model": model, "field_order": field_order, "updated_count": len(field_order)},
            "meta": {"intent": self.INTENT_TYPE, "reason_code": REASON_OK, "source_authority": self._source_authority_contract()},
        }


class FormFieldConfigBatchSetHandler(FormFieldOrderSetHandler):
    INTENT_TYPE = "ui.form_field_config.batch_set"
    DESCRIPTION = "Batch set form field order and visibility for current form scope."

    def handle(self, payload=None, ctx=None):
        order_result = super().handle(payload=payload, ctx=ctx)
        if not order_result.get("ok"):
            return order_result
        params = self.params if isinstance(self.params, dict) else {}
        visibility = params.get("field_visibility") or params.get("fieldVisibility")
        if visibility and isinstance(visibility, dict):
            Policy = self.env["ui.form.field.policy"]
            model = str(params.get("model") or "").strip()
            action_id, _ = _optional_non_negative_int(params, "action_id", "actionId")
            view_id, _ = _optional_non_negative_int(params, "view_id", "viewId")
            updates = 0
            for field_name, raw_visible in visibility.items():
                name = str(field_name or "").strip()
                if not name:
                    continue
                visible = str(raw_visible).strip().lower() not in {"0", "false", "no", "hide", "hidden"}
                policy = Policy.search([
                    ("active", "=", True),
                    ("model", "=", model),
                    ("field_name", "=", name),
                    ("company_id", "=", self.env.company.id),
                    ("action_id", "=", action_id or False),
                    ("view_id", "=", view_id or False),
                ], limit=1)
                if policy:
                    policy.write({"visible": bool(visible)})
                    updates += 1
            order_result["data"]["visibility_updated_count"] = updates
        order_result["meta"]["intent"] = self.INTENT_TYPE
        order_result["meta"]["low_code_config"] = {
            "enabled": True,
            "scope": "current_form",
            "capabilities": ["field_order", "field_visibility"],
        }
        return order_result


class BusinessConfigLowCodeApplyHandler(FormFieldConfigBatchSetHandler):
    INTENT_TYPE = "ui.business_config.lowcode.apply"
    DESCRIPTION = "Apply low-code business form configuration in current form scope."

    def handle(self, payload=None, ctx=None):
        result = super().handle(payload=payload, ctx=ctx)
        if not isinstance(result, dict):
            return result
        meta = result.get("meta") if isinstance(result.get("meta"), dict) else {}
        meta["intent"] = self.INTENT_TYPE
        meta["delivery_profile"] = "business_low_code_form_config"
        result["meta"] = meta
        return result


class BusinessConfigContractSaveHandler(BaseIntentHandler):
    INTENT_TYPE = "ui.business_config.contract.save"
    DESCRIPTION = "Save low-code business config contract payload into contract model."
    REQUIRED_GROUPS = ["smart_core.group_smart_core_admin"]
    SOURCE_KIND = "ui_business_config_contract_save"
    SOURCE_AUTHORITIES = ("ui.business.config.contract", "ui.business.config.contract.version")
    NON_IDEMPOTENT_ALLOWED = "business config contract is mutable authoring state"

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "write_proxy": True,
            "no_business_fact_authority": True,
            "runtime_carrier": self.INTENT_TYPE,
        }

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        name = str(params.get("name") or "").strip()
        model = str(params.get("model") or "").strip()
        contract_json = params.get("contract_json") or params.get("contractJson")
        publish = bool(params.get("publish") is True)
        if not name or not model:
            return self._err(400, "缺少 name 或 model", REASON_MISSING_PARAMS)
        if not isinstance(contract_json, dict):
            return self._err(400, "contract_json 必须是对象", REASON_USER_ERROR)
        precheck = self._precheck_contract_payload(contract_json)
        if precheck["errors"]:
            return self._err(400, "contract_json 预检失败", REASON_USER_ERROR)
        Contract = self.env["ui.business.config.contract"]
        domain = [("name", "=", name), ("company_id", "=", self.env.company.id)]
        rec = Contract.search(domain, limit=1)
        vals = {
            "name": name,
            "model": model,
            "contract_json": contract_json,
            "status": "published" if publish else "draft",
        }
        try:
            if rec:
                rec.write(vals)
            else:
                rec = Contract.create(vals)
            if publish:
                rec.action_publish()
        except ValidationError as exc:
            return self._err(400, str(exc), REASON_USER_ERROR)
        return {
            "ok": True,
            "data": {
                "id": int(rec.id),
                "name": str(rec.name or ""),
                "model": str(rec.model or ""),
                "status": str(rec.status or "draft"),
                "version_no": int(rec.version_no or 1),
                "precheck": precheck,
            },
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract(), "reason_code": REASON_OK},
        }

    def _precheck_contract_payload(self, payload: dict) -> dict:
        warnings = []
        errors = []
        objects = payload.get("objects") if isinstance(payload.get("objects"), list) else []
        if not objects:
            warnings.append("objects 为空，契约不会产生业务对象配置。")
        for obj in objects:
            if not isinstance(obj, dict):
                errors.append("objects 包含非对象节点。")
                continue
            obj_name = str(obj.get("name") or "").strip()
            if not obj_name:
                errors.append("存在未命名业务对象。")
            fields_rows = obj.get("fields") if isinstance(obj.get("fields"), list) else []
            if not fields_rows:
                warnings.append("业务对象 %s 未配置字段。" % (obj_name or "<unknown>"))
        rules = payload.get("rules") if isinstance(payload.get("rules"), list) else []
        for idx, rule in enumerate(rules):
            if not isinstance(rule, dict):
                errors.append("rules[%s] 非对象。" % idx)
                continue
            if not str(rule.get("name") or "").strip():
                warnings.append("rules[%s] 缺少 name。" % idx)
            if str(rule.get("trigger") or "").strip() == "scheduled" and not rule.get("cron"):
                warnings.append("rules[%s] 为 scheduled 但未配置 cron。" % idx)
        return {"warnings": warnings, "errors": errors}


class BusinessConfigContractGetHandler(BaseIntentHandler):
    INTENT_TYPE = "ui.business_config.contract.get"
    DESCRIPTION = "Get low-code business config contract payload by name/model."
    REQUIRED_GROUPS = ["smart_core.group_smart_core_admin"]
    SOURCE_KIND = "ui_business_config_contract_get"
    SOURCE_AUTHORITIES = ("ui.business.config.contract", "ui.business.config.contract.version")

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": True,
            "runtime_carrier": self.INTENT_TYPE,
        }

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        name = str(params.get("name") or "").strip()
        model = str(params.get("model") or "").strip()
        if not name and not model:
            return self._err(400, "name 或 model 至少提供一个", REASON_MISSING_PARAMS)
        domain = [("company_id", "=", self.env.company.id)]
        if name:
            domain.append(("name", "=", name))
        if model:
            domain.append(("model", "=", model))
        rec = self.env["ui.business.config.contract"].search(domain, limit=1)
        if not rec:
            return self._err(404, "未找到业务配置契约", REASON_NOT_FOUND)
        return {
            "ok": True,
            "data": {
                "id": int(rec.id),
                "name": str(rec.name or ""),
                "model": str(rec.model or ""),
                "status": str(rec.status or "draft"),
                "version_no": int(rec.version_no or 1),
                "contract_json": rec.contract_json or {},
            },
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract(), "reason_code": REASON_OK},
        }


class BusinessConfigContractListHandler(BaseIntentHandler):
    INTENT_TYPE = "ui.business_config.contract.list"
    DESCRIPTION = "List low-code business config contracts in current company."
    REQUIRED_GROUPS = ["smart_core.group_smart_core_admin"]
    SOURCE_KIND = "ui_business_config_contract_list"
    SOURCE_AUTHORITIES = ("ui.business.config.contract",)

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": True,
            "runtime_carrier": self.INTENT_TYPE,
        }

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = str(params.get("model") or "").strip()
        domain = [("company_id", "=", self.env.company.id)]
        if model:
            domain.append(("model", "=", model))
        rows = self.env["ui.business.config.contract"].search(domain, limit=100, order="write_date desc, id desc")
        data = [{
            "id": int(rec.id),
            "name": str(rec.name or ""),
            "model": str(rec.model or ""),
            "status": str(rec.status or "draft"),
            "version_no": int(rec.version_no or 1),
        } for rec in rows]
        return {
            "ok": True,
            "data": {"items": data},
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract(), "reason_code": REASON_OK},
        }


class BusinessConfigContractPublishHandler(BaseIntentHandler):
    INTENT_TYPE = "ui.business_config.contract.publish"
    DESCRIPTION = "Publish a low-code business config contract by name/model."
    REQUIRED_GROUPS = ["smart_core.group_smart_core_admin"]

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        name = str(params.get("name") or "").strip()
        model = str(params.get("model") or "").strip()
        if not name and not model:
            return self._err(400, "name 或 model 至少提供一个", REASON_MISSING_PARAMS)
        domain = [("company_id", "=", self.env.company.id)]
        if name:
            domain.append(("name", "=", name))
        if model:
            domain.append(("model", "=", model))
        rec = self.env["ui.business.config.contract"].search(domain, limit=1)
        if not rec:
            return self._err(404, "未找到业务配置契约", REASON_NOT_FOUND)
        rec.action_publish()
        return {
            "ok": True,
            "data": {
                "id": int(rec.id),
                "name": str(rec.name or ""),
                "model": str(rec.model or ""),
                "status": str(rec.status or "draft"),
                "version_no": int(rec.version_no or 1),
            },
            "meta": {"intent": self.INTENT_TYPE, "reason_code": REASON_OK},
        }


class BusinessConfigContractRollbackHandler(BaseIntentHandler):
    INTENT_TYPE = "ui.business_config.contract.rollback"
    DESCRIPTION = "Rollback a low-code business config contract to previous snapshot."
    REQUIRED_GROUPS = ["smart_core.group_smart_core_admin"]

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        name = str(params.get("name") or "").strip()
        model = str(params.get("model") or "").strip()
        if not name and not model:
            return self._err(400, "name 或 model 至少提供一个", REASON_MISSING_PARAMS)
        domain = [("company_id", "=", self.env.company.id)]
        if name:
            domain.append(("name", "=", name))
        if model:
            domain.append(("model", "=", model))
        rec = self.env["ui.business.config.contract"].search(domain, limit=1)
        if not rec:
            return self._err(404, "未找到业务配置契约", REASON_NOT_FOUND)
        versions = self.env["ui.business.config.contract.version"].search(
            [("contract_id", "=", rec.id)], order="version_no desc, id desc", limit=2
        )
        if len(versions) < 2:
            return self._err(400, "无可回滚版本", REASON_USER_ERROR)
        target = versions[1]
        rec.write({
            "contract_json": target.snapshot_json or {},
            "status": "draft",
            "version_no": int(target.version_no or rec.version_no or 1),
        })
        return {
            "ok": True,
            "data": {
                "id": int(rec.id),
                "name": str(rec.name or ""),
                "model": str(rec.model or ""),
                "status": str(rec.status or "draft"),
                "version_no": int(rec.version_no or 1),
                "rolled_back_to_version": int(target.version_no or 1),
            },
            "meta": {"intent": self.INTENT_TYPE, "reason_code": REASON_OK},
        }
