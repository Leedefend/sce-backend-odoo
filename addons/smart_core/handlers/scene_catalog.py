# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_scene.core.scene_registry_engine import load_scene_registry_content_entries


def _workspace_fallback_scene() -> Dict[str, Any]:
    return {
        "code": "workspace.home",
        "name": "工作台",
        "target": {
            "route": "/s/workspace.home",
            "menu_xmlid": "smart_core.menu_sc_workspace_home",
        },
    }


def _load_catalog_rows() -> List[Dict[str, Any]]:
    rows = load_scene_registry_content_entries(Path(__file__))
    valid: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        code = str(row.get("code") or "").strip()
        target = row.get("target") if isinstance(row.get("target"), dict) else {}
        if not code or not target:
            continue
        valid.append({
            "code": code,
            "name": str(row.get("name") or code),
            "target": target,
            "tags": row.get("tags") if isinstance(row.get("tags"), list) else [],
        })
    if not valid:
        valid.append(_workspace_fallback_scene())
    return valid


class SceneCatalogHandler(BaseIntentHandler):
    INTENT_TYPE = "scene.catalog"
    DESCRIPTION = "返回场景目录（用于按需加载）"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]

    def handle(self, payload=None, ctx=None):
        _ = payload
        _ = ctx
        rows = _load_catalog_rows()
        return {
            "ok": True,
            "data": {
                "scenes": rows,
                "count": len(rows),
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "trace_id": str((self.context or {}).get("trace_id") or ""),
            },
        }


class SceneDetailHandler(BaseIntentHandler):
    INTENT_TYPE = "scene.detail"
    DESCRIPTION = "返回单个场景详情（用于按需加载）"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}
        scene_key = str((params or {}).get("scene_key") or (params or {}).get("key") or "").strip()
        if not scene_key:
            return {
                "ok": False,
                "error": {
                    "code": "MISSING_PARAMS",
                    "message": "缺少参数：scene_key",
                    "suggested_action": "fix_input",
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "trace_id": str((self.context or {}).get("trace_id") or ""),
                },
            }
        rows = _load_catalog_rows()
        for row in rows:
            if str(row.get("code") or "").strip() == scene_key:
                return {
                    "ok": True,
                    "data": {
                        "scene": row,
                    },
                    "meta": {
                        "intent": self.INTENT_TYPE,
                        "trace_id": str((self.context or {}).get("trace_id") or ""),
                    },
                }
        return {
            "ok": False,
            "error": {
                "code": "NOT_FOUND",
                "message": f"scene not found: {scene_key}",
                "suggested_action": "open_workspace_overview",
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "trace_id": str((self.context or {}).get("trace_id") or ""),
            },
        }

