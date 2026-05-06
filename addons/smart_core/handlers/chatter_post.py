# -*- coding: utf-8 -*-
# 📁 smart_core/handlers/chatter_post.py
import re
from email.utils import formataddr
from typing import List

from odoo.exceptions import AccessError, UserError

from ..core.base_handler import BaseIntentHandler
from ..core.project_context import (
    project_scope_denied_response,
    record_in_project_scope,
    selected_project_id_from_context,
)
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
        res_id = params.get("res_id") or params.get("record_id")
        body = params.get("body")
        subject = params.get("subject")
        mode = str(params.get("mode") or "message").strip().lower()
        trace_id = self.context.get("trace_id") if isinstance(self.context, dict) else ""

        if not model or not res_id or not body:
            return self._failure(REASON_MISSING_PARAMS, "缺少参数 model/res_id/body", 400, trace_id)

        try:
            self.env[model].check_access_rights("write")
            record = self.env[model].browse(int(res_id))
            if not record.exists():
                return self._failure(REASON_NOT_FOUND, "记录不存在", 404, trace_id)
            current_project_id = selected_project_id_from_context(params, self.context if isinstance(self.context, dict) else {})
            in_scope, scope_meta = record_in_project_scope(self.env[model], int(record.id), current_project_id)
            if not in_scope:
                return project_scope_denied_response(scope_meta)
            record.check_access_rule("write")

            if not hasattr(record, "message_post"):
                return self._failure(REASON_METHOD_NOT_CALLABLE, "模型不支持 chatter", 400, trace_id)

            mention_partner_ids = self._resolve_mentions(str(body or ""))
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

            thread = record.with_context(mail_create_nosubscribe=True, mail_notify_noemail=True)
            try:
                message = thread.message_post(**post_kwargs)
            except UserError as exc:
                message = None
                message_text = str(exc) or ""
                if mode == "message" and "发件人的电子邮件地址" in message_text:
                    fallback_kwargs = dict(post_kwargs)
                    fallback_kwargs["subtype_xmlid"] = "mail.mt_note"
                    message = thread.message_post(**fallback_kwargs)
                if not message:
                    raise
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

    def _resolve_mentions(self, body: str) -> List[int]:
        tokens = set(re.findall(r"@([A-Za-z0-9_.-]{2,64})", body or ""))
        if not tokens:
            return []
        users = self.env["res.users"].search([("login", "in", list(tokens))], limit=20)
        partner_ids = users.mapped("partner_id").ids
        return [int(pid) for pid in partner_ids if pid]

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
