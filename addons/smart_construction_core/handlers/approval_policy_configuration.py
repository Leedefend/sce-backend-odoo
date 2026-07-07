# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import re
from typing import Any

from odoo.exceptions import AccessError, ValidationError

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.utils.backend_contract_boundaries import (
    APPROVAL_POLICY_INTENTS,
    APPROVAL_POLICY_RUNTIME_SOURCE,
    APPROVAL_POLICY_SOURCE_TENANT_LOWCODING,
)


_logger = logging.getLogger(__name__)


BUSINESS_CONFIG_GROUPS = [
    "smart_core.group_smart_core_business_config_admin",
    "smart_core.group_smart_core_admin",
    "smart_construction_core.group_sc_cap_business_config_admin",
]

def _to_text(value: Any) -> str:
    return str(value or "").strip()


def _to_int(value: Any) -> int:
    try:
        parsed = int(value or 0)
    except Exception:
        return 0
    return parsed if parsed > 0 else 0


def _ref_id(value: Any) -> int:
    return _to_int(getattr(value, "id", value))


def _bool_param(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _float_or_false(value: Any):
    text = _to_text(value)
    if not text:
        return False
    try:
        parsed = float(text)
    except Exception:
        raise ValidationError("审批金额条件无效。")
    if parsed < 0:
        raise ValidationError("审批金额条件不能小于 0。")
    return parsed


def _iter_records(records):
    if not records:
        return []
    try:
        return list(records)
    except TypeError:
        return [records]


class ApprovalPolicyConfigGetHandler(BaseIntentHandler):
    INTENT_TYPE = APPROVAL_POLICY_INTENTS["config_get"]
    DESCRIPTION = "读取当前业务审批启用配置"
    VERSION = "1.0.0"
    ACL_MODE = "explicit_check"
    REQUIRED_GROUPS = BUSINESS_CONFIG_GROUPS
    SOURCE_KIND = "sc_approval_policy_low_code_projection"
    SOURCE_AUTHORITIES = ("sc.approval.policy", "res.groups", "base_tier_validation")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
            "boundary": "industry_policy_runtime",
            "lowcode_boundary": "approval_policy",
            "policy_source": APPROVAL_POLICY_RUNTIME_SOURCE,
            "lowcode_source": APPROVAL_POLICY_SOURCE_TENANT_LOWCODING,
        }

    def _ensure_access(self):
        user = self.env.user
        if _to_int(getattr(user, "id", 0)) == 1:
            return
        if any(user.has_group(xmlid) for xmlid in BUSINESS_CONFIG_GROUPS):
            return
        raise AccessError("只有业务配置管理员或平台管理员可以配置审批规则。")

    def _policy_model(self):
        if "sc.approval.policy" not in self.env:
            raise ValidationError("当前行业模块未安装审批规则能力。")
        return self.env["sc.approval.policy"].sudo()

    def _selection_options(self, Policy, field_name: str) -> list[dict]:
        try:
            meta = Policy.fields_get([field_name]).get(field_name, {})
            selection = meta.get("selection") or []
        except Exception:
            selection = []
        return [{"value": _to_text(key), "label": _to_text(label or key)} for key, label in selection if _to_text(key)]

    def _scope_options(self, Policy) -> list[dict]:
        if hasattr(Policy, "_selection_approval_scope"):
            try:
                selection = Policy._selection_approval_scope()
            except Exception:
                selection = []
        else:
            selection = []
        return [{"value": _to_text(key), "label": _to_text(label or key)} for key, label in selection if _to_text(key)]

    def _model_label(self, Policy, model: str) -> str:
        for row in self._selection_options(Policy, "target_model"):
            if row["value"] == model:
                return row["label"]
        if model and model in self.env:
            try:
                return _to_text(self.env[model]._description) or model
            except Exception:
                _logger.debug("Unable to resolve approval policy target model label.", exc_info=True)
        return model

    def _find_policy(self, Policy, model: str):
        if not model:
            return Policy.browse()
        SearchPolicy = Policy.with_context(active_test=False) if hasattr(Policy, "with_context") else Policy
        domain = [
            ("target_model", "=", model),
            "|",
            ("company_id", "=", self.env.company.id),
            ("company_id", "=", False),
        ]
        return SearchPolicy.search(domain, order="company_id desc, sequence, id", limit=1)

    def _scope_label_map(self, Policy) -> dict:
        return {row["value"]: row["label"] for row in self._scope_options(Policy)}

    def _sorted_steps(self, policy):
        steps = getattr(policy, "step_ids", None)
        if not steps:
            return []
        if hasattr(steps, "sorted"):
            try:
                return _iter_records(steps.sorted(lambda row: (_to_int(getattr(row, "sequence", 0)), _ref_id(row))))
            except Exception:
                try:
                    return _iter_records(steps.sorted("sequence"))
                except Exception:
                    _logger.debug("Unable to sort approval policy steps with Odoo sorted helper.", exc_info=True)
        return sorted(_iter_records(steps), key=lambda row: (_to_int(getattr(row, "sequence", 0)), _ref_id(row)))

    def _serialize_steps(self, Policy, policy) -> list[dict]:
        labels = self._scope_label_map(Policy)
        rows = []
        for step in self._sorted_steps(policy):
            scope_key = _to_text(getattr(step, "approval_scope_key", ""))
            rows.append({
                "id": _ref_id(step),
                "name": _to_text(getattr(step, "name", "")),
                "approval_scope_key": scope_key,
                "approval_scope_label": labels.get(scope_key, scope_key),
                "sequence": _to_int(getattr(step, "sequence", 0)),
                "active": bool(getattr(step, "active", True)),
                "amount_min": getattr(step, "amount_min", False) or False,
                "amount_max": getattr(step, "amount_max", False) or False,
                "condition_note": _to_text(getattr(step, "condition_note", "")),
                "note": _to_text(getattr(step, "note", "")),
            })
        return rows

    def _serialize_policy(self, Policy, policy, model: str) -> dict:
        if not policy:
            return {
                "id": 0,
                "name": "",
                "target_model": model,
                "target_model_label": self._model_label(Policy, model),
                "approval_required": False,
                "mode": "none",
                "trigger": "submit",
                "runtime_state": "policy_only",
                "manager_scope_key": "",
                "step_count": 0,
                "steps": [],
                "active": True,
                "exists": False,
            }
        steps = self._serialize_steps(Policy, policy)
        return {
            "id": _ref_id(policy),
            "name": _to_text(getattr(policy, "name", "")),
            "target_model": _to_text(getattr(policy, "target_model", "")) or model,
            "target_model_label": self._model_label(Policy, _to_text(getattr(policy, "target_model", "")) or model),
            "approval_required": bool(getattr(policy, "approval_required", False)),
            "mode": _to_text(getattr(policy, "mode", "")) or "none",
            "trigger": _to_text(getattr(policy, "trigger", "")) or "submit",
            "runtime_state": _to_text(getattr(policy, "runtime_state", "")) or "policy_only",
            "manager_scope_key": _to_text(getattr(policy, "manager_scope_key", "")),
            "step_count": len([step for step in steps if step["active"]]),
            "steps": steps,
            "active": bool(getattr(policy, "active", True)),
            "exists": True,
        }

    def _payload(self, Policy, model: str, policy=None) -> dict:
        policy = policy if policy is not None else self._find_policy(Policy, model)
        required = False
        if model and hasattr(Policy, "is_approval_required"):
            try:
                required = bool(Policy.is_approval_required(model, company=self.env.company))
            except Exception:
                required = False
        return {
            "model": model,
            "policy": self._serialize_policy(Policy, policy, model),
            "runtime_approval_required": required,
            "mode_options": self._selection_options(Policy, "mode"),
            "trigger_options": self._selection_options(Policy, "trigger"),
            "scope_options": self._scope_options(Policy),
            "boundary": "industry_policy_runtime",
        }

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        self._ensure_access()
        params = self.params if isinstance(self.params, dict) else {}
        model = _to_text(params.get("model") or params.get("target_model") or params.get("targetModel"))
        if not model:
            raise ValidationError("请选择需要配置审批的业务。")
        Policy = self._policy_model()
        return {"ok": True, "data": self._payload(Policy, model), "meta": {"intent": self.INTENT_TYPE, "source_authority": self.source_authority_contract()}}


