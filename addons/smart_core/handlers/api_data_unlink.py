# -*- coding: utf-8 -*-
# 📄 smart_core/handlers/api_data_unlink.py
# Minimal unlink intent for portal relational MVP

import logging
from typing import Any, Dict, List

from odoo.exceptions import AccessError, UserError, ValidationError

from ..core.base_handler import BaseIntentHandler
try:
    from ..core.project_context import record_scope_denied_response
except ImportError:  # pragma: no cover - compatibility for lightweight boundary tests
    from ..core.project_context import project_scope_denied_response as record_scope_denied_response
try:
    from ..core.project_context import apply_business_scope_domain
except ImportError:  # pragma: no cover - compatibility for lightweight boundary tests
    from ..core.project_context import apply_project_scope_domain
    try:
        from ..core.project_context import selected_record_context_id_from_context
    except ImportError:  # pragma: no cover - compatibility for older lightweight boundary tests
        from ..core.project_context import selected_project_id_from_context as selected_record_context_id_from_context

    def apply_business_scope_domain(env_model, domain, params=None, context=None):
        return apply_project_scope_domain(env_model, domain, selected_record_context_id_from_context(params, context))
from ..core.request_params import parse_bool
from ..utils.idempotency import (
    apply_idempotency_identity,
    build_idempotency_conflict_response,
    build_idempotency_fingerprint,
    find_recent_audit_entry,
    normalize_request_id,
    replay_window_seconds,
)
from ..utils.reason_codes import (
    REASON_BUSINESS_RULE_FAILED,
    REASON_DELETE_POLICY_DENIED,
    REASON_INVALID_ID,
    REASON_MISSING_PARAMS,
    REASON_NOT_FOUND,
    REASON_PERMISSION_DENIED,
    REASON_SYSTEM_ERROR,
    failure_meta_for_reason,
)
from ..utils.delete_policy import resolve_unlink_policy

_logger = logging.getLogger(__name__)


