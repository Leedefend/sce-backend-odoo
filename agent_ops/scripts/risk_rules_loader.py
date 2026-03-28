#!/usr/bin/env python3
from __future__ import annotations

from common import AGENT_OPS, load_yaml


def load_rules() -> dict:
    return {
        "watchlist": load_yaml(AGENT_OPS / "policies" / "repo_watchlist.yaml") or {},
        "dirty_baseline": load_yaml(AGENT_OPS / "policies" / "repo_dirty_baseline.yaml") or {},
        "high_risk": load_yaml(AGENT_OPS / "policies" / "high_risk_change_policy.yaml") or {},
        "stop_conditions": load_yaml(AGENT_OPS / "policies" / "stop_conditions.yaml") or {},
    }
