# -*- coding: utf-8 -*-
# 📄 smart_core/handlers/api_data_write.py
# v0.6: Minimal write intent (create/update)

import logging
from typing import Any, Dict, List

from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler
try:
    from ..core.project_context import record_scope_denied_response
except ImportError:  # pragma: no cover - compatibility for lightweight boundary tests
    from ..core.project_context import project_scope_denied_response as record_scope_denied_response
try:
    from ..core.project_context import selected_record_context_id_from_context
except ImportError:  # pragma: no cover - compatibility for lightweight boundary tests
    from ..core.project_context import selected_project_id_from_context as selected_record_context_id_from_context
try:
    from ..core.project_context import apply_business_scope_domain, record_in_business_scope
except ImportError:  # pragma: no cover - compatibility for lightweight boundary tests
    from ..core.project_context import apply_project_scope_domain, record_in_project_scope

    def apply_business_scope_domain(env_model, domain, params=None, context=None):
        return apply_project_scope_domain(env_model, domain, selected_record_context_id_from_context(params, context))

    def record_in_business_scope(env_model, record_id, params=None, context=None):
        return record_in_project_scope(env_model, record_id, selected_record_context_id_from_context(params, context))
from ..core.request_params import parse_bool, parse_positive_int
from ..utils.idempotency import (
    apply_idempotency_identity,
    build_idempotency_conflict_response,
    build_idempotency_fingerprint,
    find_recent_audit_entry,
    normalize_request_id,
    replay_window_seconds,
)
from ..utils.reason_codes import (
    REASON_CONFLICT,
    REASON_INVALID_ID,
    REASON_MISSING_PARAMS,
    REASON_NOT_FOUND,
    REASON_PERMISSION_DENIED,
    REASON_SYSTEM_ERROR,
    REASON_UNSUPPORTED_SOURCE,
    REASON_USER_ERROR,
    failure_meta_for_reason,
)
from ..utils.extension_hooks import call_extension_hook_first
from ..utils.backend_contract_boundaries import is_business_config_runtime_model

_logger = logging.getLogger(__name__)


