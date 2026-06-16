# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from email.header import decode_header, make_header
from email.utils import formataddr, parseaddr
from html import escape
from typing import Any, Iterable, List

from odoo import fields
from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler
from ..core.request_params import parse_positive_int
from .collaboration_users import is_collaboration_visible_user

GLOBAL_MESSAGE_SUBJECT = "[SC_GLOBAL_MESSAGE]"


class _GlobalMessageBaseHandler(BaseIntentHandler):
    SOURCE_AUTHORITY = "mail.message"
    SOURCE_KIND = "odoo_global_station_message_contract"
    SOURCE_AUTHORITIES = ("mail.message", "mail.notification", "res.partner", "res.users", "res.groups", "ir.rule")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authority": cls.SOURCE_AUTHORITY,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": not bool(str(getattr(cls, "NON_IDEMPOTENT_ALLOWED", "") or "").strip()),
            "write_proxy": bool(str(getattr(cls, "NON_IDEMPOTENT_ALLOWED", "") or "").strip()),
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
            "scope": "global_station_message",
        }

    def _err(self, code: int, message: str):
        return {
            "ok": False,
            "error": {"code": code, "message": message},
            "code": code,
            "meta": {"source_authority": self.source_authority_contract()},
        }

    def _allowed_users(self, user_ids: Iterable[int]):
        ids = [int(uid) for uid in user_ids if int(uid or 0) > 0]
        if not ids:
            return self.env["res.users"]
        users = self.env["res.users"].browse(ids).exists().filtered(lambda user: bool(user.active))
        internal_group = self.env.ref("base.group_user", raise_if_not_found=False)
        if internal_group:
            users = users.filtered(lambda user: internal_group in user.groups_id)
        users = users.filtered(is_collaboration_visible_user)
        return users

    def _serialize_message(self, message) -> dict[str, Any]:
        partners = _message_partners(message)
        partner_ids = _conversation_partner_ids(message)
        return {
            "id": int(message.id),
            "body": _plain_text(message.body),
            "author_id": int(message.author_id.id or 0) if message.author_id else 0,
            "author_name": _author_display(message),
            "recipient_partner_ids": [int(pid) for pid in partners.ids if pid],
            "recipient_names": [str(partner.display_name or "").strip() for partner in partners if partner.display_name],
            "conversation_key": _conversation_key(partner_ids),
            "conversation_title": self._conversation_title(partner_ids),
            "date": message.date.isoformat() if message.date else "",
            "is_outgoing": bool(message.author_id and message.author_id.id == self.env.user.partner_id.id),
        }

    def _conversation_title(self, partner_ids: List[int]) -> str:
        current_partner_id = int(self.env.user.partner_id.id or 0) if self.env.user.partner_id else 0
        other_ids = [pid for pid in partner_ids if pid != current_partner_id]
        partners = self.env["res.partner"].browse(other_ids).exists()
        names = [str(partner.display_name or "").strip() for partner in partners if partner.display_name]
        if names:
            return "、".join(names[:4]) + (" 等" if len(names) > 4 else "")
        return "自己"

    def _visible_global_message_domain(self) -> list[Any]:
        partner = self.env.user.partner_id
        return [
            ("subject", "=", GLOBAL_MESSAGE_SUBJECT),
            "|",
            ("partner_ids", "in", [partner.id]),
            ("author_id", "=", partner.id),
        ]

    def _visible_messages(self, *, limit: int = 100, since_id: int = 0):
        domain = self._visible_global_message_domain()
        if since_id:
            domain.append(("id", ">", int(since_id)))
        rows = self.env["mail.message"].search(domain, order="id desc", limit=limit)
        rows.check_access_rule("read")
        return rows

    def _unread_counts_by_conversation(self, message_ids: List[int] | None = None) -> dict[str, int]:
        partner = self.env.user.partner_id
        if not partner:
            return {}
        domain: list[Any] = [
            ("res_partner_id", "=", partner.id),
            ("is_read", "=", False),
            ("mail_message_id.subject", "=", GLOBAL_MESSAGE_SUBJECT),
        ]
        if message_ids:
            domain.append(("mail_message_id", "in", message_ids))
        notifications = self.env["mail.notification"].search(domain)
        counts: dict[str, int] = {}
        for notification in notifications:
            key = _conversation_key(_conversation_partner_ids(notification.mail_message_id))
            counts[key] = counts.get(key, 0) + 1
        return counts


