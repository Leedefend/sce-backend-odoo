# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List

from .contribution_loader import load_capability_contributions
from .merge_engine import merge_capability_contributions
from .ownership import check_platform_owner_constraints
from .freeze import build_registry_snapshot


class CapabilityRegistry:
    def __init__(self, *, platform_owner: str = "smart_core"):
        self.platform_owner = platform_owner

    def build(self, env, user=None) -> Dict[str, Any]:
        rows, load_errors = load_capability_contributions(env, user=user)
        merged_rows, merge_errors = merge_capability_contributions(rows)
        owner_errors = check_platform_owner_constraints(merged_rows, platform_owner=self.platform_owner)
        snapshot = build_registry_snapshot(merged_rows)
        return {
            "rows": merged_rows,
            "snapshot": snapshot,
            "errors": {
                "load": load_errors,
                "merge": merge_errors,
                "ownership": owner_errors,
            },
        }

    @staticmethod
    def key_map(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            identity = row.get("identity") if isinstance(row, dict) else {}
            key = str((identity or {}).get("key") or "").strip()
            if key:
                out[key] = row
        return out
