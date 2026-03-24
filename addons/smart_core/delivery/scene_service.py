# -*- coding: utf-8 -*-
from __future__ import annotations


class SceneService:
    def build_entries(self, *, policy: dict, scenes: list[dict]) -> list[dict]:
        scene_index = {}
        for item in scenes or []:
            if not isinstance(item, dict):
                continue
            scene_key = str(item.get("code") or item.get("key") or "").strip()
            if scene_key and scene_key not in scene_index:
                scene_index[scene_key] = item

        entries: list[dict] = []
        for row in policy.get("scenes") or []:
            if not isinstance(row, dict):
                continue
            scene_key = str(row.get("scene_key") or "").strip()
            if not scene_key:
                continue
            source = scene_index.get(scene_key) or {}
            target = source.get("target") if isinstance(source.get("target"), dict) else {}
            route = str(target.get("route") or row.get("route") or f"/s/{scene_key}").strip()
            label = str(
                row.get("label")
                or source.get("name")
                or source.get("title")
                or source.get("label")
                or scene_key
            ).strip()
            entries.append(
                {
                    "scene_key": scene_key,
                    "label": label,
                    "route": route,
                    "product_key": str(row.get("product_key") or "").strip(),
                    "capability_key": str(row.get("capability_key") or "").strip(),
                    "requires_project_context": bool(row.get("requires_project_context", False)),
                    "state": "present" if source else "policy_only",
                    "source": "delivery_engine_v1",
                }
            )
        return entries

