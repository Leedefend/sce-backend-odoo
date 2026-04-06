# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable


def build_governance_projection(rows: Iterable[Dict[str, Any]], errors: Dict[str, Any]) -> Dict[str, Any]:
    count = 0
    for row in rows:
        if isinstance(row, dict):
            count += 1
    return {
        "capability_count": count,
        "errors": errors if isinstance(errors, dict) else {},
    }