class GlobalMessageInboxHandler(_GlobalMessageBaseHandler):
    INTENT_TYPE = "global.message.inbox"
    DESCRIPTION = "Fetch station-wide direct messages for current user"

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        limit, limit_error = parse_positive_int(params.get("limit"), allow_empty=True)
        if limit_error:
            return self._err(400, "limit 无效")
        limit = min(limit or 30, 100)
        since_id, since_error = parse_positive_int(params.get("since_id"), allow_empty=True)
        if since_error:
            return self._err(400, "since_id 无效")

        partner = self.env.user.partner_id
        if not partner:
            return self._err(403, "当前用户缺少联系人，无法读取消息")

        try:
            Message = self.env["mail.message"]
            Message.check_access_rights("read")
            conversation_key = str(params.get("conversation_key") or "").strip()
            rows = self._visible_messages(limit=max(limit * 4, limit), since_id=since_id or 0)
            if conversation_key:
                rows = rows.filtered(lambda message: _conversation_key(_conversation_partner_ids(message)) == conversation_key)
            rows = rows[:limit]
            items = [self._serialize_message(row) for row in reversed(rows)]
            latest_id = max([item["id"] for item in items], default=since_id or 0)
            return {
                "items": items,
                "latest_id": latest_id,
                "source_authority": self.source_authority_contract(),
            }, {"source_authority": self.source_authority_contract()}
        except AccessError:
            return self._err(403, "无权限读取全局消息")
        except Exception:
            return self._err(500, "读取全局消息失败")


class GlobalMessageConversationsHandler(_GlobalMessageBaseHandler):
    INTENT_TYPE = "global.message.conversations"
    DESCRIPTION = "Fetch station-wide message conversations for current user"

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        limit, limit_error = parse_positive_int(params.get("limit"), allow_empty=True)
        if limit_error:
            return self._err(400, "limit 无效")
        limit = min(limit or 30, 80)
        partner = self.env.user.partner_id
        if not partner:
            return self._err(403, "当前用户缺少联系人，无法读取消息")

        try:
            self.env["mail.message"].check_access_rights("read")
            rows = self._visible_messages(limit=300)
            unread_counts = self._unread_counts_by_conversation(rows.ids)
            conversations: dict[str, dict[str, Any]] = {}
            for message in rows:
                partner_ids = _conversation_partner_ids(message)
                key = _conversation_key(partner_ids)
                if key in conversations:
                    continue
                conversations[key] = {
                    "key": key,
                    "title": self._conversation_title(partner_ids),
                    "participant_partner_ids": partner_ids,
                    "participant_user_ids": self._partner_user_ids(partner_ids),
                    "latest_message": self._serialize_message(message),
                    "latest_message_id": int(message.id),
                    "latest_date": message.date.isoformat() if message.date else "",
                    "unread_count": unread_counts.get(key, 0),
                }
                if len(conversations) >= limit:
                    break
            items = list(conversations.values())
            return {
                "items": items,
                "total_unread": sum(int(item.get("unread_count") or 0) for item in items),
                "source_authority": self.source_authority_contract(),
            }, {"source_authority": self.source_authority_contract()}
        except AccessError:
            return self._err(403, "无权限读取全局会话")
        except Exception:
            return self._err(500, "读取全局会话失败")

    def _partner_user_ids(self, partner_ids: List[int]) -> List[int]:
        users = self.env["res.users"].search([("partner_id", "in", partner_ids), ("active", "=", True)])
        return [int(uid) for uid in users.ids if uid]


class GlobalMessageSendHandler(_GlobalMessageBaseHandler):
    INTENT_TYPE = "global.message.send"
    DESCRIPTION = "Send a station-wide direct message to internal users"
    REQUIRED_GROUPS = ["smart_core.group_smart_core_data_operator"]
    ACL_MODE = "explicit_check"
    NON_IDEMPOTENT_ALLOWED = "global station messages append collaboration history and should not replay"

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        body = str(params.get("body") or "").strip()
        recipient_user_ids = _list_ints(params.get("recipient_user_ids") or params.get("user_ids"))
        if not body:
            return self._err(400, "请输入消息内容")
        if not recipient_user_ids:
            return self._err(400, "请选择接收人")

        try:
            self.env["mail.message"].check_access_rights("create")
            users = self._allowed_users(recipient_user_ids)
            partner_ids = [int(pid) for pid in users.mapped("partner_id").ids if pid]
            if not partner_ids:
                return self._err(400, "接收人无效")
            if self.env.user.partner_id:
                partner_ids.append(int(self.env.user.partner_id.id))
            message = self.env["mail.message"].with_context(
                mail_create_nosubscribe=True,
                mail_notify_noemail=True,
                mail_notify_force_send=False,
                mail_post_autofollow=False,
                tracking_disable=True,
            ).create({
                "subject": GLOBAL_MESSAGE_SUBJECT,
                "body": f"<p>{escape(body).replace(chr(10), '<br/>')}</p>",
                "message_type": "notification",
                "author_id": self.env.user.partner_id.id,
                "email_from": _resolve_email_from(self.env.user),
            })
            self._link_message_partners(message, partner_ids)
            self._create_notifications(message, partner_ids)
            return {
                "ok": True,
                "data": {"result": {"message_id": int(message.id), "success": True}},
                "meta": {"source_authority": self.source_authority_contract()},
            }
        except AccessError:
            return self._err(403, "无权限发送全局消息")
        except Exception:
            return self._err(500, "发送全局消息失败")

    def _link_message_partners(self, message, partner_ids: List[int]) -> None:
        field = self.env["mail.message"]._fields.get("partner_ids")
        relation = getattr(field, "relation", "") or "mail_message_res_partner_rel"
        column1 = getattr(field, "column1", "") or "mail_message_id"
        column2 = getattr(field, "column2", "") or "res_partner_id"
        for partner_id in sorted(set(int(pid) for pid in partner_ids if int(pid or 0) > 0)):
            self.env.cr.execute(
                f'INSERT INTO "{relation}" ("{column1}", "{column2}") VALUES (%s, %s) ON CONFLICT DO NOTHING',
                (int(message.id), partner_id),
            )

    def _create_notifications(self, message, partner_ids: List[int]) -> None:
        Notification = self.env["mail.notification"]
        author_partner_id = int(self.env.user.partner_id.id or 0) if self.env.user.partner_id else 0
        for partner_id in sorted(set(int(pid) for pid in partner_ids if int(pid or 0) > 0)):
            existing = Notification.search([
                ("mail_message_id", "=", message.id),
                ("res_partner_id", "=", partner_id),
            ], limit=1)
            values = {
                "notification_type": "inbox",
                "notification_status": "sent",
                "is_read": partner_id == author_partner_id,
            }
            if partner_id == author_partner_id:
                values["read_date"] = fields.Datetime.now()
            if existing:
                existing.write(values)
            else:
                Notification.create({
                    "mail_message_id": message.id,
                    "res_partner_id": partner_id,
                    **values,
                })


