# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from ..core.ownership import check_platform_owner_constraints


def run_ownership_lint(rows: Iterable[Dict[str, Any]], *, platform_owner: str = "smart_core") -> List[str]:
    return check_platform_owner_constraints(rows, platform_owner=platform_owner)