class ApiDataWriteHandler(BaseIntentHandler):
    """
    Intent: api.data.create / api.data.write
    - 按 allowlist 限定可写 model
    - 字段白名单写入
    - 返回固定写入契约
    """

    INTENT_TYPE = "api.data.create"
    ALIASES = ["api.data.write"]
    DESCRIPTION = "Portal Shell v0.6 minimal write intent (create/update)"
    VERSION = "0.6.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["smart_core.group_smart_core_data_operator"]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = "odoo_orm_write_proxy"
    SOURCE_AUTHORITIES = ("odoo.orm", "ir.model.access", "ir.rule", "ir.model.fields")
    IDEMPOTENCY_WINDOW_SECONDS = 120
    IDEMPOTENCY_EVENT_CODE = "API_DATA_WRITE"

    ALLOWED_MODELS = {
        "res.partner": {"name", "email", "phone"},
    }

    def _allowed_models(self) -> Dict[str, set[str]]:
        payload = call_extension_hook_first(self.env, "smart_core_api_data_write_allowlist", self.env)
        if isinstance(payload, dict):
            out: Dict[str, set[str]] = {}
            for model_name, fields in payload.items():
                model = str(model_name or "").strip()
                if not model:
                    continue
                normalized = {str(item).strip() for item in (fields or []) if str(item).strip()}
                if normalized:
                    out[model] = normalized
            if out:
                self._merge_business_config_custom_fields(out)
                return out
        out = {
            str(model_name): {str(field).strip() for field in (field_names or []) if str(field).strip()}
            for model_name, field_names in self.ALLOWED_MODELS.items()
        }
        self._merge_business_config_custom_fields(out)
        return out

    def _merge_business_config_custom_fields(self, out: Dict[str, set[str]]) -> None:
        if "ui.form.field.policy" not in self.env:
            return
        policies = self.env["ui.form.field.policy"].sudo().search([
            ("active", "=", True),
            ("visible", "=", True),
            ("field_name", "=like", "x_%"),
            *self._business_config_policy_company_domain(),
        ])
        if not policies:
            return
        field_refs = {
            (str(policy.model or "").strip(), str(policy.field_name or "").strip())
            for policy in policies
            if str(policy.model or "").strip() and str(policy.field_name or "").strip()
        }
        if not field_refs:
            return
        domain = []
        for model_name, field_name in sorted(field_refs):
            domain = ["|"] + domain if domain else domain
            domain.append("&")
            domain.append(("model", "=", model_name))
            domain.append(("name", "=", field_name))
        field_rows = self.env["ir.model.fields"].sudo().search(domain)
        for field in field_rows:
            model_name = str(field.model or "").strip()
            field_name = str(field.name or "").strip()
            if (
                not model_name
                or not field_name.startswith("x_")
                or field.state != "manual"
                or getattr(field, "readonly", False)
                or field.ttype in {"binary", "one2many", "many2many"}
            ):
                continue
            out.setdefault(model_name, set()).add(field_name)

    def _business_config_policy_company_domain(self) -> List[Any]:
        company = getattr(self.env, "company", None)
        company_id = int(getattr(company, "id", 0) or 0)
        if not company_id:
            return [("company_id", "=", False)]
        return ["|", ("company_id", "=", False), ("company_id", "=", company_id)]

    def _err(self, code: int, message: str, reason_code: str):
        return {
            "ok": False,
            "error": {
                "code": reason_code,
                "message": message,
                "reason_code": reason_code,
                **failure_meta_for_reason(reason_code),
            },
            "code": code,
        }

    def _source_authority_contract(self, model: str, op: str) -> Dict[str, Any]:
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "model": str(model or ""),
            "op": str(op or ""),
            "proxy_only": True,
            "no_business_fact_authority": True,
            "field_value_passthrough_only": True,
        }

    def _idempotency_window_seconds(self):
        return replay_window_seconds(
            self.IDEMPOTENCY_WINDOW_SECONDS,
            env_key="API_DATA_WRITE_REPLAY_WINDOW_SEC",
        )

    def _idempotency_fingerprint(self, *, intent: str, model: str, record_id: int, vals: Dict[str, Any], dry_run: bool, idem_key: str):
        payload = {
            "intent": str(intent or ""),
            "model": str(model or ""),
            "record_id": int(record_id or 0),
            "vals": dict(vals or {}),
            "dry_run": bool(dry_run),
            "idempotency_key": str(idem_key or ""),
        }
        return build_idempotency_fingerprint(payload)

    def _write_idempotency_audit(self, *, trace_id: str, model: str, res_id: int, action: str, idem_key: str, idem_fingerprint: str, result: Dict[str, Any]):
        Audit = self.env.get("sc.audit.log")
        if not Audit:
            return
        try:
            Audit.write_event(
                event_code=self.IDEMPOTENCY_EVENT_CODE,
                model=model,
                res_id=int(res_id or 0),
                action=action or "write",
                after={
                    "idempotency_key": idem_key,
                    "idempotency_fingerprint": idem_fingerprint,
                    "result": result,
                },
                reason="api.data.write idempotency",
                trace_id=trace_id or "",
                company_id=self.env.user.company_id.id if self.env.user and self.env.user.company_id else None,
            )
        except Exception:
            return

    def _idempotency_conflict_response(self, *, request_id: str, idempotency_key: str, idempotency_fingerprint: str, trace_id: str):
        result = build_idempotency_conflict_response(
            intent_type=self.INTENT_TYPE,
            request_id=request_id,
            idempotency_key=idempotency_key,
            trace_id=trace_id,
            include_replay_evidence=False,
        )
        data = result.setdefault("data", {})
        data["idempotency_fingerprint"] = str(idempotency_fingerprint or "")
        data["replay_supported"] = False
        meta = result.setdefault("meta", {})
        meta["trace_id"] = str(trace_id or "")
        return result

    def _with_idempotency_contract(self, data: Dict[str, Any], *, request_id: str, idempotency_key: str, idempotency_fingerprint: str, trace_id: str, deduplicated: bool):
        contract = apply_idempotency_identity(
            data,
            request_id=request_id,
            idempotency_key=idempotency_key,
            idempotency_fingerprint=idempotency_fingerprint,
            trace_id=trace_id,
        )
        contract["idempotent_replay"] = False
        contract["replay_supported"] = False
        contract["replay_window_expired"] = False
        contract["idempotency_replay_reason_code"] = ""
        contract["idempotency_deduplicated"] = bool(deduplicated)
        return contract

    def _collect_params(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        params = {}
        if isinstance(payload, dict):
            params.update(payload.get("params") or {})
            params.update(payload.get("payload") or {})
        if isinstance(self.params, dict):
            params.update(self.params)
        context = {}
        if isinstance(self.context, dict):
            context.update(self.context)
        if isinstance(payload, dict) and isinstance(payload.get("context"), dict):
            context.update(payload.get("context") or {})
        if isinstance(params.get("context"), dict):
            context.update(params.get("context") or {})
        if context:
            params["context"] = context
        return params

    def _get_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = dict(params.get("context") or {}) if isinstance(params.get("context"), dict) else {}
        company_id, company_error = parse_positive_int(params.get("company_id"), allow_empty=True)
        if not company_error and company_id:
            ctx["allowed_company_ids"] = [company_id]
            ctx["company_id"] = company_id
        project_id, project_error = parse_positive_int(
            params.get("current_project_id") or params.get("project_id"),
            allow_empty=True,
        )
        if not project_error and project_id:
            ctx["current_project_id"] = project_id
            ctx.setdefault("default_project_id", project_id)
        operation_strategy = str(params.get("operation_strategy") or params.get("operationStrategy") or "").strip()
        if operation_strategy:
            ctx["operation_strategy"] = operation_strategy
        return ctx

    def _get_model(self, params: Dict[str, Any]) -> str:
        model = params.get("model") or params.get("res_model") or ""
        return str(model).strip()

    def _get_vals(self, params: Dict[str, Any]) -> Dict[str, Any]:
        vals = params.get("vals") or params.get("values") or {}
        return vals if isinstance(vals, dict) else {}

    def _get_if_match(self, params: Dict[str, Any]) -> str:
        return str(params.get("if_match") or params.get("ifMatch") or params.get("write_date") or "").strip()

    def _get_id(self, params: Dict[str, Any]) -> int:
        record_id, _error = self._read_id(params)
        return record_id

    def _read_id(self, params: Dict[str, Any]):
        for key in ("id", "record_id"):
            if key in params:
                try:
                    value = int(params.get(key))
                except Exception:
                    return 0, self._err(400, "id 无效", REASON_INVALID_ID)
                if value <= 0:
                    return 0, self._err(400, "id 无效", REASON_INVALID_ID)
                return value, None
        ids = params.get("ids")
        if isinstance(ids, list) and ids:
            try:
                value = int(ids[0])
            except Exception:
                return 0, self._err(400, "id 无效", REASON_INVALID_ID)
            if value <= 0:
                return 0, self._err(400, "id 无效", REASON_INVALID_ID)
            return value, None
        return 0, None

    def _current_project_id(self, params: Dict[str, Any]) -> int:
        context = self._get_context(params)
        return selected_record_context_id_from_context(params, context)

    def _scope_denied(self, scope_meta: Dict[str, Any]):
        return record_scope_denied_response(scope_meta)

    def _filter_vals(self, vals: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in vals.items() if k in self.ALLOWED_FIELDS}

    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        params = self._collect_params(payload)
        intent = (payload.get("intent") or self.INTENT_TYPE or "").strip().lower()
        model = self._get_model(params)

        if not model:
            return self._err(400, "缺少参数 model", REASON_MISSING_PARAMS)
        if is_business_config_runtime_model(model):
            return self._err(403, f"运行时配置模型必须通过专用配置入口写入: {model}", REASON_UNSUPPORTED_SOURCE)
        allowed_fields = self._allowed_models().get(model)
        if not allowed_fields:
            return self._err(403, f"模型不允许写入: {model}", REASON_UNSUPPORTED_SOURCE)
        if model not in self.env:
            return self._err(404, f"未知模型: {model}", REASON_NOT_FOUND)

        vals = self._get_vals(params)
        dry_run = parse_bool(params.get("dry_run"), False)
        if not vals:
            return self._err(400, "缺少参数 vals", REASON_MISSING_PARAMS)

        illegal_fields = sorted(set(vals.keys()) - allowed_fields)
        if illegal_fields:
            return self._err(400, f"字段不允许写入: {', '.join(illegal_fields)}", REASON_USER_ERROR)

        safe_vals = {k: v for k, v in vals.items() if k in allowed_fields}
        if not safe_vals:
            return self._err(400, "vals 中无可写字段", REASON_USER_ERROR)

        record_id = 0
        if intent == "api.data.write":
            record_id, record_id_error = self._read_id(params)
            if record_id_error:
                return record_id_error
            if not record_id:
                return self._err(400, "缺少参数 id", REASON_MISSING_PARAMS)

        context = self._get_context(params)
        env_model = self.env[model].with_context(context)
        current_project_id = self._current_project_id(params)

        trace_id = ""
        if isinstance(self.context, dict):
            trace_id = self.context.get("trace_id") or ""
        request_id = normalize_request_id(params.get("request_id"), prefix="adw_req")
        idempotency_key = str(params.get("idempotency_key") or "").strip() or request_id

        if intent == "api.data.write":
            rec = env_model.browse(record_id).exists()
            if not rec:
                return self._err(404, "记录不存在", REASON_NOT_FOUND)
            in_scope, scope_meta = record_in_business_scope(env_model, record_id, params, context)
            if not in_scope:
                return self._scope_denied(scope_meta)
            if current_project_id and "project_id" in safe_vals and "project_id" in env_model._fields:
                target_project_id, target_project_id_error = parse_positive_int(
                    safe_vals.get("project_id"),
                    allow_empty=True,
                )
                if target_project_id_error:
                    return self._err(400, "project_id 无效", REASON_USER_ERROR)
                if target_project_id and target_project_id != int(current_project_id):
                    return self._scope_denied(scope_meta)

            idempotency_fingerprint = self._idempotency_fingerprint(
                intent=intent,
                model=model,
                record_id=record_id,
                vals=safe_vals,
                dry_run=dry_run,
                idem_key=idempotency_key,
            )
            recent_entry = find_recent_audit_entry(
                self.env,
                event_code=self.IDEMPOTENCY_EVENT_CODE,
                idempotency_key=idempotency_key,
                window_seconds=self._idempotency_window_seconds(),
                limit=20,
                extra_domain=[("model", "=", model)],
            )
            if recent_entry:
                payload_after = recent_entry.get("payload") or {}
                recent_fingerprint = str(payload_after.get("idempotency_fingerprint") or "")
                if recent_fingerprint and recent_fingerprint != idempotency_fingerprint:
                    return self._idempotency_conflict_response(
                        request_id=request_id,
                        idempotency_key=idempotency_key,
                        idempotency_fingerprint=idempotency_fingerprint,
                        trace_id=trace_id,
                    )
                if recent_fingerprint and recent_fingerprint == idempotency_fingerprint:
                    replay_result = payload_after.get("result")
                    base_data = replay_result if isinstance(replay_result, dict) else {
                        "id": rec.id,
                        "model": model,
                        "written_fields": sorted(safe_vals.keys()),
                        "values": safe_vals,
                        "dry_run": dry_run,
                        "project_scope": scope_meta,
                        "record_scope": scope_meta,
                    }
                    if isinstance(base_data, dict):
                        base_data.setdefault("project_scope", scope_meta)
                        base_data.setdefault("record_scope", scope_meta)
                    data = self._with_idempotency_contract(
                        base_data,
                        request_id=request_id,
                        idempotency_key=idempotency_key,
                        idempotency_fingerprint=idempotency_fingerprint,
                        trace_id=trace_id,
                        deduplicated=True,
                    )
                    meta = {
                        "trace_id": trace_id,
                        "write_mode": "update",
                        "source": "portal-shell",
                        "source_authority": self._source_authority_contract(model, "write"),
                        "project_scope": scope_meta,
                        "record_scope": scope_meta,
                    }
                    return {"ok": True, "data": data, "meta": meta}

            try:
                if_match = self._get_if_match(params)
                if if_match:
                    current = rec.write_date and rec.write_date.strftime("%Y-%m-%d %H:%M:%S") or ""
                    if current and current != if_match:
                        return self._err(409, "Record changed", REASON_CONFLICT)
                env_model.check_access_rights("write")
                rec.check_access_rule("write")
                if not dry_run:
                    rec.write(safe_vals)
            except AccessError as ae:
                _logger.warning("api.data.write AccessError on %s: %s", model, ae)
                return self._err(403, "无写入权限", REASON_PERMISSION_DENIED)
            except Exception as e:
                _logger.exception("api.data.write failed on %s", model)
                return self._err(500, str(e), REASON_SYSTEM_ERROR)

            data = {
                "id": rec.id,
                "model": model,
                "written_fields": sorted(safe_vals.keys()),
                "values": safe_vals,
                "dry_run": dry_run,
                "project_scope": scope_meta,
                "record_scope": scope_meta,
            }
            data = self._with_idempotency_contract(
                data,
                request_id=request_id,
                idempotency_key=idempotency_key,
                idempotency_fingerprint=idempotency_fingerprint,
                trace_id=trace_id,
                deduplicated=False,
            )
            self._write_idempotency_audit(
                trace_id=trace_id,
                model=model,
                res_id=rec.id,
                action="write",
                idem_key=idempotency_key,
                idem_fingerprint=idempotency_fingerprint,
                result=data,
            )
            meta = {
                "trace_id": trace_id,
                "write_mode": "update",
                "source": "portal-shell",
                "source_authority": self._source_authority_contract(model, "write"),
                "project_scope": scope_meta,
                "record_scope": scope_meta,
            }
            return {"ok": True, "data": data, "meta": meta}

        if intent == "api.data.create":
            _scoped_domain, scope_meta = apply_business_scope_domain(env_model, [], params, context)
            if scope_meta.get("project_operation_strategy_mismatch"):
                return self._scope_denied(scope_meta)
            scope_company_id = int(scope_meta.get("company_id") or 0)
            if scope_company_id and "company_id" in env_model._fields:
                target_company_id, target_company_id_error = parse_positive_int(
                    safe_vals.get("company_id"),
                    allow_empty=True,
                )
                if target_company_id_error:
                    return self._err(400, "company_id 无效", REASON_USER_ERROR)
                if target_company_id and target_company_id != scope_company_id:
                    return self._scope_denied(scope_meta)
                if not target_company_id and "company_id" in allowed_fields:
                    safe_vals["company_id"] = scope_company_id
            scope_operation_strategy = str(scope_meta.get("operation_strategy") or "").strip()
            operation_field = env_model._fields.get("operation_strategy")
            if (
                scope_operation_strategy
                and operation_field
                and not getattr(operation_field, "related", None)
                and "operation_strategy" in allowed_fields
            ):
                incoming_operation_strategy = str(safe_vals.get("operation_strategy") or "").strip()
                if not incoming_operation_strategy:
                    safe_vals["operation_strategy"] = scope_operation_strategy
                elif incoming_operation_strategy != scope_operation_strategy:
                    return self._scope_denied(scope_meta)
            if current_project_id and scope_meta.get("applied") and "project_id" in env_model._fields:
                target_project_id, target_project_id_error = parse_positive_int(
                    safe_vals.get("project_id"),
                    allow_empty=True,
                )
                if target_project_id_error:
                    return self._err(400, "project_id 无效", REASON_USER_ERROR)
                if target_project_id and target_project_id != int(current_project_id):
                    return self._scope_denied(scope_meta)
                if not target_project_id and "project_id" in allowed_fields:
                    safe_vals["project_id"] = int(current_project_id)
            idempotency_fingerprint = self._idempotency_fingerprint(
                intent=intent,
                model=model,
                record_id=0,
                vals=safe_vals,
                dry_run=dry_run,
                idem_key=idempotency_key,
            )
            recent_entry = find_recent_audit_entry(
                self.env,
                event_code=self.IDEMPOTENCY_EVENT_CODE,
                idempotency_key=idempotency_key,
                window_seconds=self._idempotency_window_seconds(),
                limit=20,
                extra_domain=[("model", "=", model)],
            )
            if recent_entry:
                payload_after = recent_entry.get("payload") or {}
                recent_fingerprint = str(payload_after.get("idempotency_fingerprint") or "")
                if recent_fingerprint and recent_fingerprint != idempotency_fingerprint:
                    return self._idempotency_conflict_response(
                        request_id=request_id,
                        idempotency_key=idempotency_key,
                        idempotency_fingerprint=idempotency_fingerprint,
                        trace_id=trace_id,
                    )
                if recent_fingerprint and recent_fingerprint == idempotency_fingerprint:
                    replay_result = payload_after.get("result")
                    base_data = replay_result if isinstance(replay_result, dict) else {
                        "id": 0,
                        "model": model,
                        "written_fields": sorted(safe_vals.keys()),
                        "values": safe_vals,
                        "dry_run": dry_run,
                        "project_scope": scope_meta,
                        "record_scope": scope_meta,
                    }
                    if isinstance(base_data, dict):
                        base_data.setdefault("project_scope", scope_meta)
                        base_data.setdefault("record_scope", scope_meta)
                    data = self._with_idempotency_contract(
                        base_data,
                        request_id=request_id,
                        idempotency_key=idempotency_key,
                        idempotency_fingerprint=idempotency_fingerprint,
                        trace_id=trace_id,
                        deduplicated=True,
                    )
                    meta = {
                        "trace_id": trace_id,
                        "write_mode": "create",
                        "source": "portal-shell",
                        "source_authority": self._source_authority_contract(model, "create"),
                        "project_scope": scope_meta,
                        "record_scope": scope_meta,
                    }
                    return {"ok": True, "data": data, "meta": meta}

            try:
                env_model.check_access_rights("create")
                rec = env_model.create(safe_vals) if not dry_run else None
            except AccessError as ae:
                _logger.warning("api.data.create AccessError on %s: %s", model, ae)
                return self._err(403, "无创建权限", REASON_PERMISSION_DENIED)
            except Exception as e:
                _logger.exception("api.data.create failed on %s", model)
                return self._err(500, str(e), REASON_SYSTEM_ERROR)

            data = {
                "id": rec.id if rec else 0,
                "model": model,
                "written_fields": sorted(safe_vals.keys()),
                "values": safe_vals,
                "dry_run": dry_run,
                "project_scope": scope_meta,
                "record_scope": scope_meta,
            }
            data = self._with_idempotency_contract(
                data,
                request_id=request_id,
                idempotency_key=idempotency_key,
                idempotency_fingerprint=idempotency_fingerprint,
                trace_id=trace_id,
                deduplicated=False,
            )
            self._write_idempotency_audit(
                trace_id=trace_id,
                model=model,
                res_id=rec.id if rec else 0,
                action="create",
                idem_key=idempotency_key,
                idem_fingerprint=idempotency_fingerprint,
                result=data,
            )
            meta = {
                "trace_id": trace_id,
                "write_mode": "create",
                "source": "portal-shell",
                "source_authority": self._source_authority_contract(model, "create"),
                "project_scope": scope_meta,
                "record_scope": scope_meta,
            }
            return {"ok": True, "data": data, "meta": meta}

        return self._err(400, f"未知写入意图: {intent}", REASON_UNSUPPORTED_SOURCE)
