# -*- coding: utf-8 -*-
from __future__ import annotations


class CapabilitySurfaceEngine:
    def build_summary(self, capabilities, capability_groups) -> dict:
        summary = {
            "capability_count": 0,
            "group_count": 0,
            "state_counts": {"READY": 0, "LOCKED": 0, "PREVIEW": 0},
            "capability_state_counts": {"allow": 0, "readonly": 0, "deny": 0, "pending": 0, "coming_soon": 0},
        }
        caps = capabilities if isinstance(capabilities, list) else []
        groups = capability_groups if isinstance(capability_groups, list) else []
        summary["capability_count"] = len(caps)
        summary["group_count"] = len(groups)
        for cap in caps:
            if not isinstance(cap, dict):
                continue
            state = str(cap.get("state") or "").strip().upper()
            capability_state = str(cap.get("capability_state") or "").strip().lower()
            if state in summary["state_counts"]:
                summary["state_counts"][state] = int(summary["state_counts"].get(state) or 0) + 1
            if capability_state in summary["capability_state_counts"]:
                summary["capability_state_counts"][capability_state] = (
                    int(summary["capability_state_counts"].get(capability_state) or 0) + 1
                )
        return summary
