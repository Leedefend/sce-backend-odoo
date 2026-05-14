# -*- coding: utf-8 -*-
"""Contract-backed form field configuration intents."""

from __future__ import annotations

import re
import time

from odoo.exceptions import ValidationError

from ..core.base_handler import BaseIntentHandler
from ..utils.reason_codes import REASON_MISSING_PARAMS, REASON_NOT_FOUND, REASON_OK, REASON_USER_ERROR


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

        action_id = int(params.get("action_id") or params.get("actionId") or 0)
        view_id = int(params.get("view_id") or params.get("viewId") or 0)
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
        model_rec = self.env["ir.model"].search([("model", "=", model)], limit=1)
        if not model_rec or model not in self.env:
            return self._err(404, "模型不存在：%s" % model, REASON_NOT_FOUND)
        if model_rec.transient:
            return self._err(400, "临时模型不能新增业务字段：%s" % model, REASON_USER_ERROR)

        action_id = int(params.get("action_id") or params.get("actionId") or 0)
        view_id = int(params.get("view_id") or params.get("viewId") or 0)
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
            "sequence": int(params.get("sequence") or 100),
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
