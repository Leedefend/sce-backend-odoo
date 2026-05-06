# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ..core.base_handler import BaseIntentHandler
from ..core.intent_execution_result import IntentExecutionResult
from ..core.unified_page_contract_v2_assembler import (
    CONTRACT_VERSION,
    assemble_unified_page_contract_v2,
)
from ..core.unified_page_contract_v2_client import (
    MOBILE_CLIENT_TYPES,
    resolve_client_type,
    resolve_delivery_profile,
    trim_unified_page_contract_v2,
)
from ..core.scene_provider import load_scenes_from_db_or_fallback
from ..core.request_params import parse_positive_int
from .ui_contract import UiContractHandler

_logger = logging.getLogger(__name__)


class UiContractV2Handler(BaseIntentHandler):
    INTENT_TYPE = "ui.contract.v2"
    DESCRIPTION = "统一页面契约 v2 入口；以 ui.contract 为事实来源，按终端类型裁剪 v2 契约"
    VERSION = CONTRACT_VERSION
    SOURCE_KIND = "unified_page_contract_v2"
    SOURCE_AUTHORITIES = (
        "ui.contract",
        "ir.ui.view",
        "ir.actions.act_window",
        "ir.ui.menu",
        "ir.model.fields",
        "ir.model.access",
        "ir.rule",
    )
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def handle(self, payload: Optional[Dict[str, Any]] = None, ctx: Optional[Dict[str, Any]] = None):
        params = self._params(payload)
        client_type = resolve_client_type(self._headers(), params)
        delivery_profile = resolve_delivery_profile(client_type, params)
        source_type = str(params.get("source_type") or params.get("sourceType") or "ui.contract").strip()
        if source_type == "scene_contract_v1":
            return self._handle_scene_contract(params, client_type=client_type, delivery_profile=delivery_profile)
        if source_type != "ui.contract":
            return self._err(400, f"unsupported v2 source_type: {source_type}")
        limit_params, limit_error = self._trim_limit_params(params)
        if limit_error:
            return self._err(400, f"{limit_error} 无效")

        ui_params = self._ui_contract_params(params)
        source_result = UiContractHandler(
            self.env,
            su_env=self.su_env,
            request=self.request,
            context=ctx or self.context,
            payload=ui_params,
        ).handle(ui_params, ctx)
        source_envelope = self._envelope(source_result)
        if not source_envelope.get("ok", True):
            return source_result

        ui_data = source_envelope.get("data") or {}
        ui_meta = source_envelope.get("meta") or {}
        ui_data, ui_meta = self._resolve_entry_contract(ui_data, ui_meta, ui_params, ctx)
        model = params.get("model") or ui_data.get("model") or ui_meta.get("model") or ""
        view_type = params.get("view_type") or params.get("viewType") or ui_data.get("view_type") or ui_meta.get("view_type") or "form"
        request_id = (
            params.get("request_id")
            or params.get("requestId")
            or ui_meta.get("trace_id")
            or ui_meta.get("traceId")
            or f"ui.contract.v2.{model or 'unknown'}.{view_type or 'form'}"
        )

        ui_nested_data = ui_data.get("data") if isinstance(ui_data.get("data"), dict) else {}
        source_contract = {
            "ui_contract": ui_data,
            "model": model,
            "view_type": view_type,
            "record_id": params.get("record_id") or params.get("recordId") or ui_params.get("record_id") or ui_params.get("recordId"),
            "render_profile": params.get("render_profile") or params.get("renderProfile") or ui_params.get("render_profile") or ui_params.get("renderProfile"),
            "domain_raw": params.get("domain_raw") or params.get("domainRaw") or ui_params.get("domain_raw") or ui_params.get("domainRaw"),
            "context_raw": params.get("context_raw") or params.get("contextRaw") or ui_params.get("context_raw") or ui_params.get("contextRaw"),
            "context": (
                ui_data.get("context")
                or ((ui_data.get("head") or {}).get("context") if isinstance(ui_data.get("head"), dict) else {})
                or ui_params.get("context")
                or params.get("context")
                or {}
            ),
            "record": (
                ui_data.get("record")
                if isinstance(ui_data.get("record"), dict)
                else (ui_nested_data.get("record") if isinstance(ui_nested_data.get("record"), dict) else {})
            ),
            "source_meta": ui_meta,
        }
        contract_v2 = assemble_unified_page_contract_v2(
            source_contract,
            source_type="ui.contract",
            client_type=client_type,
            request_id=str(request_id),
        )
        contract_v2 = trim_unified_page_contract_v2(
            contract_v2,
            client_type=client_type,
            delivery_profile=delivery_profile,
            **limit_params,
            include_source_compat=client_type not in MOBILE_CLIENT_TYPES,
        )

        return IntentExecutionResult(
            ok=True,
            data=contract_v2,
            meta={
                "intent": self.INTENT_TYPE,
                "version": self.VERSION,
                "contract_version": CONTRACT_VERSION,
                "client_type": client_type,
                "delivery_profile": delivery_profile,
                "source_type": "ui.contract",
                "source_intent": ui_meta.get("intent") or "ui.contract",
                "source_kind": self.SOURCE_KIND,
                "source_authorities": list(self.SOURCE_AUTHORITIES),
                "source_authority": self.source_authority_contract(),
            },
        )

    def _handle_scene_contract(self, params: dict[str, Any], *, client_type: str, delivery_profile: str):
        scene_key = str(params.get("scene_key") or params.get("sceneKey") or "").strip()
        if not scene_key:
            return self._err(400, "missing scene_key for scene_contract_v1")
        limit_params, limit_error = self._trim_limit_params(params)
        if limit_error:
            return self._err(400, f"{limit_error} 无效")
        source_contract = self._scene_contract_source(scene_key)
        contract_v2 = assemble_unified_page_contract_v2(
            {"scene_contract_v1": source_contract},
            source_type="scene_contract_v1",
            client_type=client_type,
            request_id=str(params.get("request_id") or params.get("requestId") or f"ui.contract.v2.scene.{scene_key}"),
        )
        contract_v2 = trim_unified_page_contract_v2(
            contract_v2,
            client_type=client_type,
            delivery_profile=delivery_profile,
            **limit_params,
            include_source_compat=client_type not in MOBILE_CLIENT_TYPES,
        )
        return IntentExecutionResult(
            ok=True,
            data=contract_v2,
            meta={
                "intent": self.INTENT_TYPE,
                "version": self.VERSION,
                "contract_version": CONTRACT_VERSION,
                "client_type": client_type,
                "delivery_profile": delivery_profile,
                "source_type": "scene_contract_v1",
                "source_kind": self.SOURCE_KIND,
                "source_authorities": list(self.SOURCE_AUTHORITIES),
                "source_authority": self.source_authority_contract(),
            },
        )

    def _scene_contract_source(self, scene_key: str) -> dict[str, Any]:
        scene = {}
        try:
            payload = load_scenes_from_db_or_fallback(self.env, drift=None, logger=None) or {}
            for row in payload.get("scenes") or []:
                if not isinstance(row, dict):
                    continue
                key = str(row.get("code") or row.get("key") or "").strip()
                if key == scene_key:
                    scene = row
                    break
        except Exception:
            scene = {}
        target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
        title = str(scene.get("title") or scene.get("label") or scene.get("name") or scene_key).strip()
        blocks = scene.get("blocks") if isinstance(scene.get("blocks"), list) else []
        if not blocks:
            blocks = [{"key": scene_key, "title": title, "block_type": "scene_summary"}]
        actions = scene.get("actions") if isinstance(scene.get("actions"), dict) else {}
        if not actions:
            actions = {
                "primary_actions": [
                    {
                        "key": "open_scene",
                        "label": title,
                        "intent": "ui.contract",
                        "target": {"scene_key": scene_key},
                    }
                ]
            }
        return {
            "contract_version": "scene_contract_standard_v1",
            "identity": {
                "scene_key": scene_key,
                "title": title,
                "product_key": str(scene.get("product_key") or "").strip(),
                "capability": str(scene.get("capability") or scene.get("capability_key") or "").strip(),
            },
            "target": {
                "route": str(target.get("route") or f"/s/{scene_key}").strip(),
                "openable": True,
            },
            "state": {
                "status": "ready",
                "state_tone": "stable",
                "reason_code": "SCENE_CONTRACT_READY",
            },
            "page": {
                "layout": str(scene.get("layout") or scene.get("page_type") or "entry_shell").strip(),
                "blocks": blocks,
            },
            "actions": actions,
        }

    def _params(self, payload: Optional[Dict[str, Any]]) -> dict[str, Any]:
        if isinstance(payload, dict):
            nested = payload.get("params")
            if isinstance(nested, dict):
                merged = dict(payload)
                merged.update(nested)
                return merged
            return dict(payload)
        if isinstance(self.params, dict):
            return dict(self.params)
        return {}

    def _headers(self) -> dict[str, Any]:
        try:
            http_request = getattr(self.request, "httprequest", None)
            headers = getattr(http_request, "headers", None)
            if headers:
                return dict(headers)
        except Exception:
            _logger.debug("failed to read ui.contract.v2 request headers", exc_info=True)
        return {}

    def _trim_limit_params(self, params: dict[str, Any]) -> tuple[dict[str, Optional[int]], Optional[str]]:
        out: dict[str, Optional[int]] = {}
        for output_key, snake_key, camel_key in (
            ("max_widgets", "max_widgets", "maxWidgets"),
            ("max_actions", "max_actions", "maxActions"),
            ("max_containers", "max_containers", "maxContainers"),
        ):
            raw = params.get(snake_key) if snake_key in params else params.get(camel_key)
            value, error = parse_positive_int(raw, allow_empty=True)
            if error:
                return {}, snake_key
            out[output_key] = value
        return out, None

    def _ui_contract_params(self, params: dict[str, Any]) -> dict[str, Any]:
        ui_params = dict(params)
        ui_params.pop("source_type", None)
        ui_params.pop("sourceType", None)
        ui_params.pop("client_type", None)
        ui_params.pop("clientType", None)
        ui_params.setdefault("source_mode", "backend_internal")
        ui_params.setdefault("contract_surface", "user")
        if not ui_params.get("op") and not ui_params.get("subject"):
            if ui_params.get("menu_id") or ui_params.get("menuId") or ui_params.get("id"):
                ui_params["op"] = "menu"
            elif ui_params.get("action_id") or ui_params.get("actionId"):
                ui_params["op"] = "action_open"
            elif ui_params.get("model") or ui_params.get("model_code") or ui_params.get("modelCode"):
                ui_params["op"] = "model"
        return ui_params

    def _envelope(self, result: Any) -> dict[str, Any]:
        if isinstance(result, IntentExecutionResult):
            return result.to_legacy_dict()
        if isinstance(result, dict):
            return result
        return {"ok": True, "data": result or {}, "meta": {}}

    def _resolve_entry_contract(
        self,
        ui_data: dict[str, Any],
        ui_meta: dict[str, Any],
        ui_params: dict[str, Any],
        ctx: Optional[Dict[str, Any]],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        entry = ui_data.get("entry") if isinstance(ui_data.get("entry"), dict) else {}
        model = str(entry.get("model") or ui_data.get("model") or "").strip()
        view_type = str(
            entry.get("view_type")
            or entry.get("viewType")
            or ui_data.get("view_type")
            or ui_data.get("viewType")
            or ""
        ).strip()
        if not model:
            return ui_data, ui_meta

        next_params = dict(ui_params)
        next_params["op"] = "model"
        next_params["model"] = model
        next_params["view_type"] = view_type or "tree"
        if ui_data.get("menu_id") and not next_params.get("menu_id"):
            next_params["menu_id"] = ui_data.get("menu_id")
        action = ui_data.get("action") if isinstance(ui_data.get("action"), dict) else {}
        if action.get("id") and not next_params.get("action_id"):
            next_params["action_id"] = action.get("id")
        view_ids = ui_data.get("view_ids_by_type") if isinstance(ui_data.get("view_ids_by_type"), dict) else {}
        requested_view_id = view_ids.get(next_params["view_type"])
        if requested_view_id and not next_params.get("view_id"):
            next_params["view_id"] = requested_view_id

        resolved = UiContractHandler(
            self.env,
            su_env=self.su_env,
            request=self.request,
            context=ctx or self.context,
            payload=next_params,
        ).handle(next_params, ctx)
        envelope = self._envelope(resolved)
        if not envelope.get("ok", True):
            return ui_data, ui_meta
        resolved_data = envelope.get("data") or {}
        resolved_meta = envelope.get("meta") or {}
        if isinstance(resolved_data, dict) and resolved_data:
            merged_meta = dict(ui_meta)
            merged_meta.update(resolved_meta if isinstance(resolved_meta, dict) else {})
            merged_meta.setdefault("entry_subject", "menu")
            return resolved_data, merged_meta
        return ui_data, ui_meta

    def _err(self, code: int, message: str) -> IntentExecutionResult:
        return IntentExecutionResult(
            ok=False,
            error={"code": code, "message": message},
            meta={
                "intent": self.INTENT_TYPE,
                "version": self.VERSION,
                "contract_version": CONTRACT_VERSION,
                "source_authority": self.source_authority_contract(),
            },
            code=code,
        )
