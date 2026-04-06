# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List


def check_platform_owner_constraints(rows: Iterable[Dict[str, Any]], *, platform_owner: str = "smart_core") -> List[str]:
    errors: List[str] = []
    for row in rows:
        identity = row.get("identity") if isinstance(row, dict) else {}
        ownership = row.get("ownership") if isinstance(row, dict) else {}
        key = str((identity or {}).get("key") or "").strip()
        owner_module = str((ownership or {}).get("owner_module") or "").strip()
        if not key:
            continue
        if owner_module and owner_module != platform_owner:
            errors.append(f"owner violation key={key} owner={owner_module}")
    return errors
