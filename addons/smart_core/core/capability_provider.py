# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List


def load_capabilities_for_user(env, user) -> List[dict]:
    try:
        cap_model = env["sc.capability"].sudo()
    except Exception:
        return []
    try:
        caps = cap_model.search([("active", "=", True)], order="sequence, id")
    except Exception:
        return []
    out: List[dict] = []
    for rec in caps:
        try:
            if rec._user_visible(user):
                out.append(rec.to_public_dict(user))
        except Exception:
            continue
    return out
