# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import hashlib
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
BUSINESS_FORM_STRUCTURE_ALLOWED_LEGACY_FIELDS = {
    "legacy_document_no",
    "legacy_contract_no",
    "legacy_status",
}
BUSINESS_FORM_STRUCTURE_HISTORY_LABEL_TOKENS = (
    "历史",
    "旧系统",
    "旧库",
    "来源",
    "导入",
    "原始",
)
BUSINESS_FORM_STRUCTURE_HISTORY_NAME_PREFIXES = (
    "legacy_source_",
)
BUSINESS_FORM_STRUCTURE_HISTORY_NAME_TOKENS = (
    "_record_id",
    "_source_",
    "_batch",
    "_deleted",
    "_attachment_ref",
    "_pid",
    "_parent_id",
)
BUSINESS_FORM_STRUCTURE_HISTORY_NAME_SUFFIXES = (
    "_id",
    "_sort",
)
BUSINESS_FORM_STRUCTURE_INTERNAL_FIELDS = {
    "active",
    "archived",
    "color",
    "can_review",
    "entry_data",
    "has_comment",
    "has_message",
    "hide_reviews",
    "is_favorite",
    "is_locked",
    "my_activity_date_deadline",
    "name_short",
    "need_validation",
    "next_review",
    "sequence",
    "source_origin",
    "task_properties",
    "reject_reason",
    "rejected",
    "rejected_message",
    "review_ids",
    "reviewer_ids",
    "to_validate_message",
    "validated",
    "validated_message",
    "validation_status",
}
BUSINESS_FORM_STRUCTURE_INTERNAL_PREFIXES = (
    "access_",
    "alias_",
    "allow_",
    "dashboard_",
    "favorite_",
    "last_update_",
    "privacy_",
)
BUSINESS_FORM_STRUCTURE_INTERNAL_TOKENS = (
    "_delta",
    "_source",
    "_source_",
    "_visible",
    "legacy_deleted",
    "legacy_",
    "source_created",
    "validation",
)
BUSINESS_FORM_STRUCTURE_INTERNAL_SUFFIXES = (
    "_count",
    "_rate",
)
SCBS55_SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"


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
        projection_context = dict(getattr(self.env, "context", {}) or {})
        projection_context["contract_projection_readonly"] = True
        try:
            from odoo import api
            projection_env = api.Environment(self.env.cr, self.env.uid, projection_context)
            projection_su_env = api.Environment(self.su_env.cr, self.su_env.uid, projection_context)
        except Exception:
            projection_env = self.env
            projection_su_env = self.su_env
        source_result = UiContractHandler(
            projection_env,
            su_env=projection_su_env,
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
        try:
            has_model = bool(model and model in self.env)
        except Exception:
            return
        if not has_model:
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

        form_structure_governed_field_names: set[str] = set()

        def is_form_structure_internal(name: str) -> bool:
            if not name or name in BUSINESS_FORM_STRUCTURE_ALLOWED_LEGACY_FIELDS:
                return False
            if name in form_structure_governed_field_names:
                return False
            return (
                is_technical(name)
                or name in BUSINESS_FORM_STRUCTURE_INTERNAL_FIELDS
                or any(name.startswith(prefix) for prefix in BUSINESS_FORM_STRUCTURE_INTERNAL_PREFIXES)
                or any(token in name for token in BUSINESS_FORM_STRUCTURE_INTERNAL_TOKENS)
                or any(name.endswith(suffix) for suffix in BUSINESS_FORM_STRUCTURE_INTERNAL_SUFFIXES)
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

        def field_names_from_layout(rows: Any) -> list[str]:
            out: list[str] = []

            def visit(node: Any) -> None:
                if isinstance(node, list):
                    for child in node:
                        visit(child)
                    return
                if not isinstance(node, dict):
                    return
                node_type = str(node.get("type") or node.get("kind") or "").strip().lower()
                node_name = str(node.get("name") or node.get("field") or "").strip()
                if node_type == "field" and node_name:
                    out.append(node_name)
                for key in ("children", "tabs", "pages", "groups", "fields", "widgetList"):
                    visit(node.get(key))

            visit(rows)
            return out

        def section_titles_from_layout(rows: Any) -> list[str]:
            out: list[str] = []
            seen: set[str] = set()

            def add(raw: Any) -> None:
                title = str(raw or "").strip()
                if title and title not in seen:
                    seen.add(title)
                    out.append(title)

            def visit(node: Any) -> None:
                if isinstance(node, list):
                    for child in node:
                        visit(child)
                    return
                if not isinstance(node, dict):
                    return
                node_type = str(node.get("type") or node.get("kind") or "").strip().lower()
                if node_type != "field":
                    add(node.get("title") or node.get("string") or node.get("label"))
                for key in ("children", "tabs", "pages", "groups", "fields", "widgetList"):
                    visit(node.get(key))

            visit(rows)
            return out

        def source_form_field_candidates() -> list[str]:
            governed_field_names = form_structure_governance.get("field_names")
            if isinstance(governed_field_names, list) and governed_field_names:
                return unique([str(item or "").strip() for item in governed_field_names])
            field_groups = source_contract.get("field_groups") if isinstance(source_contract.get("field_groups"), list) else []
            group_fields: list[str] = []
            for group in field_groups:
                if isinstance(group, dict) and isinstance(group.get("fields"), list):
                    group_fields.extend(str(item or "").strip() for item in group.get("fields") or [])
            views = source_contract.get("views") if isinstance(source_contract.get("views"), dict) else {}
            form_view = views.get("form") if isinstance(views.get("form"), dict) else {}
            layout_fields = field_names_from_layout(form_view.get("layout"))
            explicit_fields = source_contract.get("visible_fields") if isinstance(source_contract.get("visible_fields"), list) else []
            governed_fields = layout_fields + group_fields
            if governed_fields:
                return unique(governed_fields)
            return unique([str(item or "").strip() for item in explicit_fields])

        form_structure_governance = self._form_structure_governance(
            source_contract,
            model=model,
            view_type=view_type,
        )
        form_structure_governed_field_names.update(
            str(item or "").strip()
            for item in (form_structure_governance.get("field_names") or [])
            if str(item or "").strip()
        )
        form_field_candidates = source_form_field_candidates() if form_structure_governance else []
        source_section_titles: list[str] = []
        if form_structure_governance:
            views = source_contract.get("views") if isinstance(source_contract.get("views"), dict) else {}
            form_view = views.get("form") if isinstance(views.get("form"), dict) else {}
            source_section_titles = section_titles_from_layout(form_view.get("layout"))
            for title in form_structure_governance.get("section_titles") or []:
                value = str(title or "").strip()
                if value and value not in source_section_titles:
                    source_section_titles.append(value)
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
        priority_fields = unique([
            name
            for name in BUSINESS_OPERATION_FIELD_PRIORITY
            if has_field(name) and field_type(name) not in {"one2many", "many2many"}
        ])
        source_common_fields = (
            [
                name
                for name in form_field_candidates
                if not is_form_structure_internal(name) and field_type(name) not in {"one2many", "many2many"}
            ]
            if view_type == "form"
            else []
        )
        source_detail_fields = (
            [
                name
                for name in form_field_candidates
                if not is_form_structure_internal(name) and field_type(name) in {"one2many", "many2many"}
            ]
            if view_type == "form"
            else []
        )
        common_fields = unique(priority_fields + source_common_fields)
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
            "form_structure_common_fields": source_common_fields,
            "form_structure_detail_fields": source_detail_fields,
            "field_labels": {name: field_label(name) for name in unique(common_fields + detail_fields + [attachment_field])},
            "capabilities": {
                "remarks": bool(note_field),
                "attachments": bool(attachment_field),
                "details": bool(detail_fields),
                "collaboration": any(has_field(name) for name in ("message_ids", "activity_ids")),
            },
        })
        if form_structure_governance:
            profile["form_structure_governance"] = form_structure_governance
            profile["source_section_titles"] = source_section_titles
        source_contract["business_operation_profile"] = profile

        if view_type in {"tree", "list"}:
            self._merge_business_list_profile(
                source_contract,
                common_fields=common_fields,
                amount_fields=amount_fields,
                note_field=note_field,
                status_field=status_field,
                label_for=field_label,
                type_for=field_type,
            )

        if form_structure_governance:
            source_contract["form_structure_contract"] = self._build_form_structure_contract(
                model=model,
                profile=profile,
                field_type=field_type,
                unique=unique,
                governance=form_structure_governance,
            )
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

    def _form_structure_governance(self, source_contract: dict[str, Any], *, model: str, view_type: str) -> dict[str, Any]:
        if view_type != "form":
            return {}
        governance = source_contract.get("governance") if isinstance(source_contract.get("governance"), dict) else {}
        view_governance = governance.get("view_orchestration") if isinstance(governance.get("view_orchestration"), dict) else {}
        source_trace = source_contract.get("source_trace") if isinstance(source_contract.get("source_trace"), dict) else {}
        view_trace = source_trace.get("view_orchestration") if isinstance(source_trace.get("view_orchestration"), dict) else {}
        business_contracts = view_trace.get("business_config_contracts")
        if not isinstance(business_contracts, list):
            business_contracts = view_governance.get("business_config_contracts")
        if not isinstance(business_contracts, list):
            business_contracts = []
        legacy_overlay = bool(view_trace.get("legacy_field_policy_overlay") or view_governance.get("legacy_field_policy_overlay"))
        field_names: list[str] = []
        section_titles: list[str] = []
        config_summaries: list[dict[str, Any]] = []
        try:
            view_ids = source_contract.get("view_ids_by_type") if isinstance(source_contract.get("view_ids_by_type"), dict) else {}
            configs = self.env["ui.business.config.contract"]._effective_view_orchestration_contracts(
                model,
                view_type="form",
                action_id=source_contract.get("action_id") or source_contract.get("actionId"),
                view_id=view_ids.get("form"),
            )
        except Exception:
            configs = []
        hidden_field_names: set[str] = set()
        for config in configs:
            config_summaries.append({
                "id": int(config.id or 0),
                "name": str(config.name or ""),
                "priority": int(config.priority or 0),
                "view_type": str(config.view_type or ""),
            })
            payload = config.contract_json if isinstance(config.contract_json, dict) else {}
            orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
            views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
            form_spec = views.get("form") if isinstance(views.get("form"), dict) else {}
            rows = form_spec.get("fields") if isinstance(form_spec.get("fields"), list) else []
            for row in rows:
                if isinstance(row, dict):
                    name = str(row.get("name") or row.get("field") or row.get("field_name") or "").strip()
                    if not name:
                        continue
                    if row.get("visible") is False:
                        hidden_field_names.add(name)
                        field_names = [item for item in field_names if item != name]
                        continue
                else:
                    name = str(row or "").strip()
                if name and name in hidden_field_names:
                    hidden_field_names.remove(name)
                if name and name not in field_names:
                    field_names.append(name)
            sections = form_spec.get("sections") if isinstance(form_spec.get("sections"), list) else []
            for row in sections:
                if isinstance(row, dict):
                    title = str(row.get("title") or row.get("label") or row.get("name") or "").strip()
                else:
                    title = str(row or "").strip()
                if title and title not in section_titles:
                    section_titles.append(title)
        applied = bool(view_governance.get("applied") or business_contracts or legacy_overlay or field_names)
        if not applied:
            return {}
        return {
            "source": "business_view_orchestration",
            "owner_layer": str(view_trace.get("owner_layer") or view_governance.get("owner_layer") or "business_view_orchestration"),
            "business_config_contracts": [dict(item) for item in business_contracts if isinstance(item, dict)] or config_summaries,
            "legacy_field_policy_overlay": legacy_overlay,
            "field_names": field_names,
            "section_titles": section_titles,
        }

    def _build_form_structure_contract(
        self,
        *,
        model: str,
        profile: dict[str, Any],
        field_type,
        unique,
        governance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        common_source = (
            profile.get("form_structure_common_fields")
            if "form_structure_common_fields" in profile
            else profile.get("common_fields")
        )
        detail_source = (
            profile.get("form_structure_detail_fields")
            if "form_structure_detail_fields" in profile
            else profile.get("detail_fields")
        )
        common_fields = [
            str(item or "").strip()
            for item in (common_source or [])
        ]
        amount_fields = [str(item or "").strip() for item in profile.get("amount_fields") or []]
        date_fields = [str(item or "").strip() for item in profile.get("date_fields") or []]
        detail_fields = [
            str(item or "").strip()
            for item in (detail_source or [])
        ]
        status_field = str(profile.get("status_field") or "").strip()
        note_field = str(profile.get("note_field") or "").strip()
        attachment_field = str(profile.get("attachment_field") or "").strip()
        source_section_titles = [
            str(item or "").strip()
            for item in (profile.get("source_section_titles") or [])
            if str(item or "").strip()
        ]
        allowed_fields = {
            name
            for name in common_fields + detail_fields
            if name
        }
        if attachment_field:
            detail_fields = [name for name in detail_fields if name != attachment_field]

        def fields_for(items: list[str]) -> list[str]:
            selected = unique(items)
            if not allowed_fields:
                return []
            return [name for name in selected if name in allowed_fields]

        slot_assigned_fields: set[str] = set()

        def claim_slot_fields(items: list[str]) -> list[str]:
            out: list[str] = []
            for name in fields_for(items):
                if name in slot_assigned_fields:
                    continue
                slot_assigned_fields.add(name)
                out.append(name)
            return out

        def first_existing(items: list[str]) -> list[str]:
            return fields_for(items)[:1]

        field_labels = profile.get("field_labels") if isinstance(profile.get("field_labels"), dict) else {}

        def field_display_label(name: str) -> str:
            label = str(field_labels.get(name) or "").strip()
            if label:
                return label
            try:
                return str(field_label(name) or "").strip()
            except Exception:
                return str(name or "").strip()

        def is_migration_history_field(name: str) -> bool:
            value = str(name or "").strip()
            label = field_display_label(value)
            if any(token in label for token in BUSINESS_FORM_STRUCTURE_HISTORY_LABEL_TOKENS):
                return True
            return (
                value.startswith(BUSINESS_FORM_STRUCTURE_HISTORY_NAME_PREFIXES)
                or any(token in value for token in BUSINESS_FORM_STRUCTURE_HISTORY_NAME_TOKENS)
                or any(value.endswith(suffix) for suffix in BUSINESS_FORM_STRUCTURE_HISTORY_NAME_SUFFIXES)
            )

        def is_history_check_field(name: str) -> bool:
            value = str(name or "").strip()
            if value.startswith("p1_visible_"):
                return True
            if value.startswith("legacy_") or "_legacy_" in value or value.endswith("_legacy"):
                return is_migration_history_field(value)
            return False

        history_check_fields = [
            name
            for name in fields_for(common_fields)
            if is_history_check_field(name)
        ]
        business_common_fields = [
            name
            for name in common_fields
            if name not in set(history_check_fields)
        ]

        identity_fields = claim_slot_fields([
            "name", "document_no", "invoice_no", "invoice_code",
            "subject", "type", "source_kind", "direction", "category_id", "contract_type_id",
        ])
        source_fields_candidates = fields_for([
            "entry_user_id", "entry_user_text", "entry_time", "handler_name",
            "creator_name", "created_time", "archived",
        ])
        relation_candidates = fields_for([
            "project_id", "partner_id", "contract_id", "settlement_id", "payment_request_id",
            "operation_strategy", "handler_id", "company_id", "budget_id", "analytic_id",
        ] + [
            name
            for name in business_common_fields
            if field_type(name) == "many2one"
        ])
        relation_fields = claim_slot_fields([
            name
            for name in relation_candidates
            if name not in identity_fields and name not in source_fields_candidates
        ])
        term_fields = claim_slot_fields([
            "date_start", "date_end", "engineering_category_text", "engineering_address",
            "engineering_content", "affiliated_person", "contract_duration_text",
            "contract_payment_method_text",
        ])
        attachment_fields = fields_for(["attachment_text", attachment_field])
        amount_fields = claim_slot_fields([name for name in amount_fields if name in business_common_fields])
        status_fields = claim_slot_fields([
            name
            for name in fields_for([status_field, "document_status"] + date_fields)
            if name not in source_fields_candidates and name in business_common_fields
        ])
        collaboration_fields = claim_slot_fields([
            name
            for name in ["approval_info", note_field] + attachment_fields
            if name in business_common_fields or name in attachment_fields
        ])
        detail_fields = claim_slot_fields(detail_fields)
        source_fields = claim_slot_fields(source_fields_candidates)
        history_check_fields = claim_slot_fields(history_check_fields)
        field_roles: dict[str, dict[str, Any]] = {}

        def labels_for(items: list[str]) -> dict[str, str]:
            return {
                name: str(field_labels.get(name) or name).strip()
                for name in fields_for(items)
            }

        def assign_role(fields: list[str], *, role: str, slot: str, group: str) -> None:
            for name in fields_for(fields):
                if name not in field_roles:
                    field_roles[name] = {"role": role, "slot": slot, "group": group}

        assigned = set(
            identity_fields
            + relation_fields
            + term_fields
            + amount_fields
            + status_fields
            + collaboration_fields
            + source_fields
            + detail_fields
            + history_check_fields
        )
        other_fact_fields = fields_for([
            name
            for name in business_common_fields
            if name not in assigned and field_type(name) not in {"one2many", "many2many"}
        ])
        assign_role(identity_fields, role="identity", slot="primary_facts", group="identity")
        assign_role(relation_fields, role="relation", slot="primary_facts", group="relations")
        assign_role(term_fields, role="term", slot="primary_facts", group="terms")
        assign_role(other_fact_fields, role="fact", slot="primary_facts", group="other_facts")
        assign_role(amount_fields, role="amount", slot="amount_progress", group="amounts")
        assign_role(status_fields, role="status_or_date", slot="amount_progress", group="status_dates")
        assign_role(collaboration_fields, role="collaboration", slot="collaboration", group="approval_remarks")
        assign_role(detail_fields, role="detail", slot="details_source", group="details")
        assign_role(source_fields, role="provenance", slot="details_source", group="provenance")
        assign_role(history_check_fields, role="history_check", slot="details_source", group="history_check")

        summary_fields = fields_for(
            [status_field]
            + first_existing(["subject", "name", "document_no", "legacy_document_no", "invoice_no"])
            + first_existing(["project_id", "partner_id", "contract_id", "settlement_id"])
            + first_existing(["date_contract", "document_date", "invoice_date", "date_request", "date_receipt"])
            + first_existing([
                "visible_contract_amount", "amount_total", "amount", "settlement_amount",
                "invoice_amount", "received_amount", "paid_amount",
            ])
            + attachment_fields
        )
        if summary_fields and all(is_history_check_field(name) for name in summary_fields):
            summary_fields = []

        def group(name: str, title: str, fields: list[str], *, role: str = "") -> dict[str, Any]:
            group_fields = fields_for(fields)
            effective_title = title
            if name == "details" and len(group_fields) == 1:
                label = str(field_labels.get(group_fields[0]) or "").strip()
                if label and label not in {"明细", "行", "Lines"}:
                    effective_title = label
            return {
                "name": name,
                "title": effective_title,
                "role": role or name,
                "fieldRefs": group_fields,
                "fieldLabels": labels_for(group_fields),
            }

        def slot(name: str, title: str, groups: list[dict[str, Any]], *, role: str = "") -> dict[str, Any]:
            return {
                "slot": name,
                "title": title,
                "role": role or name,
                "groups": [item for item in groups if item.get("fieldRefs")],
            }

        slots = [
            {
                "slot": "overview",
                "title": "办理总览",
                "role": "overview",
                "readonly": True,
                "fieldRefs": summary_fields or fields_for(business_common_fields[:6]),
            },
            slot("primary_facts", "主业务事实", [
                group("identity", "业务识别", identity_fields, role="identity"),
                group("relations", "业务关系", relation_fields, role="relations"),
                group("terms", "业务约定", term_fields, role="terms"),
                group("other_facts", "其他事实", other_fact_fields, role="facts"),
            ], role="facts"),
            slot("amount_progress", "金额与进度", [
                group("amounts", "金额信息", amount_fields, role="amounts"),
                group("status_dates", "状态与日期", status_fields, role="status_dates"),
            ], role="progress"),
            slot("collaboration", "办理协作", [
                group("approval_remarks", "审批与备注", collaboration_fields, role="collaboration"),
            ], role="collaboration"),
            slot("details_source", "明细与来源", [
                group("details", "业务明细", detail_fields, role="details"),
                group("provenance", "录入与归档", source_fields, role="provenance"),
                group("history_check", "历史核对信息", history_check_fields, role="history_check"),
            ], role="provenance"),
        ]
        slots = [
            item
            for item in slots
            if item.get("fieldRefs") or item.get("groups")
        ]

        return {
            "source": "ui.contract.v2.form_structure_contract",
            "structureVersion": "1.0",
            "model": model,
            "viewType": "form",
            "mode": "business_task_form",
            "layoutPolicy": "overview_then_task_slots",
            "objectProfile": {
                "model": model,
                "kind": "business_form",
                "factAuthority": "business_object_model_and_view",
            },
            "navigation": {"title": "业务办理"},
            "sourceSectionTitles": source_section_titles,
            "slots": slots,
            "fieldRoles": field_roles,
            "sourceAuthority": {
                "kind": self.SOURCE_KIND,
                "runtime_carrier": "ui.contract.v2.form_structure_contract",
                "projection_only": True,
                "no_business_fact_authority": True,
                "governed_form_structure": True,
                "governance_source": dict(governance or {}),
            },
        }

    def _merge_business_list_profile(
        self,
        source_contract: dict[str, Any],
        *,
        common_fields: list[str],
        amount_fields: list[str],
        note_field: str,
        status_field: str,
        label_for,
        type_for,
    ) -> None:
        views = source_contract.get("views") if isinstance(source_contract.get("views"), dict) else {}
        tree = views.get("tree") if isinstance(views.get("tree"), dict) else views.get("list") if isinstance(views.get("list"), dict) else {}
        raw_columns = tree.get("columns") if isinstance(tree.get("columns"), list) else []
        legacy_override = self._scbs55_legacy_visible_list_override(source_contract)
        columns: list[str] = []
        has_explicit_view_columns = False
        for row in raw_columns:
            name = str(row.get("name") if isinstance(row, dict) else row or "").strip()
            if name and name not in columns:
                columns.append(name)
                has_explicit_view_columns = True
        profile = source_contract.get("list_profile") if isinstance(source_contract.get("list_profile"), dict) else {}
        for name in profile.get("columns") if isinstance(profile.get("columns"), list) else []:
            normalized = str(name or "").strip()
            if normalized and normalized not in columns:
                columns.append(normalized)
        column_policy = profile.get("column_policy") if isinstance(profile.get("column_policy"), dict) else {}
        column_policy_mode = str(column_policy.get("mode") or "").strip().lower()
        strict_columns = column_policy_mode == "strict" or (has_explicit_view_columns and column_policy_mode != "extend")
        override_labels = {}
        if legacy_override:
            columns = list(legacy_override.get("columns") or [])
            override_labels = dict(legacy_override.get("column_labels") or {})
            strict_columns = True
        if not strict_columns and columns and all(str(name or "").startswith("p1_visible_") for name in columns):
            # SCBS55 legacy-visible delivery actions use action-scoped alias
            # columns to mirror the old system. Keep that list exact: appending
            # business-operation fallback fields reintroduces user-hidden
            # migration columns and can truncate long old-system lists.
            strict_columns = True
        if not strict_columns:
            for name in common_fields:
                if name and name not in columns:
                    columns.append(name)
            if note_field and note_field not in columns:
                columns.append(note_field)
        max_visible_columns = 24
        if not strict_columns and len(columns) > max_visible_columns:
            selected = columns[:max_visible_columns]
            list_visibility_fields = [
                "operation_strategy",
                "entry_user_text",
                "entry_time",
                "contract_duration_text",
                "contract_payment_method_text",
                "attachment_text",
            ]
            protected = [
                name
                for name in amount_fields + [note_field] + list_visibility_fields
                if name and name in columns and name not in selected
            ]
            protected_names = set(amount_fields + [note_field] + list_visibility_fields)
            for name in protected:
                replace_index = len(selected) - 1
                while replace_index >= 0 and selected[replace_index] in protected_names:
                    replace_index -= 1
                if replace_index < 0:
                    break
                selected[replace_index] = name
                protected_names.add(name)
            columns = selected
        if not columns:
            return

        labels = profile.get("column_labels") if isinstance(profile.get("column_labels"), dict) else {}
        labels = {**labels, **{name: label_for(name) for name in columns}, **override_labels}
        deduped_columns: list[str] = []
        preserve_duplicate_labels = bool(columns) and all(str(name or "").startswith("legacy_visible_") for name in columns)
        seen_keys: set[str] = set()
        for name in columns:
            label = str(labels.get(name) or label_for(name) or name).strip()
            dedupe_key = name if preserve_duplicate_labels else (label or name)
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            deduped_columns.append(name)
        columns = deduped_columns
        labels = {name: labels.get(name) or label_for(name) for name in columns}
        derived_status_field = str(profile.get("status_field") or status_field or "").strip()
        if not derived_status_field:
            derived_status_field = next(
                (
                    name
                    for name in columns
                    if str(labels.get(name) or label_for(name) or name).strip()
                    in {"状态", "单据状态", "开票状态", "付款状态", "结算状态", "支付申请状态", "账户状态"}
                ),
                "",
            )
        default_primary = "name" if "name" in columns else next((name for name in columns if name != derived_status_field), columns[0])
        row_primary = str(profile.get("row_primary") or default_primary or "").strip()
        row_secondary = str(profile.get("row_secondary") or "").strip()
        if not row_secondary and row_primary != derived_status_field and "project_id" in columns:
            row_secondary = "project_id"
        profile.update({
            "source": "ui.contract.v2.scbs55_legacy_visible_projection" if legacy_override else "ui.contract.v2.business_operation_projection",
            "columns": columns,
            "fact_columns": columns,
            "hidden_columns": [name for name in (profile.get("hidden_columns") if isinstance(profile.get("hidden_columns"), list) else []) if name in columns],
            "column_labels": labels,
            "show_row_number": False if legacy_override else profile.get("show_row_number", True),
            "row_primary": row_primary,
            "row_secondary": row_secondary,
            "status_field": derived_status_field,
            "preference_policy": {
                **(profile.get("preference_policy") if isinstance(profile.get("preference_policy"), dict) else {}),
                "scope": "ui_only",
                "allow_visibility": False if legacy_override else True,
                "allow_order": False if legacy_override else True,
                "allow_width": False if legacy_override else True,
                "locked_columns": columns if legacy_override else (
                    (profile.get("preference_policy") or {}).get("locked_columns", [])
                    if isinstance(profile.get("preference_policy"), dict)
                    else []
                ),
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

    def _scbs55_legacy_visible_list_override(self, source_contract: dict[str, Any]) -> dict[str, Any] | None:
        action_id = 0
        for raw in (
            source_contract.get("action_id"),
            source_contract.get("actionId"),
            (source_contract.get("head") or {}).get("action_id") if isinstance(source_contract.get("head"), dict) else None,
            (source_contract.get("source_meta") or {}).get("action_id") if isinstance(source_contract.get("source_meta"), dict) else None,
        ):
            try:
                action_id = int(raw or 0)
            except Exception:
                action_id = 0
            if action_id > 0:
                break
        if action_id <= 0 or "sc.legacy.user.priority.menu.plan" not in self.env:
            return None
        try:
            plan = self.env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False).search(
                [
                    ("source_document", "=", SCBS55_SOURCE_DOCUMENT),
                    ("target_action_id", "=", action_id),
                    ("list_field_contract", "!=", False),
                ],
                limit=1,
            )
        except Exception:
            _logger.debug("SCBS55 legacy visible list override lookup skipped", exc_info=True)
            return None
        if not plan:
            return None
        model_name = str(getattr(plan, "target_model", "") or source_contract.get("model") or "").strip()
        model_fields = {}
        try:
            model_fields = getattr(self.env[model_name], "_fields", {}) if model_name in self.env else {}
        except Exception:
            model_fields = {}

        columns: list[str] = []
        labels: dict[str, str] = {}
        for item in plan.list_field_contract or []:
            if not isinstance(item, dict):
                continue
            label = str(item.get("legacy_label") or "").strip()
            if not label or label == "操作":
                continue
            field_name = "p1_visible_" + hashlib.sha1(label.encode("utf-8")).hexdigest()[:12]
            if field_name in columns:
                continue
            if model_fields and field_name not in model_fields:
                continue
            columns.append(field_name)
            labels[field_name] = label
        if not columns:
            return None
        return {
            "source": "scbs55_legacy_user_priority_menu_plan",
            "action_id": action_id,
            "plan_id": int(plan.id),
            "columns": columns,
            "column_labels": labels,
        }

    def _inject_collaboration_contract(self, source_contract: dict[str, Any], *, model: str, view_type: str) -> None:
        try:
            has_model = bool(model and model in self.env)
        except Exception:
            return
        if view_type != "form" or not has_model:
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
                self._hydrate_attachment_display_values(record, field_names, merged)
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
                            self._hydrate_attachment_display_values(record, [name], merged)
                    except Exception:
                        _logger.debug("ui.contract.v2 field hydration skipped: %s.%s", model, name, exc_info=True)
        return merged

    def _hydrate_attachment_display_values(self, record, field_names: list[str], values: dict[str, Any]) -> None:
        for name in field_names:
            field = record._fields.get(name)
            if not field or field.type != "many2many" or field.comodel_name != "ir.attachment":
                continue
            raw_value = values.get(name)
            if not isinstance(raw_value, list):
                continue
            attachment_ids = [int(item) for item in raw_value if isinstance(item, int) or str(item).isdigit()]
            if not attachment_ids:
                continue
            attachments = self.env["ir.attachment"].sudo().browse(attachment_ids).exists()
            display_values = []
            for attachment in attachments:
                label = str(attachment.name or attachment.display_name or attachment.id)
                url = attachment.url or f"/web/content/{attachment.id}?download=true"
                label = f"{label} | {url}"
                display_values.append(label)
            values[name] = display_values

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

        projection_context = dict(getattr(self.env, "context", {}) or {})
        projection_context["contract_projection_readonly"] = True
        try:
            from odoo import api
            projection_env = api.Environment(self.env.cr, self.env.uid, projection_context)
            projection_su_env = api.Environment(self.su_env.cr, self.su_env.uid, projection_context)
        except Exception:
            projection_env = self.env
            projection_su_env = self.su_env
        resolved = UiContractHandler(
            projection_env,
            su_env=projection_su_env,
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
