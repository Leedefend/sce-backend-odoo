# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.core.runtime_fetch_context_builder import build_runtime_fetch_context
from odoo.addons.smart_core.core.runtime_fetch_handler_helper import (
    build_runtime_fetch_meta,
    parse_runtime_fetch_params,
)
from odoo.addons.smart_core.core.runtime_page_contract_builder import build_runtime_page_contract
from odoo.addons.smart_core.core.runtime_workspace_collection_helper import collect_workspace_collections

class PageContractHandler(BaseIntentHandler):
    INTENT_TYPE = "page.contract"
    DESCRIPTION = "返回单页 page contract（运行时按需加载）"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]

    @classmethod
    def aliases(cls):
        return ["scene.page_contract"]

    def handle(self, payload=None, ctx=None):
        params = parse_runtime_fetch_params(payload, self.params)
        page_key = str(params.get("page_key") or params.get("key") or "").strip().lower()
        if not page_key:
            return {
                "ok": False,
                "error": {
                    "code": "MISSING_PARAMS",
                    "message": "缺少参数：page_key",
                    "suggested_action": "fix_input",
                },
                "meta": build_runtime_fetch_meta(self.INTENT_TYPE, self.context),
            }
        data = build_runtime_fetch_context(self.env, params=params)
        contract = build_runtime_page_contract(page_key, data)
        if not contract:
            return {
                "ok": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"page contract not found: {page_key}",
                    "suggested_action": "open_workspace_overview",
                },
                "meta": build_runtime_fetch_meta(self.INTENT_TYPE, self.context),
            }
        return {
            "ok": True,
            "data": {
                "page_key": page_key,
                "page_contract": contract,
            },
            "meta": build_runtime_fetch_meta(self.INTENT_TYPE, self.context),
        }


class WorkspaceCollectionsHandler(BaseIntentHandler):
    INTENT_TYPE = "workspace.collections"
    DESCRIPTION = "返回工作台运行时集合（按需加载）"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]

    def handle(self, payload=None, ctx=None):
        params = parse_runtime_fetch_params(payload, self.params)
        raw_keys = params.get("keys")
        keys = raw_keys if isinstance(raw_keys, list) else []
        data = build_runtime_fetch_context(self.env, params=params)
        collections = collect_workspace_collections(data, keys=keys)
        return {
            "ok": True,
            "data": {
                "collections": collections,
                "keys": sorted(list(collections.keys())),
                "count": len(collections),
            },
            "meta": build_runtime_fetch_meta(self.INTENT_TYPE, self.context),
        }