class ApprovalPolicyConfigSetHandler(ApprovalPolicyConfigGetHandler):
    INTENT_TYPE = APPROVAL_POLICY_INTENTS["config_set"]
    DESCRIPTION = "保存当前业务审批启用配置"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = BUSINESS_CONFIG_GROUPS
    NON_IDEMPOTENT_ALLOWED = "approval policy configuration writes sc.approval.policy"
    SOURCE_KIND = "sc_approval_policy_low_code_write_proxy"

    @classmethod
    def source_authority_contract(cls) -> dict:
        source = super().source_authority_contract()
        source.update({
            "kind": cls.SOURCE_KIND,
            "projection_only": False,
            "write_proxy": True,
        })
        return source

    def _policy_code(self, model: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9_]+", "_", model).strip("_") or "approval"
        return "low_code_%s_company_%s" % (slug, _to_int(getattr(self.env.company, "id", 0)))

    def _create_policy(self, Policy, model: str, vals: dict):
        label = self._model_label(Policy, model)
        create_vals = {
            "name": "%s审批规则" % label,
            "code": self._policy_code(model),
            "target_model": model,
            "company_id": self.env.company.id,
            "active": True,
            "trigger": "submit",
            "runtime_state": "policy_only",
            "sequence": 50,
        }
        create_vals.update(vals)
        return Policy.create(create_vals)

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        self._ensure_access()
        params = self.params if isinstance(self.params, dict) else {}
        model = _to_text(params.get("model") or params.get("target_model") or params.get("targetModel"))
        if not model:
            raise ValidationError("请选择需要配置审批的业务。")
        Policy = self._policy_model()
        policy = self._find_policy(Policy, model)
        mode = _to_text(params.get("mode"))
        approval_required = _bool_param(params.get("approval_required"))
        if not approval_required:
            mode = "none"
        elif mode in {"", "none"}:
            mode = "single"
        if mode not in {"none", "single", "linear"}:
            raise ValidationError("审批方式无效。")
        vals = {
            "approval_required": approval_required,
            "mode": mode,
            "active": True,
        }
        trigger = _to_text(params.get("trigger"))
        if trigger:
            vals["trigger"] = trigger
        if "manager_scope_key" in params or "managerScopeKey" in params:
            scope_key = _to_text(params.get("manager_scope_key") or params.get("managerScopeKey"))
            vals["manager_scope_key"] = scope_key or False
        note = _to_text(params.get("note"))
        if note:
            vals["note"] = note
        if policy:
            policy.write(vals)
        else:
            policy = self._create_policy(Policy, model, vals)
        if hasattr(policy, "sync_tier_definitions"):
            policy.sync_tier_definitions()
        return {"ok": True, "data": self._payload(Policy, model, policy), "meta": {"intent": self.INTENT_TYPE, "source_authority": self.source_authority_contract()}}