class GlobalMessageReadHandler(_GlobalMessageBaseHandler):
    INTENT_TYPE = "global.message.read"
    DESCRIPTION = "Mark station-wide direct messages as read for current user"
    REQUIRED_GROUPS = ["smart_core.group_smart_core_data_operator"]
    ACL_MODE = "explicit_check"
    NON_IDEMPOTENT_ALLOWED = "message read state mutates current user's notification state"

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        conversation_key = str(params.get("conversation_key") or "").strip()
        message_ids = _list_ints(params.get("message_ids"))
        partner = self.env.user.partner_id
        if not partner:
            return self._err(403, "当前用户缺少联系人，无法标记已读")
        try:
            domain: list[Any] = [
                ("res_partner_id", "=", partner.id),
                ("is_read", "=", False),
                ("mail_message_id.subject", "=", GLOBAL_MESSAGE_SUBJECT),
            ]
            if message_ids:
                domain.append(("mail_message_id", "in", message_ids))
            notifications = self.env["mail.notification"].search(domain)
            if conversation_key:
                notifications = notifications.filtered(
                    lambda notification: _conversation_key(_conversation_partner_ids(notification.mail_message_id)) == conversation_key
                )
            count = len(notifications)
            if notifications:
                notifications.write({"is_read": True, "read_date": fields.Datetime.now()})
            return {
                "ok": True,
                "data": {"result": {"updated": count}},
                "meta": {"source_authority": self.source_authority_contract()},
            }
        except AccessError:
            return self._err(403, "无权限标记全局消息")
        except Exception:
            return self._err(500, "标记消息失败")


def _resolve_email_from(user) -> str:
    email = str(user.email or user.partner_id.email or "").strip()
    if email:
        return user.email_formatted or formataddr((user.display_name or user.login or "User", email))
    login = re.sub(r"[^A-Za-z0-9_.-]+", ".", str(user.login or "user").strip()).strip(".") or "user"
    display = str(user.display_name or user.login or "User").strip() or "User"
    return formataddr((display, f"{login}@example.invalid"))


def _plain_text(html: Any) -> str:
    text = re.sub(r"<br\s*/?>", "\n", str(html or ""), flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def _author_display(message) -> str:
    partner_name = str(message.author_id.display_name or "").strip() if message.author_id else ""
    if partner_name:
        return partner_name
    email_from = str(message.email_from or "").strip()
    if email_from:
        parsed_name, parsed_email = parseaddr(email_from)
        raw = parsed_name or parsed_email or email_from
        try:
            decoded = str(make_header(decode_header(raw))).strip()
        except Exception:
            decoded = raw.strip()
        if decoded:
            return decoded
    return "系统"


def _conversation_partner_ids(message) -> List[int]:
    partner_ids = set(int(pid) for pid in message.partner_ids.ids if pid)
    notifications = message.env["mail.notification"].search([("mail_message_id", "=", message.id)])
    partner_ids.update(int(pid) for pid in notifications.mapped("res_partner_id").ids if pid)
    if message.author_id:
        partner_ids.add(int(message.author_id.id))
    return sorted(partner_ids)


def _message_partners(message):
    partner_ids = _conversation_partner_ids(message)
    return message.env["res.partner"].browse(partner_ids).exists()


def _conversation_key(partner_ids: Iterable[int]) -> str:
    ids = sorted(set(int(pid) for pid in partner_ids if int(pid or 0) > 0))
    return "partners:" + ",".join(str(pid) for pid in ids)


def _list_ints(value) -> List[int]:
    if value is None or value is False:
        return []
    raw = value if isinstance(value, (list, tuple, set)) else [value]
    out: List[int] = []
    for item in raw:
        try:
            parsed = int(item)
        except Exception:
            continue
        if parsed > 0 and parsed not in out:
            out.append(parsed)
    return out
