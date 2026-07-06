# -*- coding: utf-8 -*-
# 📁 smart_core/handlers/chatter_post.py
import re
from html import escape
from email.utils import formataddr
from typing import List

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
from ..core.request_params import parse_positive_int
from .collaboration_users import is_collaboration_visible_user
from ..utils.reason_codes import (
    REASON_MISSING_PARAMS,
    REASON_METHOD_NOT_CALLABLE,
    REASON_NOT_FOUND,
    REASON_OK,
    REASON_PERMISSION_DENIED,
    REASON_SYSTEM_ERROR,
    REASON_USER_ERROR,
    failure_meta_for_reason,
)

class ChatterPostHandler(BaseIntentHandler):
    INTENT_TYPE = "chatter.post"
    DESCRIPTION = "Post a chatter message (mail.thread)"
    REQUIRED_GROUPS = ["smart_core.group_smart_core_data_operator"]
    ACL_MODE = "explicit_check"
    NON_IDEMPOTENT_ALLOWED = "message_post appends chatter history and should not replay"
    SOURCE_AUTHORITY = "mail.message"
    SOURCE_KIND = "odoo_collaboration_message_write_proxy"
    SOURCE_AUTHORITIES = ("mail.message", "mail.thread", "res.partner", "odoo.orm", "ir.rule", "record_context_model")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authority": cls.SOURCE_AUTHORITY,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "write_proxy": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = params.get("model")
        res_id = params.get("res_id") if "res_id" in params else params.get("record_id")
        body = params.get("body")
        subject = params.get("subject")
        mode = str(params.get("mode") or "message").strip().lower()
        explicit_user_ids = _list_ints(params.get("mention_user_ids") or params.get("mentioned_user_ids"))
        explicit_partner_ids = _list_ints(params.get("partner_ids") or params.get("mention_partner_ids"))
        trace_id = self.context.get("trace_id") if isinstance(self.context, dict) else ""

        if not model or _is_empty_param(res_id) or not body:
            return self._failure(REASON_MISSING_PARAMS, "缺少参数 model/res_id/body", 400, trace_id)
        if model not in self.env:
            return self._failure(REASON_NOT_FOUND, "模型不存在", 404, trace_id)
        res_id, res_id_error = parse_positive_int(res_id)
        if res_id_error:
            return self._failure(REASON_USER_ERROR, "res_id 无效", 400, trace_id)

        try:
            self.env[model].check_access_rights("write")
            record = self.env[model].browse(res_id)
            if not record.exists():
                return self._failure(REASON_NOT_FOUND, "记录不存在", 404, trace_id)
            in_scope, scope_meta = record_in_business_scope(
                self.env[model],
                int(record.id),
                params,
                self.context if isinstance(self.context, dict) else {},
            )
            if not in_scope:
                return record_scope_denied_response(scope_meta)
            record.check_access_rule("write")

            if not hasattr(record, "message_post"):
                return self._failure(REASON_METHOD_NOT_CALLABLE, "模型不支持 chatter", 400, trace_id)

            mention_partner_ids = self._resolve_mention_partners(
                body=str(body or ""),
                user_ids=explicit_user_ids,
                partner_ids=explicit_partner_ids,
            )
            subtype_xmlid = "mail.mt_note" if mode == "note" else "mail.mt_comment"
            post_kwargs = {
                "body": body,
                "subject": subject,
                "message_type": "comment",
                "subtype_xmlid": subtype_xmlid,
                "email_from": _resolve_email_from(self.env.user),
            }
            if mention_partner_ids:
                post_kwargs["partner_ids"] = mention_partner_ids

            message = self._create_log_message(
                model=model,
                record_id=record.id,
                body=str(body or ""),
                subject=subject,
                subtype_xmlid=subtype_xmlid,
                partner_ids=mention_partner_ids,
            )
            return {
                "ok": True,
                "data": {
                    "result": {
                        "message_id": message.id,
                        "success": True,
                        "reason_code": REASON_OK,
                        "message": "Comment posted",
                        "mode": mode,
                        "mentioned_partner_ids": mention_partner_ids,
                    }
                },
                "meta": {
                    "trace_id": trace_id,
                    "source_authority": self.source_authority_contract(),
                    "legacy_source_authority": self.SOURCE_AUTHORITY,
                },
            }
        except AccessError:
            return self._failure(REASON_PERMISSION_DENIED, "无权限发布评论", 403, trace_id)
        except UserError as exc:
            return self._failure(REASON_USER_ERROR, str(exc) or "业务规则不允许", 400, trace_id)
        except Exception:
            return self._failure(REASON_SYSTEM_ERROR, "发布评论失败", 500, trace_id)

    def _resolve_mention_partners(self, body: str, user_ids: List[int], partner_ids: List[int]) -> List[int]:
        partner_ids_out: set[int] = set()
        if partner_ids:
            partners = self.env["res.partner"].browse(partner_ids).exists()
            partner_ids_out.update(int(pid) for pid in partners.ids if pid)
        if user_ids:
            users = self._allowed_mention_users([int(uid) for uid in user_ids if uid])
            partner_ids_out.update(int(pid) for pid in users.mapped("partner_id").ids if pid)
        partner_ids_out.update(self._resolve_mentions(body))
        return sorted(partner_ids_out)

    def _allowed_mention_users(self, user_ids: List[int]):
        if not user_ids:
            return self.env["res.users"]
        users = self.env["res.users"].browse(user_ids).exists().filtered(lambda user: bool(user.active))
        internal_group = self.env.ref("base.group_user", raise_if_not_found=False)
        if internal_group:
            users = users.filtered(lambda user: internal_group in user.groups_id)
        users = users.filtered(is_collaboration_visible_user)
        return users

    def _resolve_mentions(self, body: str) -> List[int]:
        tokens = set(re.findall(r"@([A-Za-z0-9_.-]{2,64})", body or ""))
        if not tokens:
            return []
        users = self._allowed_mention_users(self.env["res.users"].search([("login", "in", list(tokens))], limit=20).ids)
        partner_ids = users.mapped("partner_id").ids
        return [int(pid) for pid in partner_ids if pid]

    def _create_log_message(self, *, model: str, record_id: int, body: str, subject, subtype_xmlid: str, partner_ids: List[int]):
        subtype = self.env.ref(subtype_xmlid, raise_if_not_found=False)
        vals = {
            "model": model,
            "res_id": int(record_id),
            "body": f"<p>{escape(body).replace(chr(10), '<br/>')}</p>",
            "subject": subject,
            "message_type": "comment",
            "author_id": self.env.user.partner_id.id,
            "email_from": _resolve_email_from(self.env.user),
        }
        if subtype:
            vals["subtype_id"] = subtype.id
        message = self.env["mail.message"].with_context(
            mail_create_nosubscribe=True,
            mail_notify_noemail=True,
            mail_notify_force_send=False,
            mail_post_autofollow=False,
            tracking_disable=True,
        ).create(vals)
        self._link_message_partners(message, partner_ids)
        return message

    def _link_message_partners(self, message, partner_ids: List[int]) -> None:
        if not partner_ids:
            return
        field = self.env["mail.message"]._fields.get("partner_ids")
        relation = getattr(field, "relation", "") or "mail_message_res_partner_rel"
        column1 = getattr(field, "column1", "") or "mail_message_id"
        column2 = getattr(field, "column2", "") or "res_partner_id"
        for partner_id in sorted(set(int(pid) for pid in partner_ids if int(pid or 0) > 0)):
            self.env.cr.execute(
                f'INSERT INTO "{relation}" ("{column1}", "{column2}") VALUES (%s, %s) ON CONFLICT DO NOTHING',
                (int(message.id), partner_id),
            )

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


def _resolve_email_from(user) -> str:
    email = str(user.email or user.partner_id.email or "").strip()
    if email:
        return user.email_formatted or formataddr((user.display_name or user.login or "User", email))
    login = re.sub(r"[^A-Za-z0-9_.-]+", ".", str(user.login or "user").strip()).strip(".") or "user"
    display = str(user.display_name or user.login or "User").strip() or "User"
    return formataddr((display, f"{login}@example.invalid"))


def _is_empty_param(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


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
