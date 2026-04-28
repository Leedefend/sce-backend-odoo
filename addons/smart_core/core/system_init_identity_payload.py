# -*- coding: utf-8 -*-
from __future__ import annotations


class SystemInitIdentityPayload:
    @staticmethod
    def build(user, user_groups_xmlids: list) -> dict:
        company = user.company_id if user.company_id else None
        company_id = company.id if company else None
        company_name = (company.name or "").strip() if company else ""
        return {
            "id": user.id,
            "name": user.name,
            "groups_xmlids": list(user_groups_xmlids),
            "lang": user.lang,
            "tz": user.tz,
            "company_id": company_id,
            "company_name": company_name,
            "company": {
                "id": company_id,
                "name": company_name,
                "display_name": company_name,
            } if company_id else None,
        }
