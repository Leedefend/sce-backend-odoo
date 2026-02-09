# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Any, Dict, List, Optional

from odoo.exceptions import AccessError, UserError

from ..core.base_handler import BaseIntentHandler


class ChatterTimelineHandler(BaseIntentHandler):
    INTENT_TYPE = "chatter.timeline"
    DESCRIPTION = "Unified collaboration timeline for message/attachment/audit"

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = params.get("model")
        res_id = params.get("res_id") or params.get("record_id")
        limit = _coerce_limit(params.get("limit"), default=40, cap=120)
        include_audit = bool(params.get("include_audit", True))

        if not model or not res_id:
            raise UserError("缺少参数 model/res_id")
        if model not in self.env:
            raise UserError("模型不存在")

        try:
            record = self.env[model].browse(int(res_id)).exists()
        except Exception:
            raise UserError("res_id 无效")
        if not record:
            raise UserError("记录不存在")

        self.env[model].check_access_rights("read")
        record.check_access_rule("read")

        messages = self._load_messages(model, record.id, limit)
        attachments = self._load_attachments(model, record.id, limit)
        audit_items = self._load_audit_items(model, record.id, limit) if include_audit else []

        items = messages + attachments + audit_items
        items.sort(key=lambda item: item.get("at") or "", reverse=True)
        if len(items) > limit:
            items = items[:limit]

        return {
            "items": items,
            "counts": {
                "messages": len(messages),
                "attachments": len(attachments),
                "audit": len(audit_items),
                "total": len(items),
            },
        }, {}

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
            items.append(
                {
                    "key": f"m-{row.id}",
                    "type": "message",
                    "typeLabel": "评论",
                    "title": row.subject or "评论",
                    "meta": f"{row.author_id.display_name or 'Unknown'} · {date_value or '-'}",
                    "body": _strip_html(row.body or ""),
                    "at": date_value,
                    "id": row.id,
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


def _coerce_limit(value: Any, default: int, cap: int) -> int:
    try:
        parsed = int(value)
    except Exception:
        return default
    if parsed <= 0:
        return default
    if parsed > cap:
        return cap
    return parsed


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
