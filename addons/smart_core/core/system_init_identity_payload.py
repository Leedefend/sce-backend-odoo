# -*- coding: utf-8 -*-
from __future__ import annotations


class SystemInitIdentityPayload:
    @staticmethod
    def build(user, user_groups_xmlids: list) -> dict:
        return {
            "id": user.id,
            "name": user.name,
            "groups_xmlids": list(user_groups_xmlids),
            "lang": user.lang,
            "tz": user.tz,
            "company_id": user.company_id.id if user.company_id else None,
            "company_name": user.company_id.display_name if user.company_id else "",
        }
