# -*- coding: utf-8 -*-
from typing import Any

from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler
from ..core.request_params import parse_positive_int


class CollaborationUsersSearchHandler(BaseIntentHandler):
    INTENT_TYPE = "collaboration.users.search"
    DESCRIPTION = "Search active internal users for collaboration mentions and activity assignment"
    SOURCE_KIND = "odoo_collaboration_user_directory_projection"
    SOURCE_AUTHORITIES = ("res.users", "res.partner", "res.groups", "ir.rule")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        query = str(params.get("query") or params.get("q") or "").strip()
        limit, limit_error = parse_positive_int(params.get("limit"), allow_empty=True)
        if limit_error:
            return self._err(400, "limit 无效")
        limit = min(limit or 20, 50)

        try:
            Users = self.env["res.users"]
            Users.check_access_rights("read")
            domain = self._user_domain(query)
            rows = Users.search(domain, order="name, login", limit=max(limit * 4, 80))
            rows.check_access_rule("read")
            users = [
                self._serialize_user(row)
                for row in rows
                if row.exists() and is_collaboration_visible_user(row)
            ][:limit]
            return {
                "items": users,
                "source_authority": self.source_authority_contract(),
            }, {"source_authority": self.source_authority_contract()}
        except AccessError:
            return self._err(403, "无权限读取协作人员")
        except Exception:
            return self._err(500, "读取协作人员失败")

    def _user_domain(self, query: str) -> list[Any]:
        domain: list[Any] = [("active", "=", True)]
        internal_group = self.env.ref("base.group_user", raise_if_not_found=False)
        if internal_group:
            domain.append(("groups_id", "in", internal_group.id))
        if query:
            token = query[:80]
            domain.extend(["|", "|", ("name", "ilike", token), ("login", "ilike", token), ("email", "ilike", token)])
        return domain

    def _serialize_user(self, row) -> dict[str, Any]:
        partner = row.partner_id
        return {
            "id": int(row.id),
            "name": str(row.name or row.display_name or row.login or "").strip(),
            "login": str(row.login or "").strip(),
            "email": str(row.email or "").strip(),
            "partner_id": int(partner.id or 0) if partner else 0,
            "partner_name": str(partner.display_name or "").strip() if partner else "",
        }

    def _err(self, code: int, message: str):
        return {
            "ok": False,
            "error": {"code": code, "message": message},
            "code": code,
            "meta": {"source_authority": self.source_authority_contract()},
        }


def is_collaboration_visible_user(user) -> bool:
    login = str(user.login or "").strip().lower()
    name = str(user.name or user.display_name or "").strip().lower()
    email = str(user.email or "").strip().lower()
    if not login:
        return False
    if login.startswith(("demo_", "sc_fx_", "fixture_", "test_", "ceshi", "linshi")):
        return False
    if login in {"demo_business_full", "default"}:
        return False
    hidden_tokens = ("fixture", "smoke")
    if any(token in name for token in hidden_tokens):
        return False
    if any(token in email for token in hidden_tokens):
        return False
    if any(token in name for token in ("测试", "临时账号")):
        return False
    if name.startswith("技术"):
        return False
    return True