class ApprovalPolicyStepsSetHandler(ApprovalPolicyConfigSetHandler):
    INTENT_TYPE = APPROVAL_POLICY_INTENTS["steps_set"]
    DESCRIPTION = "保存当前业务审批步骤编排"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = BUSINESS_CONFIG_GROUPS
    NON_IDEMPOTENT_ALLOWED = "approval step configuration writes sc.approval.step"
    SOURCE_KIND = "sc_approval_step_low_code_write_proxy"

    def _step_model(self):
        if "sc.approval.step" not in self.env:
            raise ValidationError("当前行业模块未安装审批步骤能力。")
        return self.env["sc.approval.step"].sudo()

    def _step_writer(self, step):
        return step.with_context(skip_tier_sync=True) if hasattr(step, "with_context") else step

    def _valid_scope_keys(self, Policy) -> set[str]:
        return {row["value"] for row in self._scope_options(Policy)}

    def _step_vals(self, Policy, raw: dict, sequence: int) -> dict:
        name = _to_text(raw.get("name"))
        scope_key = _to_text(raw.get("approval_scope_key") or raw.get("approvalScopeKey"))
        active = _bool_param(raw.get("active", True))
        if active and not name:
            raise ValidationError("审批步骤名称不能为空。")
        if active and not scope_key:
            raise ValidationError("审批步骤必须选择审批岗位。")
        if scope_key and scope_key not in self._valid_scope_keys(Policy):
            raise ValidationError("审批岗位无效。")
        amount_min = _float_or_false(raw.get("amount_min") if "amount_min" in raw else raw.get("amountMin"))
        amount_max = _float_or_false(raw.get("amount_max") if "amount_max" in raw else raw.get("amountMax"))
        if amount_min and amount_max and amount_min > amount_max:
            raise ValidationError("审批金额下限不能大于上限。")
        return {
            "name": name,
            "approval_scope_key": scope_key or False,
            "active": active,
            "sequence": sequence,
            "amount_min": amount_min,
            "amount_max": amount_max,
            "condition_note": _to_text(raw.get("condition_note") or raw.get("conditionNote")),
            "note": _to_text(raw.get("note")),
        }

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        self._ensure_access()
        params = self.params if isinstance(self.params, dict) else {}
        model = _to_text(params.get("model") or params.get("target_model") or params.get("targetModel"))
        if not model:
            raise ValidationError("请选择需要配置审批的业务。")
        steps = params.get("steps")
        if not isinstance(steps, list):
            raise ValidationError("审批步骤配置无效。")
        Policy = self._policy_model()
        Step = self._step_model()
        policy = self._find_policy(Policy, model)
        if not policy:
            policy = self._create_policy(Policy, model, {
                "approval_required": True,
                "mode": "linear" if len(steps) > 1 else "single",
                "active": True,
            })
        existing = {_ref_id(step): step for step in self._sorted_steps(policy) if _ref_id(step)}
        seen_ids = set()
        active_count = 0
        for index, raw in enumerate(steps):
            if not isinstance(raw, dict):
                raise ValidationError("审批步骤配置无效。")
            step_id = _to_int(raw.get("id"))
            vals = self._step_vals(Policy, raw, (index + 1) * 10)
            if vals["active"]:
                active_count += 1
            if step_id and step_id in existing:
                seen_ids.add(step_id)
                self._step_writer(existing[step_id]).write(vals)
                continue
            create_vals = dict(vals, policy_id=_ref_id(policy))
            Step.create(create_vals)
        for step_id, step in existing.items():
            if step_id not in seen_ids:
                self._step_writer(step).write({"active": False})
        policy_vals = {"approval_required": active_count > 0, "mode": "none" if active_count == 0 else ("single" if active_count == 1 else "linear"), "active": True}
        self._step_writer(policy).write(policy_vals)
        if hasattr(policy, "sync_tier_definitions"):
            policy.sync_tier_definitions()
        return {"ok": True, "data": self._payload(Policy, model, policy), "meta": {"intent": self.INTENT_TYPE, "source_authority": self.source_authority_contract()}}
