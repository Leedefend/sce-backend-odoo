# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from copy import deepcopy
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
from ..utils.extension_hooks import call_extension_hook_first
from .ui_contract import UiContractHandler

_logger = logging.getLogger(__name__)

BUSINESS_OPERATION_FIELD_PRIORITY = (
    "name",
    "document_no",
    "legacy_document_no",
    "invoice_no",
    "invoice_code",
    "subject",
    "type",
    "source_kind",
    "direction",
    "project_id",
    "operation_strategy",
    "partner_id",
    "contract_id",
    "settlement_id",
    "payment_request_id",
    "date_request",
    "date_receipt",
    "document_date",
    "invoice_date",
    "date_contract",
    "amount",
    "amount_no_tax",
    "tax_amount",
    "amount_total",
    "visible_contract_amount",
    "settlement_amount",
    "settlement_amount_payable",
    "paid_amount",
    "unpaid_amount",
    "state",
    "document_status",
    "handler_id",
    "handler_name",
    "creator_name",
    "created_time",
    "note",
)
BUSINESS_OPERATION_TECHNICAL_PREFIXES = (
    "message_",
    "activity_",
    "website_",
    "rating_",
)
BUSINESS_OPERATION_TECHNICAL_FIELDS = {
    "id",
    "display_name",
    "create_uid",
    "create_date",
    "write_uid",
    "write_date",
    "__last_update",
}


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
            return self._handle_scene_contract(
                params,
                client_type=client_type,
                delivery_profile=delivery_profile,
            )
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

        source_contract = dict(ui_data) if isinstance(ui_data, dict) else {}
        nested_ui_contract = source_contract.pop("ui_contract", {})
        if isinstance(nested_ui_contract, dict):
            source_contract.update(nested_ui_contract)
        nested_data = ui_data.get("data") if isinstance(ui_data.get("data"), dict) else {}
        source_record = (
            ui_data.get("record")
            if isinstance(ui_data.get("record"), dict)
            else nested_data.get("record")
            if isinstance(nested_data.get("record"), dict)
            else {}
        )
        source_contract.update({
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
            "record": source_record,
            "source_meta": ui_meta,
        })
        self._inject_current_form_settings_action(
            source_contract,
            params=params,
            ui_params=ui_params,
            model=str(model or "").strip(),
            view_type=str(view_type or "").strip().lower(),
        )
        self._inject_business_operation_contract(
            source_contract,
            model=str(model or "").strip(),
            view_type=str(view_type or "").strip().lower(),
        )
        self._inject_collaboration_contract(
            source_contract,
            model=str(model or "").strip(),
            view_type=str(view_type or "").strip().lower(),
        )
        hydrated_record = self._hydrate_record_snapshot(
            model=str(model or "").strip(),
            record_id=params.get("record_id") or params.get("recordId") or ui_params.get("record_id") or ui_params.get("recordId"),
            source_contract=source_contract,
            current_record=source_record,
            view_type=str(view_type or "").strip().lower(),
        )
        if hydrated_record:
            source_contract["record"] = hydrated_record
        contract_v2 = assemble_unified_page_contract_v2(
            source_contract,
            source_type="ui.contract",
            client_type=client_type,
            request_id=str(request_id),
        )
        if isinstance(source_contract.get("delete_policy"), dict):
            contract_v2["delete_policy"] = dict(source_contract.get("delete_policy") or {})
        contract_v2 = trim_unified_page_contract_v2(
            contract_v2,
            client_type=client_type,
            delivery_profile=delivery_profile,
            **limit_params,
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

    def _inject_current_form_settings_action(
        self,
        source_contract: dict[str, Any],
        *,
        params: dict[str, Any],
        ui_params: dict[str, Any],
        model: str,
        view_type: str,
    ) -> None:
        if view_type != "form" or not model:
            return
        action_id = (
            params.get("action_id")
            or params.get("actionId")
            or ui_params.get("action_id")
            or ui_params.get("actionId")
            or source_contract.get("action_id")
            or source_contract.get("actionId")
        )
        view_id = (
            params.get("view_id")
            or params.get("viewId")
            or ui_params.get("view_id")
            or ui_params.get("viewId")
        )
        if not view_id:
            view_ids = source_contract.get("view_ids_by_type")
            if isinstance(view_ids, dict):
                view_id = view_ids.get("form")
        render_profile = (
            source_contract.get("render_profile")
            or params.get("render_profile")
            or params.get("renderProfile")
            or ui_params.get("render_profile")
            or ui_params.get("renderProfile")
            or "edit"
        )
        try:
            from ..app_config_engine.services.assemblers.page_assembler import PageAssembler

            assembler = PageAssembler(self.env, self.su_env)
            assembler._inject_current_form_settings_action(
                source_contract,
                model_name=model,
                action_id=action_id,
                view_id=view_id,
                render_profile=render_profile,
            )
        except Exception:
            _logger.debug("ui.contract.v2 current form settings action injection skipped", exc_info=True)

    def _inject_business_operation_contract(self, source_contract: dict[str, Any], *, model: str, view_type: str) -> None:
        if not model or model not in self.env:
            return
        try:
            model_obj = self.env[model]
            model_fields = getattr(model_obj, "_fields", {}) or {}
            if not model_fields:
                return
        except Exception:
            _logger.debug("ui.contract.v2 business operation projection skipped: model inspect failed", exc_info=True)
            return

        fields_contract = source_contract.get("fields") if isinstance(source_contract.get("fields"), dict) else {}
        descriptor_cache: dict[str, dict[str, Any]] = {}

        def descriptor(name: str) -> dict[str, Any]:
            if name in descriptor_cache:
                return descriptor_cache[name]
            current = fields_contract.get(name) if isinstance(fields_contract.get(name), dict) else {}
            if current:
                descriptor_cache[name] = dict(current)
                return descriptor_cache[name]
            try:
                fetched = self.env[model].fields_get([name]).get(name) or {}
            except Exception:
                fetched = {}
            descriptor_cache[name] = dict(fetched)
            if fetched:
                fields_contract[name] = dict(fetched)
                source_contract["fields"] = fields_contract
            return descriptor_cache[name]

        def has_field(name: str) -> bool:
            return bool(name and name in model_fields)

        def field_type(name: str) -> str:
            meta = descriptor(name)
            return str(meta.get("type") or getattr(model_fields.get(name), "type", "") or "").strip()

        def field_relation(name: str) -> str:
            meta = descriptor(name)
            return str(meta.get("relation") or getattr(model_fields.get(name), "comodel_name", "") or "").strip()

        def field_label(name: str) -> str:
            meta = descriptor(name)
            return str(meta.get("string") or getattr(model_fields.get(name), "string", "") or name).strip()

        def is_technical(name: str) -> bool:
            return (
                name in BUSINESS_OPERATION_TECHNICAL_FIELDS
                or any(name.startswith(prefix) for prefix in BUSINESS_OPERATION_TECHNICAL_PREFIXES)
            )

        def unique(items: list[str]) -> list[str]:
            out: list[str] = []
            seen: set[str] = set()
            for item in items:
                value = str(item or "").strip()
                if value and value not in seen and has_field(value):
                    seen.add(value)
                    out.append(value)
            return out

        note_field = next((name for name in ("note", "remark", "remarks", "description", "memo") if has_field(name)), "")
        attachment_field = next(
            (
                name
                for name in model_fields
                if (
                    name == "attachment_ids"
                    or (field_type(name) == "many2many" and field_relation(name) == "ir.attachment")
                )
            ),
            "",
        )
        detail_fields = unique([
            name
            for name in model_fields
            if field_type(name) == "one2many" and not is_technical(name)
        ])
        common_fields = unique([
            name
            for name in BUSINESS_OPERATION_FIELD_PRIORITY
            if has_field(name) and field_type(name) not in {"one2many", "many2many"}
        ])
        if note_field and note_field not in common_fields:
            common_fields.append(note_field)

        amount_fields = [
            name
            for name in common_fields
            if field_type(name) in {"float", "integer", "monetary"} or "amount" in name
        ]
        date_fields = [
            name
            for name in common_fields
            if field_type(name) in {"date", "datetime"} or name.startswith("date_") or name.endswith("_time")
        ]
        status_field = next((name for name in ("state", "document_status", "status", "lifecycle_state") if has_field(name)), "")

        profile = source_contract.get("business_operation_profile") if isinstance(source_contract.get("business_operation_profile"), dict) else {}
        profile.update({
            "source": "ui.contract.v2.business_operation_projection",
            "model": model,
            "view_type": view_type,
            "common_fields": common_fields,
            "amount_fields": amount_fields,
            "date_fields": date_fields,
            "status_field": status_field,
            "note_field": note_field,
            "attachment_field": attachment_field,
            "detail_fields": detail_fields,
            "field_labels": {name: field_label(name) for name in unique(common_fields + detail_fields + [attachment_field])},
            "capabilities": {
                "remarks": bool(note_field),
                "attachments": bool(attachment_field),
                "details": bool(detail_fields),
                "collaboration": any(has_field(name) for name in ("message_ids", "activity_ids")),
            },
        })
        source_contract["business_operation_profile"] = profile

        visible_fields = source_contract.get("visible_fields") if isinstance(source_contract.get("visible_fields"), list) else []
        source_contract["visible_fields"] = unique([str(item or "") for item in visible_fields] + common_fields + detail_fields + [attachment_field])

        field_groups = source_contract.get("field_groups") if isinstance(source_contract.get("field_groups"), list) else []
        normalized_groups = [dict(item) for item in field_groups if isinstance(item, dict)]
        existing_group_names = {str(item.get("name") or "").strip() for item in normalized_groups}

        def append_group(name: str, title: str, fields: list[str]) -> None:
            selected = unique(fields)
            if not selected or name in existing_group_names:
                return
            normalized_groups.append({"name": name, "title": title, "label": title, "fields": selected})
            existing_group_names.add(name)

        append_group("business_core", "基本信息", common_fields[:18])
        append_group("business_amount", "金额信息", amount_fields)
        append_group("business_details", "明细", detail_fields)
        append_group("business_collaboration", "备注与附件", [note_field, attachment_field])
        if normalized_groups:
            source_contract["field_groups"] = normalized_groups

        self._merge_business_list_profile(
            source_contract,
            common_fields=common_fields,
            note_field=note_field,
            status_field=status_field,
            label_for=field_label,
            type_for=field_type,
        )

        if view_type == "form":
            form = _ensure_source_form_contract(source_contract)
            if attachment_field:
                attachments = form.get("attachments") if isinstance(form.get("attachments"), dict) else {}
                attachments.update({
                    "enabled": True,
                    "field": attachment_field,
                    "label": attachments.get("label") or "附件",
                    "ui_labels": attachments.get("ui_labels") if isinstance(attachments.get("ui_labels"), dict) else {
                        "label": "附件",
                        "upload": "上传附件",
                        "uploading": "上传中...",
                        "download": "下载",
                        "upload_failed": "附件上传失败",
                        "download_failed": "附件下载失败",
                        "size_exceeded": "文件过大",
                    },
                })
                form["attachments"] = attachments

    def _merge_business_list_profile(
        self,
        source_contract: dict[str, Any],
        *,
        common_fields: list[str],
        note_field: str,
        status_field: str,
        label_for,
        type_for,
    ) -> None:
        views = source_contract.get("views") if isinstance(source_contract.get("views"), dict) else {}
        tree = views.get("tree") if isinstance(views.get("tree"), dict) else views.get("list") if isinstance(views.get("list"), dict) else {}
        raw_columns = tree.get("columns") if isinstance(tree.get("columns"), list) else []
        columns: list[str] = []
        for row in raw_columns:
            name = str(row.get("name") if isinstance(row, dict) else row or "").strip()
            if name and name not in columns:
                columns.append(name)
        profile = source_contract.get("list_profile") if isinstance(source_contract.get("list_profile"), dict) else {}
        for name in profile.get("columns") if isinstance(profile.get("columns"), list) else []:
            normalized = str(name or "").strip()
            if normalized and normalized not in columns:
                columns.append(normalized)
        for name in common_fields:
            if name and name not in columns:
                columns.append(name)
        if note_field and note_field not in columns:
            columns.append(note_field)
        if len(columns) > 18:
            selected = columns[:18]
            if note_field and note_field in columns and note_field not in selected:
                selected[-1] = note_field
            columns = selected
        if not columns:
            return

        labels = profile.get("column_labels") if isinstance(profile.get("column_labels"), dict) else {}
        labels = {**labels, **{name: label_for(name) for name in columns}}
        profile.update({
            "source": "ui.contract.v2.business_operation_projection",
            "columns": columns,
            "fact_columns": columns,
            "hidden_columns": [name for name in (profile.get("hidden_columns") if isinstance(profile.get("hidden_columns"), list) else []) if name in columns],
            "column_labels": labels,
            "row_primary": profile.get("row_primary") or ("name" if "name" in columns else columns[0]),
            "row_secondary": profile.get("row_secondary") or ("project_id" if "project_id" in columns else ""),
            "status_field": profile.get("status_field") or status_field,
            "preference_policy": {
                **(profile.get("preference_policy") if isinstance(profile.get("preference_policy"), dict) else {}),
                "scope": "ui_only",
                "allow_visibility": True,
                "allow_order": True,
                "allow_width": True,
                "must_request_columns": columns,
            },
        })
        source_contract["list_profile"] = profile

        if tree:
            schema_rows = tree.get("columns_schema") if isinstance(tree.get("columns_schema"), list) else []
            schema_by_name = {
                str(row.get("name") or "").strip(): dict(row)
                for row in schema_rows
                if isinstance(row, dict) and str(row.get("name") or "").strip()
            }
            tree["columns"] = columns
            tree["columns_schema"] = [
                {
                    **schema_by_name.get(name, {}),
                    "name": name,
                    "label": labels.get(name) or label_for(name),
                    "string": schema_by_name.get(name, {}).get("string") or label_for(name),
                    "type": schema_by_name.get(name, {}).get("type") or type_for(name) or "char",
                    "widget": schema_by_name.get(name, {}).get("widget") or type_for(name) or "char",
                }
                for name in columns
            ]
            if "tree" in views:
                views["tree"] = tree
            elif "list" in views:
                views["list"] = tree
            source_contract["views"] = views

    def _inject_collaboration_contract(self, source_contract: dict[str, Any], *, model: str, view_type: str) -> None:
        if view_type != "form" or not model or model not in self.env:
            return
        try:
            model_obj = self.env[model]
            if getattr(model_obj, "_transient", False):
                return
            model_fields = getattr(model_obj, "_fields", {}) or {}
        except Exception:
            _logger.debug("ui.contract.v2 collaboration injection skipped: model inspect failed", exc_info=True)
            return

        form = _ensure_source_form_contract(source_contract)
        chatter = form.get("chatter") if isinstance(form.get("chatter"), dict) else {}
        attachments = form.get("attachments") if isinstance(form.get("attachments"), dict) else {}
        upload_allowed = model in _allowed_models_from_hook(self.env, "smart_core_file_upload_allowed_models")
        download_allowed = model in _allowed_models_from_hook(self.env, "smart_core_file_download_allowed_models")
        chatter_fields = [
            field_name
            for field_name in ("message_follower_ids", "activity_ids", "message_ids", "website_message_ids")
            if field_name in model_fields
        ]
        message_capable = "message_ids" in model_fields or hasattr(model_obj, "message_post")
        activity_capable = "activity_ids" in model_fields
        chatter_enabled = bool(chatter.get("enabled") or message_capable or activity_capable)
        attachment_enabled = bool(attachments.get("enabled") or upload_allowed or download_allowed)
        if not chatter_enabled and not attachment_enabled:
            return

        collaboration = source_contract.get("collaboration") if isinstance(source_contract.get("collaboration"), dict) else {}
        if chatter_enabled:
            chatter = {
                **chatter,
                "enabled": True,
                "label": chatter.get("label") or "协作日志",
                "fields": chatter.get("fields") if isinstance(chatter.get("fields"), list) else chatter_fields,
                "features": chatter.get("features") if isinstance(chatter.get("features"), dict) else {
                    "message": bool(message_capable),
                    "note": bool(message_capable),
                    "activity": bool(activity_capable),
                },
                "actions": chatter.get("actions") if isinstance(chatter.get("actions"), list) else _standard_chatter_actions(
                    message_capable=bool(message_capable),
                    activity_capable=bool(activity_capable),
                ),
            }
            form["chatter"] = chatter
            collaboration["chatter"] = deepcopy(chatter)
        if attachment_enabled:
            upload_contract = attachments.get("upload") if isinstance(attachments.get("upload"), dict) else {}
            download_contract = attachments.get("download") if isinstance(attachments.get("download"), dict) else {}
            attachments = {
                **attachments,
                "enabled": True,
                "label": attachments.get("label") or "附件",
                "upload": {
                    "intent": "file.upload",
                    "max_bytes": 5 * 1024 * 1024,
                    "accepted_types": [],
                    "enabled": bool(upload_allowed),
                },
                "download": {
                    "intent": "file.download",
                    "enabled": bool(download_allowed),
                },
                "ui_labels": attachments.get("ui_labels") if isinstance(attachments.get("ui_labels"), dict) else {
                    "label": "附件",
                    "upload": "上传附件",
                    "uploading": "上传中...",
                    "download": "下载",
                    "upload_failed": "附件上传失败",
                    "download_failed": "附件下载失败",
                    "size_exceeded": "文件过大",
                },
            }
            attachments["upload"].update(upload_contract)
            attachments["upload"]["enabled"] = bool(upload_allowed)
            attachments["download"].update(download_contract)
            attachments["download"]["enabled"] = bool(download_allowed)
            form["attachments"] = attachments
            collaboration["attachments"] = deepcopy(attachments)
        collaboration["timeline"] = {
            "enabled": True,
            "intent": "chatter.timeline",
            "include_audit": True,
        }
        collaboration["sourceAuthority"] = {
            "kind": "ui_contract_v2_collaboration_projection",
            "authorities": ["mail.thread", "mail.activity", "ir.attachment", "ir.rule", "extension_hook"],
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": True,
            "runtime_carrier": "ui.contract.v2.collaboration",
        }
        source_contract["collaboration"] = collaboration

    def _hydrate_record_snapshot(
        self,
        *,
        model: str,
        record_id: Any,
        source_contract: dict[str, Any],
        current_record: dict[str, Any],
        view_type: str,
    ) -> dict[str, Any]:
        if view_type != "form" or not model:
            return dict(current_record or {}) if isinstance(current_record, dict) else {}
        record_id_int, _record_id_error = parse_positive_int(record_id, allow_empty=True)
        record_id_int = int(record_id_int or 0)
        if record_id_int <= 0:
            return dict(current_record or {}) if isinstance(current_record, dict) else {}
        field_map = source_contract.get("fields") if isinstance(source_contract.get("fields"), dict) else {}
        field_names = [str(name).strip() for name in field_map.keys() if str(name).strip()]
        if "id" not in field_names:
            field_names.insert(0, "id")
        if not field_names:
            return dict(current_record or {}) if isinstance(current_record, dict) else {}
        merged = deepcopy(current_record) if isinstance(current_record, dict) else {}
        try:
            record = self.env[model].browse(record_id_int).exists()
            if not record:
                return merged
            rows = record.read(field_names)
            if rows and isinstance(rows[0], dict):
                merged.update(rows[0])
        except Exception:
            _logger.debug("ui.contract.v2 bulk record hydration skipped; falling back to per-field read", exc_info=True)
            try:
                record = self.env[model].browse(record_id_int).exists()
            except Exception:
                record = None
            if record:
                for name in field_names:
                    try:
                        rows = record.read([name])
                        if rows and isinstance(rows[0], dict) and name in rows[0]:
                            merged[name] = rows[0].get(name)
                    except Exception:
                        _logger.debug("ui.contract.v2 field hydration skipped: %s.%s", model, name, exc_info=True)
        return merged

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
        op = str(ui_params.get("op") or ui_params.get("subject") or "").strip().lower()
        view_type = str(ui_params.get("view_type") or ui_params.get("viewType") or "").strip().lower()
        record_id = ui_params.get("record_id") or ui_params.get("recordId") or ui_params.get("res_id") or ui_params.get("resId")
        if op == "model" and view_type in {"form", ""} and record_id and "with_data" not in ui_params:
            ui_params["with_data"] = True
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


def _ensure_source_form_contract(source_contract: dict[str, Any]) -> dict[str, Any]:
    views = source_contract.get("views")
    if not isinstance(views, dict):
        views = {}
        source_contract["views"] = views
    form = views.get("form")
    if not isinstance(form, dict):
        form = {}
        views["form"] = form
    return form


def _allowed_models_from_hook(env, hook_name: str) -> set[str]:
    try:
        payload = call_extension_hook_first(env, hook_name, env)
    except Exception:
        payload = None
    if not isinstance(payload, (list, tuple, set)):
        return set()
    return {str(item).strip() for item in payload if str(item).strip()}


def _standard_chatter_actions(*, message_capable: bool, activity_capable: bool) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if message_capable:
        actions.extend([
            {
                "key": "chatter_send_message",
                "label": "发送消息",
                "kind": "chatter",
                "level": "chatter",
                "selection": "none",
                "intent": "message",
                "payload": {"mode": "message"},
            },
            {
                "key": "chatter_log_note",
                "label": "记录备注",
                "kind": "chatter",
                "level": "chatter",
                "selection": "none",
                "intent": "note",
                "payload": {"mode": "note"},
            },
        ])
    if activity_capable:
        actions.append({
            "key": "chatter_schedule_activity",
            "label": "活动",
            "kind": "chatter",
            "level": "chatter",
            "selection": "none",
            "intent": "activity",
            "payload": {
                "mode": "activity",
                "execute_intent": "chatter.activity.schedule",
                "activity_type_xmlid": "mail.mail_activity_data_todo",
                "fields": [
                    {"name": "summary", "label": "摘要", "type": "char", "required": True},
                    {"name": "date_deadline", "label": "截止日期", "type": "date", "required": False},
                    {"name": "note", "label": "备注", "type": "text", "required": False},
                ],
            },
        })
    return actions
