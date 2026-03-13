# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Tuple


REQUIRED_TOP_LEVEL = (
    "scene",
    "page",
    "zones",
    "record",
    "permissions",
    "actions",
    "extensions",
    "diagnostics",
)


def check_top_level_shape(payload: dict) -> Tuple[bool, Dict[str, object]]:
    if not isinstance(payload, dict):
        return False, {"code": "contract_not_dict"}
    missing = [key for key in REQUIRED_TOP_LEVEL if key not in payload]
    if missing:
        return False, {"code": "missing_top_level", "keys": missing}
    return True, {"code": "ok"}

