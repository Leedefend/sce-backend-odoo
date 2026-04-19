# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple

from .contribution_loader import load_capability_contributions, load_capability_contributions_with_timings
from .merge_engine import merge_capability_contributions
from .ownership import check_platform_owner_constraints
from .freeze import build_registry_snapshot


class CapabilityRegistry:
    def __init__(self, *, platform_owner: str = "smart_core"):
        self.platform_owner = platform_owner

    def build(self, env, user=None) -> Dict[str, Any]:
        bundle, _timings = self.build_with_timings(env, user=user)
        return bundle

    def build_with_timings(self, env, user=None) -> Tuple[Dict[str, Any], dict[str, int]]:
        timings_ms: dict[str, int] = {}

        def _mark(stage: str, started_at: float) -> float:
            timings_ms[stage] = int((time.perf_counter() - started_at) * 1000)
            return time.perf_counter()

        stage_ts = time.perf_counter()
        rows, load_errors, load_timings_ms = load_capability_contributions_with_timings(env, user=user)
        stage_ts = _mark("load_capability_contributions", stage_ts)
        if load_timings_ms:
            for key, value in load_timings_ms.items():
                timings_ms[f"load_capability_contributions.{key}"] = int(value)
        merged_rows, merge_errors = merge_capability_contributions(rows)
        stage_ts = _mark("merge_capability_contributions", stage_ts)
        owner_errors = check_platform_owner_constraints(merged_rows, platform_owner=self.platform_owner)
        stage_ts = _mark("check_platform_owner_constraints", stage_ts)
        snapshot = build_registry_snapshot(merged_rows)
        _mark("build_registry_snapshot", stage_ts)
        return {
            "rows": merged_rows,
            "snapshot": snapshot,
            "errors": {
                "load": load_errors,
                "merge": merge_errors,
                "ownership": owner_errors,
            },
        }, timings_ms

    @staticmethod
    def key_map(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            identity = row.get("identity") if isinstance(row, dict) else {}
            key = str((identity or {}).get("key") or "").strip()
            if key:
                out[key] = row
        return out
