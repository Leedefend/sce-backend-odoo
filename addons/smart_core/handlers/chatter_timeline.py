# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Any, Dict, List, Optional

from odoo.exceptions import AccessError, UserError

from ..core.base_handler import BaseIntentHandler
from ..core.project_context import (
    project_scope_denied_response,
    record_in_project_scope,
    selected_project_id_from_context,
)
from ..core.request_params import parse_bool, parse_positive_int
from ..utils.reason_codes import (
    REASON_MISSING_PARAMS,
    REASON_NOT_FOUND,
    REASON_PERMISSION_DENIED,
    REASON_SYSTEM_ERROR,
    REASON_USER_ERROR,
    failure_meta_for_reason,
)


class ChatterTimelineHandler(BaseIntentHandler):
    INTENT_TYPE = "chatter.timeline"
    DESCRIPTION = "Unified collaboration timeline for message/attachment/audit"
    SOURCE_KIND = "odoo_collaboration_timeline_projection"
    SOURCE_AUTHORITIES = ("mail.message", "ir.attachment", "mail.activity")
    AUXILIARY_AUTHORITIES = ("sc.audit.log",)
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "auxiliary_authorities": list(cls.AUXILIARY_AUTHORITIES),
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = params.get("model")
        res_id = params.get("res_id") if "res_id" in params else params.get("record_id")
        include_audit = parse_bool(params.get("include_audit"), True)
        trace_id = self.context.get("trace_id") if isinstance(self.context, dict) else ""

        if not model or _is_empty_param(res_id):
            return self._failure(REASON_MISSING_PARAMS, "缺少参数 model/res_id", 400, trace_id)
        limit, limit_error = _read_limit(params.get("limit"), default=40, cap=120)
        if limit_error:
            return self._failure(REASON_USER_ERROR, "limit 无效", 400, trace_id)
        if model not in self.env:
            return self._failure(REASON_NOT_FOUND, "模型不存在", 404, trace_id)

        res_id, res_id_error = parse_positive_int(res_id)
        if res_id_error:
            return self._failure(REASON_USER_ERROR, "res_id 无效", 400, trace_id)

        try:
            record = self.env[model].browse(res_id).exists()
        except AccessError:
            return self._failure(REASON_PERMISSION_DENIED, "无权限读取协作时间线", 403, trace_id)
        except UserError as exc:
            return self._failure(REASON_USER_ERROR, str(exc) or "业务规则不允许", 400, trace_id)
        except Exception:
            return self._failure(REASON_SYSTEM_ERROR, "读取协作时间线失败", 500, trace_id)
        if not record:
            return self._failure(REASON_NOT_FOUND, "记录不存在", 404, trace_id)
        current_project_id = selected_project_id_from_context(params, self.context if isinstance(self.context, dict) else {})
        in_scope, scope_meta = record_in_project_scope(self.env[model], int(record.id), current_project_id)
        if not in_scope:
            return project_scope_denied_response(scope_meta)

        try:
            self.env[model].check_access_rights("read")
            record.check_access_rule("read")

            messages = self._load_messages(model, record.id, limit)
            attachments = self._load_attachments(model, record.id, limit)
            activity_items = self._load_activities(model, record.id, limit)
            audit_items = self._load_audit_items(model, record.id, limit) if include_audit else []
        except AccessError:
            return self._failure(REASON_PERMISSION_DENIED, "无权限读取协作时间线", 403, trace_id)
        except UserError as exc:
            return self._failure(REASON_USER_ERROR, str(exc) or "业务规则不允许", 400, trace_id)
        except Exception:
            return self._failure(REASON_SYSTEM_ERROR, "读取协作时间线失败", 500, trace_id)

        items = messages + attachments + activity_items + audit_items
        items.sort(key=lambda item: item.get("at") or "", reverse=True)
        if len(items) > limit:
            items = items[:limit]

        return {
            "items": items,
            "counts": {
                "messages": len(messages),
                "attachments": len(attachments),
                "activities": len(activity_items),
                "audit": len(audit_items),
                "total": len(items),
            },
            "source_authorities": list(self.SOURCE_AUTHORITIES),
            "auxiliary_authorities": list(self.AUXILIARY_AUTHORITIES) if include_audit else [],
            "source_authority": self.source_authority_contract(),
        }, {
            "source_authorities": list(self.SOURCE_AUTHORITIES),
            "auxiliary_authorities": list(self.AUXILIARY_AUTHORITIES) if include_audit else [],
            "source_authority": self.source_authority_contract(),
        }

    def _failure(self, reason_code: str, message: str, status_code: int, trace_id: str):
        return {
            "ok": False,
            "error": {
                "code": reason_code,
                "message": message,
                "reason_code": reason_code,
                **failure_meta_for_reason(reason_code),
            },
            "data": {"result": {"success": False, "reason_code": reason_code, "message": message}},
            "code": status_code,
            "meta": {"trace_id": trace_id, "source_authority": self.source_authority_contract()},
        }

    def _load_messages(self, model: str, res_id: int, limit: int) -> List[Dict[str, Any]]:
        Message = self.env["mail.message"]
        rows = Message.search(
            [("model", "=", model), ("res_id", "=", res_id)],
            order="date desc, id desc",
            limit=limit,
        )
        items: List[Dict[str, Any]] = []
        for row in rows:
            date_value = _to_iso(row.date)
            subtype_xmlid = _message_subtype_xmlid(row)
            type_label = "备注" if subtype_xmlid == "mail.mt_note" else "评论"
            items.append(
                {
                    "key": f"m-{row.id}",
                    "type": "message",
                    "typeLabel": type_label,
                    "title": row.subject or type_label,
                    "meta": f"{row.author_id.display_name or 'Unknown'} · {date_value or '-'}",
                    "body": _strip_html(row.body or ""),
                    "at": date_value,
                    "id": row.id,
                    "subtype": subtype_xmlid,
                }
            )
        return items

    def _load_attachments(self, model: str, res_id: int, limit: int) -> List[Dict[str, Any]]:
        Attachment = self.env["ir.attachment"]
        rows = Attachment.search(
            [("res_model", "=", model), ("res_id", "=", res_id)],
            order="id desc",
            limit=limit,
        )
        items: List[Dict[str, Any]] = []
        for row in rows:
            date_value = _to_iso(row.create_date) or _to_iso(row.write_date)
            items.append(
                {
                    "key": f"a-{row.id}",
                    "type": "attachment",
                    "typeLabel": "附件",
                    "title": row.name or "Attachment",
                    "meta": f"{row.mimetype or 'unknown'} · {row.file_size or '-'}",
                    "body": "",
                    "at": date_value,
                    "id": row.id,
                    "attachment": {
                        "id": row.id,
                        "name": row.name or "",
                        "mimetype": row.mimetype or "",
                    },
                }
            )
        return items

    def _load_activities(self, model: str, res_id: int, limit: int) -> List[Dict[str, Any]]:
        Activity = self.env.get("mail.activity")
        IrModel = self.env.get("ir.model")
        if Activity is None or IrModel is None:
            return []
        model_rec = IrModel.sudo().search([("model", "=", model)], limit=1)
        if not model_rec:
            return []
        rows = Activity.search(
            [("res_model_id", "=", model_rec.id), ("res_id", "=", res_id)],
            order="date_deadline desc, id desc",
            limit=limit,
        )
        items: List[Dict[str, Any]] = []
        for row in rows:
            deadline = _to_iso(row.date_deadline)
            items.append(
                {
                    "key": f"act-{row.id}",
                    "type": "activity",
                    "typeLabel": "活动",
                    "title": row.summary or row.activity_type_id.display_name or "活动",
                    "meta": f"{row.user_id.display_name or 'Unknown'} · {deadline or '-'}",
                    "body": _strip_html(row.note or ""),
                    "at": deadline,
                    "id": row.id,
                }
            )
        return items

    def _load_audit_items(self, model: str, res_id: int, limit: int) -> List[Dict[str, Any]]:
        Audit = self.env.get("sc.audit.log")
        if not Audit:
            return []
        rows = Audit.sudo().search(
            [("model", "=", model), ("res_id", "=", res_id)],
            order="ts desc, id desc",
            limit=limit,
        )
        items: List[Dict[str, Any]] = []
        for row in rows:
            date_value = _to_iso(row.ts)
            actor = row.actor_login or (row.actor_uid.display_name if row.actor_uid else "System")
            items.append(
                {
                    "key": f"l-{row.id}",
                    "type": "audit",
                    "typeLabel": "操作",
                    "title": row.action or row.event_code or "操作日志",
                    "meta": f"{actor} · {date_value or '-'}",
                    "body": row.reason or "",
                    "at": date_value,
                    "id": row.id,
                    "reason_code": row.event_code or "",
                }
            )
        return items


def _read_limit(value: Any, default: int, cap: int):
    parsed, error = parse_positive_int(value, allow_empty=True)
    if error:
        return 0, error
    if parsed is None:
        return default, None
    return min(parsed, cap), None


def _is_empty_param(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _to_iso(value: Any) -> Optional[str]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    try:
        return datetime.fromisoformat(str(value).replace(" ", "T")).isoformat()
    except Exception:
        return str(value)


def _strip_html(value: str) -> str:
    text = str(value or "")
    out: List[str] = []
    in_tag = False
    for ch in text:
        if ch == "<":
            in_tag = True
            continue
        if ch == ">":
            in_tag = False
            continue
        if not in_tag:
            out.append(ch)
    return "".join(out).strip()


def _message_subtype_xmlid(row: Any) -> str:
    subtype = getattr(row, "subtype_id", None)
    if not subtype:
        return ""
    try:
        xmlids = subtype._get_external_ids().get(subtype.id) or []
    except Exception:
        xmlids = []
    if xmlids:
        return str(xmlids[0] or "")
    return str(subtype.name or "")
