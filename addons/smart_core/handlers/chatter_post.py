# -*- coding: utf-8 -*-
# 📁 smart_core/handlers/chatter_post.py
import re
from typing import List

from odoo.exceptions import AccessError, UserError

from ..core.base_handler import BaseIntentHandler
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
    NON_IDEMPOTENT_ALLOWED = "message_post appends chatter history and should not replay"

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = params.get("model")
        res_id = params.get("res_id") or params.get("record_id")
        body = params.get("body")
        subject = params.get("subject")
        trace_id = self.context.get("trace_id") if isinstance(self.context, dict) else ""

        if not model or not res_id or not body:
            return self._failure(REASON_MISSING_PARAMS, "缺少参数 model/res_id/body", 400, trace_id)

        try:
            self.env[model].check_access_rights("write")
            record = self.env[model].browse(int(res_id))
            if not record.exists():
                return self._failure(REASON_NOT_FOUND, "记录不存在", 404, trace_id)
            record.check_access_rule("write")

            if not hasattr(record, "message_post"):
                return self._failure(REASON_METHOD_NOT_CALLABLE, "模型不支持 chatter", 400, trace_id)

            mention_partner_ids = self._resolve_mentions(str(body or ""))
            post_kwargs = {"body": body, "subject": subject}
            if mention_partner_ids:
                post_kwargs["partner_ids"] = mention_partner_ids

            message = record.message_post(**post_kwargs)
            return {
                "ok": True,
                "data": {
                    "result": {
                        "message_id": message.id,
                        "success": True,
                        "reason_code": REASON_OK,
                        "message": "Comment posted",
                        "mentioned_partner_ids": mention_partner_ids,
                    }
                },
                "meta": {"trace_id": trace_id},
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
            "meta": {"trace_id": trace_id},
        }