class ApiDataUnlinkHandler(BaseIntentHandler):
    """
    Intent: api.data.unlink
    - 按 delete_policy 契约限定可删除 model
    - 返回删除 ids
    """

    INTENT_TYPE = "api.data.unlink"
    DESCRIPTION = "Portal Shell minimal unlink intent"
    VERSION = "0.1.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["smart_core.group_smart_core_data_operator"]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = "odoo_orm_unlink_proxy"
    SOURCE_AUTHORITIES = ("odoo.orm", "ir.model.access", "ir.rule", "ir.model.fields")
    IDEMPOTENCY_WINDOW_SECONDS = 120
    IDEMPOTENCY_EVENT_CODE = "API_DATA_UNLINK"

    ALLOWED_MODELS = {"res.partner"}

    def _delete_policy(self, model: str) -> Dict[str, Any]:
        return resolve_unlink_policy(self.env, model, default_allowed_models=self.ALLOWED_MODELS)

    def _check_record_delete_policy(self, recs, delete_policy: Dict[str, Any]):
        state_field = str(delete_policy.get("state_field") or "").strip()
        allowed_states = {
            str(item or "").strip()
            for item in (delete_policy.get("allowed_states") or [])
            if str(item or "").strip()
        }
        if not state_field and not allowed_states:
            return None
        if not state_field or not allowed_states:
            return self._err(403, "删除策略缺少状态字段或允许状态配置", REASON_DELETE_POLICY_DENIED)
        if state_field not in getattr(recs, "_fields", {}):
            return self._err(403, f"当前模型缺少删除策略要求的状态字段: {state_field}", REASON_DELETE_POLICY_DENIED)
        invalid_ids = []
        for rec in recs:
            value = str(getattr(rec, state_field, "") or "").strip()
            if value not in allowed_states:
                invalid_ids.append(rec.id)
        if invalid_ids:
            allowed_text = "、".join(sorted(allowed_states))
            return self._err(
                400,
                f"仅允许删除 {state_field} 为 {allowed_text} 的草稿/取消态数据",
                REASON_BUSINESS_RULE_FAILED,
            )
        return None

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

    def _source_authority_contract(self, model: str) -> Dict[str, Any]:
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "model": str(model or ""),
            "op": "unlink",
            "proxy_only": True,
        }

    def _idempotency_window_seconds(self):
        return replay_window_seconds(
            self.IDEMPOTENCY_WINDOW_SECONDS,
            env_key="API_DATA_UNLINK_REPLAY_WINDOW_SEC",
        )

    def _idempotency_fingerprint(self, *, model: str, ids: List[int], dry_run: bool, idem_key: str):
        payload = {
            "intent": self.INTENT_TYPE,
            "model": str(model or ""),
            "ids": list(ids or []),
            "dry_run": bool(dry_run),
            "idempotency_key": str(idem_key or ""),
        }
        return build_idempotency_fingerprint(payload, normalize_id_keys=["ids"])

    def _write_idempotency_audit(self, *, trace_id: str, model: str, ids: List[int], idem_key: str, idem_fingerprint: str, result: Dict[str, Any]):
        Audit = self.env.get("sc.audit.log")
        if not Audit:
            return
        try:
            Audit.write_event(
                event_code=self.IDEMPOTENCY_EVENT_CODE,
                model=model,
                res_id=0,
                action="unlink",
                after={
                    "idempotency_key": idem_key,
                    "idempotency_fingerprint": idem_fingerprint,
                    "result": result,
                    "ids": list(ids or []),
                },
                reason="api.data.unlink idempotency",
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
            if isinstance(payload.get("context"), dict):
                params.setdefault("context", {}).update(payload.get("context") or {})
            params.update(payload.get("params") or {})
            params.update(payload.get("payload") or {})
        if isinstance(self.params, dict):
            params.update(self.params)
        return params

    def _get_model(self, params: Dict[str, Any]) -> str:
        model = params.get("model") or params.get("res_model") or ""
        return str(model).strip()

    def _get_ids(self, params: Dict[str, Any]) -> List[int]:
        ids, _error = self._read_ids(params)
        return ids

    def _read_ids(self, params: Dict[str, Any]):
        ids = params.get("ids") or params.get("record_ids") or []
        if isinstance(ids, list):
            values = []
            for raw in ids:
                try:
                    value = int(raw)
                except Exception:
                    return [], self._err(400, "ids 无效", REASON_INVALID_ID)
                if value <= 0:
                    return [], self._err(400, "ids 无效", REASON_INVALID_ID)
                values.append(value)
            return values, None
        try:
            value = int(ids)
        except Exception:
            return [], self._err(400, "ids 无效", REASON_INVALID_ID)
        if value <= 0:
            return [], self._err(400, "ids 无效", REASON_INVALID_ID)
        return [value], None

    def _request_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = dict(params.get("context") or {}) if isinstance(params.get("context"), dict) else {}
        company_id = 0
        try:
            company_id = int(params.get("company_id") or 0)
        except Exception:
            company_id = 0
        if company_id > 0:
            ctx["allowed_company_ids"] = [company_id]
            ctx["company_id"] = company_id
        project_id = 0
        try:
            project_id = int(params.get("current_project_id") or params.get("project_id") or 0)
        except Exception:
            project_id = 0
        if project_id > 0:
            ctx["current_project_id"] = project_id
            ctx.setdefault("default_project_id", project_id)
        operation_strategy = str(params.get("operation_strategy") or params.get("operationStrategy") or "").strip()
        if operation_strategy:
            ctx["operation_strategy"] = operation_strategy
        return ctx

    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        params = self._collect_params(payload)
        model = self._get_model(params)
        if not model:
            return self._err(400, "缺少参数 model", REASON_MISSING_PARAMS)
        delete_policy = self._delete_policy(model)
        if not bool(delete_policy.get("allowed")) or str(delete_policy.get("delete_mode") or "none") != "unlink":
            return self._err(
                403,
                str(delete_policy.get("message") or f"当前模型未开放删除: {model}"),
                str(delete_policy.get("reason_code") or REASON_DELETE_POLICY_DENIED),
            )
        if model not in self.env:
            return self._err(404, f"未知模型: {model}", REASON_NOT_FOUND)

        ids, ids_error = self._read_ids(params)
        if ids_error:
            return ids_error
        dry_run = parse_bool(params.get("dry_run"), False)
        if not ids:
            return self._err(400, "缺少参数 ids", REASON_MISSING_PARAMS)

        env_model = self.env[model]
        context = self._request_context(params)
        scoped_domain, project_scope_meta = apply_business_scope_domain(env_model, [("id", "in", ids)], params, context)
        if project_scope_meta.get("applied"):
            allowed_count = env_model.search_count(scoped_domain)
            if int(allowed_count or 0) != len(set(ids)):
                return record_scope_denied_response(project_scope_meta, message="当前记录上下文不允许删除其他记录的数据")
        trace_id = ""
        if isinstance(self.context, dict):
            trace_id = self.context.get("trace_id") or ""
        request_id = normalize_request_id(params.get("request_id"), prefix="adu_req")
        idempotency_key = str(params.get("idempotency_key") or "").strip() or request_id
        idempotency_fingerprint = self._idempotency_fingerprint(
            model=model,
            ids=ids,
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
                    "ids": ids,
                    "model": model,
                    "dry_run": dry_run,
                    "project_scope": project_scope_meta,
                    "record_scope": project_scope_meta,
                }
                if isinstance(base_data, dict):
                    base_data.setdefault("project_scope", project_scope_meta)
                    base_data.setdefault("record_scope", project_scope_meta)
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
                    "write_mode": "unlink",
                    "source": "portal-shell",
                    "source_authority": self._source_authority_contract(model),
                    "project_scope": project_scope_meta,
                    "record_scope": project_scope_meta,
                }
                return {"ok": True, "data": data, "meta": meta}

        recs = env_model.browse(ids).exists()
        found_ids = set(recs.ids)
        missing_ids = [rec_id for rec_id in ids if rec_id not in found_ids]
        if missing_ids:
            return self._err(404, "记录不存在", REASON_NOT_FOUND)

        policy_error = self._check_record_delete_policy(recs, delete_policy)
        if policy_error:
            return policy_error

        try:
            env_model.check_access_rights("unlink")
            recs.check_access_rule("unlink")
            if not dry_run:
                recs.unlink()
        except (UserError, ValidationError) as exc:
            _logger.warning("api.data.unlink business rule blocked on %s: %s", model, exc)
            return self._err(400, str(exc) or "业务规则不允许删除", REASON_BUSINESS_RULE_FAILED)
        except AccessError as ae:
            _logger.warning("api.data.unlink AccessError on %s: %s", model, ae)
            return self._err(403, "无删除权限", REASON_PERMISSION_DENIED)
        except Exception as e:
            _logger.exception("api.data.unlink failed on %s", model)
            return self._err(500, str(e), REASON_SYSTEM_ERROR)

        data = {
            "ids": ids,
            "deleted_count": 0 if dry_run else len(set(ids)),
            "model": model,
            "dry_run": dry_run,
            "delete_policy": delete_policy,
            "project_scope": project_scope_meta,
            "record_scope": project_scope_meta,
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
            ids=ids,
            idem_key=idempotency_key,
            idem_fingerprint=idempotency_fingerprint,
            result=data,
        )
        meta = {
            "trace_id": trace_id,
            "write_mode": "unlink",
            "source": "portal-shell",
            "source_authority": self._source_authority_contract(model),
            "project_scope": project_scope_meta,
            "record_scope": project_scope_meta,
        }
        return {"ok": True, "data": data, "meta": meta}
