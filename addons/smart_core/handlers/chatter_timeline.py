# -*- coding: utf-8 -*-
from datetime import datetime
from email.header import decode_header, make_header
from email.utils import parseaddr
from typing import Any, Dict, List, Optional

from odoo.exceptions import AccessError, UserError

from ..core.base_handler import BaseIntentHandler
try:
    from ..core.project_context import record_scope_denied_response
except ImportError:  # pragma: no cover - compatibility for lightweight boundary tests
    from ..core.project_context import project_scope_denied_response as record_scope_denied_response
try:
    from ..core.project_context import record_in_business_scope
except ImportError:  # pragma: no cover - compatibility for lightweight boundary tests
    from ..core.project_context import record_in_project_scope
    try:
        from ..core.project_context import selected_record_context_id_from_context
    except ImportError:  # pragma: no cover - compatibility for older lightweight boundary tests
        from ..core.project_context import selected_project_id_from_context as selected_record_context_id_from_context

    def record_in_business_scope(env_model, record_id, params=None, context=None):
        return record_in_project_scope(env_model, record_id, selected_record_context_id_from_context(params, context))
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
        in_scope, scope_meta = record_in_business_scope(
            self.env[model],
            int(record.id),
            params,
            self.context if isinstance(self.context, dict) else {},
        )
        if not in_scope:
            return record_scope_denied_response(scope_meta)

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
                    "meta": f"{_message_author_display(row)} · {date_value or '-'}",
                    "body": _strip_html(row.body or ""),
                    "at": date_value,
                    "id": row.id,
                    "subtype": subtype_xmlid,
                }
            )
        return items

    def _load_attachments(self, model: str, res_id: int, limit: int) -> List[Dict[str, Any]]:
        Attachment = self.env["ir.attachment"]
        domain = [("res_model", "=", model), ("res_id", "=", res_id)]
        related_ids: List[int] = []
        if model in self.env:
            record = self.env[model].browse(res_id).exists()
            record_fields = getattr(record, "_fields", {}) if record else {}
            attachment_field = record and next(
                (
                    name
                    for name, field in record_fields.items()
                    if name == "attachment_ids"
                    or (field.type == "many2many" and field.comodel_name == "ir.attachment")
                ),
                "",
            )
            if attachment_field:
                related_ids = record[attachment_field].ids
        if related_ids:
            domain = ["|", ("id", "in", related_ids), "&", ("res_model", "=", model), ("res_id", "=", res_id)]
        AttachmentModel = Attachment.sudo() if hasattr(Attachment, "sudo") else Attachment
        rows = AttachmentModel.search(domain, order="id desc", limit=limit)
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
            assignee = row.user_id.display_name or "Unknown"
            is_assignee = bool(row.user_id and row.user_id.id == self.env.user.id)
            items.append(
                {
                    "key": f"act-{row.id}",
                    "type": "activity",
                    "typeLabel": "计划",
                    "title": row.summary or row.activity_type_id.display_name or "计划",
                    "meta": f"{assignee} · {deadline or '-'}",
                    "body": _strip_html(row.note or ""),
                    "at": deadline,
                    "id": row.id,
                    "activity": {
                        "id": row.id,
                        "assignee_user_id": row.user_id.id or 0,
                        "assignee_name": assignee,
                        "deadline": deadline,
                        "activity_type": row.activity_type_id.display_name or "",
                        "can_complete": is_assignee,
                        "can_cancel": True,
                    },
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


def _message_author_display(row: Any) -> str:
    author = getattr(row, "author_id", None)
    author_name = str(getattr(author, "display_name", "") or "").strip()
    if author_name:
        return author_name
    email_from = str(getattr(row, "email_from", "") or "").strip()
    if email_from:
        display_name, email = parseaddr(email_from)
        decoded_name = _decode_header_value(display_name)
        if decoded_name:
            return decoded_name
        if email:
            return email
        return _decode_header_value(email_from) or email_from
    create_user = getattr(row, "create_uid", None)
    create_user_name = str(getattr(create_user, "display_name", "") or "").strip()
    return create_user_name or "系统"


def _decode_header_value(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        return str(make_header(decode_header(raw))).strip()
    except Exception:
        return raw


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
