# -*- coding: utf-8 -*-
from __future__ import annotations


class CapabilityService:
    def build_entries(self, *, policy: dict, capabilities: list[dict]) -> list[dict]:
        runtime_index = {}
        for item in capabilities or []:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "").strip()
            if key and key not in runtime_index:
                runtime_index[key] = item

        entries: list[dict] = []
        for row in policy.get("capabilities") or []:
            if not isinstance(row, dict):
                continue
            key = str(row.get("capability_key") or row.get("key") or "").strip()
            if not key:
                continue
            runtime = runtime_index.get(key) or {}
            entries.append(
                {
                    "key": key,
                    "label": str(row.get("label") or runtime.get("ui_label") or runtime.get("name") or key).strip(),
                    "group_key": str(row.get("group_key") or runtime.get("group_key") or "delivery").strip(),
                    "group_label": str(row.get("group_label") or runtime.get("group_label") or "产品交付").strip(),
                    "product_key": str(row.get("product_key") or "").strip(),
                    "target_scene_key": str(row.get("target_scene_key") or runtime.get("target_scene_key") or "").strip(),
                    "delivery_level": str(row.get("delivery_level") or "exclusive").strip(),
                    "entry_kind": str(row.get("entry_kind") or "exclusive").strip(),
                    "runtime_capability_key": str(runtime.get("key") or "").strip(),
                    "runtime_state": str(runtime.get("state") or "").strip() or "POLICY_READY",
                    "runtime_reason_code": str(runtime.get("reason_code") or "").strip(),
                    "source": "delivery_engine_v1",
                }
            )
        return entries

