# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import hashlib
import ast
from copy import deepcopy
from typing import Any, Dict, Optional
from lxml import etree

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
from ..utils.contract_governance import apply_contract_governance, resolve_contract_mode, resolve_contract_surface
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
BUSINESS_OPERATION_TECHNICAL_AUDIT_FIELDS = {
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
LEGACY_VISIBLE_BUSINESS_COLUMN_LABELS_BY_MODEL = {
    "project.material.plan": {
        "legacy_visible_01": "单据状态",
        "legacy_visible_02": "单据编号",
        "legacy_visible_05": "采购材料名称",
    },
    "sc.material.inbound": {
        "legacy_visible_01": "单据状态",
        "legacy_visible_02": "入库单号",
        "legacy_visible_05": "材料名称",
    },
}
STANDARD_LOWCODE_COLUMN_LABELS = {
    "source_created_by": "录入人",
    "source_created_at": "录入时间",
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

    def _set_v2_container_tree(self, contract: dict[str, Any], container_tree: list[Any]) -> None:
        if not isinstance(contract, dict):
            return
        layout_contract = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
        layout_contract["containerTree"] = container_tree
        contract["layoutContract"] = layout_contract

    def _set_v2_widget_status(self, contract: dict[str, Any], widget_status: list[dict[str, Any]]) -> None:
        if not isinstance(contract, dict):
            return
        status_contract = contract.get("statusContract") if isinstance(contract.get("statusContract"), dict) else {}
        status_contract["widgetStatus"] = widget_status
        contract["statusContract"] = status_contract

    def _set_v2_data_meta(self, contract: dict[str, Any], patch: dict[str, Any]) -> None:
        if not isinstance(contract, dict) or not isinstance(patch, dict):
            return
        data_contract = contract.get("dataContract") if isinstance(contract.get("dataContract"), dict) else {}
        data_meta = data_contract.get("dataMeta") if isinstance(data_contract.get("dataMeta"), dict) else {}
        data_meta.update(patch)
        data_contract["dataMeta"] = data_meta
        contract["dataContract"] = data_contract

    def _replace_v2_contract_content(self, contract: dict[str, Any], replacement: dict[str, Any]) -> None:
        if not isinstance(contract, dict) or not isinstance(replacement, dict):
            return
        contract.clear()
        contract.update(replacement)

    def _set_v2_governance_patch(self, contract: dict[str, Any], key: str, patch: dict[str, Any]) -> None:
        if not isinstance(contract, dict) or not key or not isinstance(patch, dict):
            return
        governance = contract.get("governance") if isinstance(contract.get("governance"), dict) else {}
        governance[key] = patch
        contract["governance"] = governance

    def _v2_policy_projection_source_authority(self, *, runtime_carrier: str, source_key: str) -> dict[str, Any]:
        return {
            "kind": self.SOURCE_KIND,
            "runtime_carrier": runtime_carrier,
            "projection_only": True,
            "no_business_fact_authority": self.NO_BUSINESS_FACT_AUTHORITY,
            "formal_projection": True,
            "fact_authority": "source_contract_projection",
            "source_key": source_key,
        }

    def _legacy_visible_business_label(
        self,
        model_name: str,
        field_name: str,
        current_label: str = "",
    ) -> str:
        field_name = str(field_name or "").strip()
        model_key = str(model_name or "").strip()
        if field_name in STANDARD_LOWCODE_COLUMN_LABELS:
            return STANDARD_LOWCODE_COLUMN_LABELS[field_name]
        label_maps = call_extension_hook_first(
            self.env,
            "smart_core_legacy_visible_business_column_labels",
            self.env,
        )
        if not isinstance(label_maps, dict):
            label_maps = LEGACY_VISIBLE_BUSINESS_COLUMN_LABELS_BY_MODEL
        label_map = label_maps.get(model_key, {}) if isinstance(label_maps.get(model_key), dict) else {}
        business_label = label_map.get(field_name)
        if not business_label:
            label = str(current_label or "").strip()
            if model_key in self.env and (
                field_name.startswith("legacy_visible_")
                or field_name.startswith("p1_visible_")
            ):
                try:
                    field = self.env[model_key]._fields.get(field_name)
                except Exception:
                    field = None
                field_label = str(getattr(field, "string", "") or "").strip()
                if field_name.startswith("p1_visible_") and field_label.startswith("P1可见"):
                    field_label = field_label[len("P1可见"):].strip()
                if field_label and field_label != field_name and (not label or label == field_name):
                    return field_label
            return label
        label = str(current_label or "").strip()
        if not label or label.startswith("历史验收可见字段"):
            return business_label
        return label

    def _apply_legacy_visible_business_labels(
        self,
        source_contract: dict[str, Any],
        columns: list[str],
        labels: dict[str, str] | None = None,
    ) -> dict[str, str]:
        labels = dict(labels or {})
        model_name = self._source_model_name(source_contract)
        for name in columns:
            normalized = str(name or "").strip()
            label = self._legacy_visible_business_label(model_name, normalized, labels.get(normalized, ""))
            if label:
                labels[normalized] = label
        return labels

    def _form_field_aliases(self, model: str, source_contract: dict[str, Any] | None = None) -> dict[str, str]:
        payload = call_extension_hook_first(
            self.env,
            "smart_core_form_field_aliases",
            self.env,
            {
                "model": str(model or "").strip(),
                "source_contract": source_contract if isinstance(source_contract, dict) else {},
            },
        )
        if not isinstance(payload, dict):
            return {}
        return {
            str(key or "").strip(): str(value or "").strip()
            for key, value in payload.items()
            if str(key or "").strip() and str(value or "").strip()
        }

    def _resolve_form_field_alias(self, name: str, aliases: dict[str, str]) -> str:
        normalized = str(name or "").strip()
        return aliases.get(normalized, normalized)

    def _apply_extension_projected_contract_normalizers(
        self,
        source_contract: dict[str, Any],
        *,
        view_type: str,
        client_type: str,
        delivery_profile: str,
    ) -> dict[str, Any]:
        payload = call_extension_hook_first(
            self.env,
            "smart_core_normalize_projected_contract_data",
            self.env,
            source_contract,
            {
                "view_type": view_type,
                "subject": "ui.contract.v2",
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "client_type": client_type,
                    "delivery_profile": delivery_profile,
                },
            },
        )
        return dict(payload) if isinstance(payload, dict) else source_contract

    def _apply_extension_unified_page_contract_normalizers(
        self,
        contract_v2: dict[str, Any],
        *,
        source_contract: dict[str, Any],
        view_type: str,
        client_type: str,
        delivery_profile: str,
    ) -> dict[str, Any]:
        payload = call_extension_hook_first(
            self.env,
            "smart_core_normalize_unified_page_contract_v2",
            self.env,
            contract_v2,
            {
                "source_contract": source_contract,
                "view_type": view_type,
                "subject": "ui.contract.v2",
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "client_type": client_type,
                    "delivery_profile": delivery_profile,
                },
            },
        )
        return dict(payload) if isinstance(payload, dict) else contract_v2

    def _v2_policy_projection(self, value: dict[str, Any], *, runtime_carrier: str, source_key: str) -> dict[str, Any]:
        projection = deepcopy(value or {})
        projection["sourceAuthority"] = self._v2_policy_projection_source_authority(
            runtime_carrier=runtime_carrier,
            source_key=source_key,
        )
        return projection

    def _project_v2_source_policies(self, contract: dict[str, Any], source_contract: dict[str, Any]) -> None:
        if not isinstance(contract, dict) or not isinstance(source_contract, dict):
            return
        if isinstance(source_contract.get("delete_policy"), dict):
            delete_policy = dict(source_contract.get("delete_policy") or {})
            action_contract = contract.get("actionContract") if isinstance(contract.get("actionContract"), dict) else {}
            action_contract["deletePolicy"] = self._v2_policy_projection(
                delete_policy,
                runtime_carrier="ui.contract.v2.actionContract.deletePolicy",
                source_key="delete_policy",
            )
            contract["actionContract"] = action_contract
        if isinstance(source_contract.get("surface_policies"), dict):
            surface_policies = deepcopy(source_contract.get("surface_policies") or {})
            action_contract = contract.get("actionContract") if isinstance(contract.get("actionContract"), dict) else {}
            action_contract["surfacePolicies"] = self._v2_policy_projection(
                surface_policies,
                runtime_carrier="ui.contract.v2.actionContract.surfacePolicies",
                source_key="surface_policies",
            )
            contract["actionContract"] = action_contract
        if isinstance(source_contract.get("list_profile"), dict):
            list_profile = deepcopy(source_contract.get("list_profile") or {})
            columns = self._user_visible_list_columns(list_profile.get("columns") if isinstance(list_profile.get("columns"), list) else [])
            fact_columns = self._user_visible_list_columns(list_profile.get("fact_columns") if isinstance(list_profile.get("fact_columns"), list) else [])
            if columns:
                list_profile["columns"] = columns
            if fact_columns:
                list_profile["fact_columns"] = fact_columns
            list_profile["hidden_columns"] = [
                name
                for name in self._user_visible_list_columns(list_profile.get("hidden_columns") if isinstance(list_profile.get("hidden_columns"), list) else [])
                if not columns or name in columns
            ]
            column_labels = list_profile.get("column_labels") if isinstance(list_profile.get("column_labels"), dict) else {}
            if column_labels:
                list_profile["column_labels"] = {
                    str(name or "").strip(): label
                    for name, label in column_labels.items()
                    if str(name or "").strip() and str(name or "").strip() not in BUSINESS_OPERATION_TECHNICAL_AUDIT_FIELDS
                }
            preference_policy = list_profile.get("preference_policy") if isinstance(list_profile.get("preference_policy"), dict) else {}
            if preference_policy:
                preference_policy = deepcopy(preference_policy)
                for key in ("locked_columns", "must_request_columns"):
                    if isinstance(preference_policy.get(key), list):
                        preference_policy[key] = self._user_visible_list_columns(preference_policy.get(key) or [])
                list_profile["preference_policy"] = preference_policy
            layout_contract = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
            layout_contract["listProfile"] = self._v2_policy_projection(
                list_profile,
                runtime_carrier="ui.contract.v2.layoutContract.listProfile",
                source_key="list_profile",
            )
            contract["layoutContract"] = layout_contract

    def _enforce_business_list_config_projection(self, contract: dict[str, Any], source_contract: dict[str, Any]) -> None:
        if not isinstance(contract, dict) or not isinstance(source_contract, dict):
            return
        profile = source_contract.get("list_profile") if isinstance(source_contract.get("list_profile"), dict) else {}
        policy = profile.get("column_policy") if isinstance(profile.get("column_policy"), dict) else {}
        if str(policy.get("reason") or "").strip() != "business_list_config_contract_authoritative":
            return
        columns = [
            str(name or "").strip()
            for name in (profile.get("columns") if isinstance(profile.get("columns"), list) else [])
            if str(name or "").strip()
        ]
        fact_columns = [
            str(name or "").strip()
            for name in (profile.get("fact_columns") if isinstance(profile.get("fact_columns"), list) else [])
            if str(name or "").strip()
        ]
        if fact_columns and any(name not in columns for name in fact_columns):
            columns = list(fact_columns)
        if not columns:
            return
        columns = self._merge_user_list_preference_columns(source_contract, columns)
        locked_profile = deepcopy(profile)
        profile_labels = locked_profile.get("column_labels") if isinstance(locked_profile.get("column_labels"), dict) else {}
        locked_profile["column_labels"] = self._apply_legacy_visible_business_labels(
            source_contract,
            columns,
            profile_labels,
        )
        locked_profile["columns"] = columns
        locked_profile["fact_columns"] = list(fact_columns or columns)
        locked_profile["hidden_columns"] = [
            str(name or "").strip()
            for name in (locked_profile.get("hidden_columns") if isinstance(locked_profile.get("hidden_columns"), list) else [])
            if str(name or "").strip() in set(columns)
        ]
        pref = locked_profile.get("preference_policy") if isinstance(locked_profile.get("preference_policy"), dict) else {}
        locked_profile["preference_policy"] = {
            **pref,
            "scope": "business_config_contract",
            "allow_visibility": True,
            "allow_order": True,
            "allow_width": bool(pref.get("allow_width", True)),
            "locked_columns": [],
            "must_request_columns": list(locked_profile.get("fact_columns") or columns),
        }
        self._project_v2_source_policies(contract, {"list_profile": locked_profile})
        profile_projection = ((contract.get("layoutContract") or {}).get("listProfile") or {})
        source_authority = profile_projection.get("sourceAuthority") if isinstance(profile_projection, dict) else {}
        if isinstance(source_authority, dict):
            source_authority["source_key"] = "list_profile.business_config_contract_authoritative"

    def _merge_user_list_preference_columns(self, source_contract: dict[str, Any], columns: list[str]) -> list[str]:
        action_id = self._source_action_id(source_contract)
        if action_id <= 0 or "sc.user.view.preference" not in self.env:
            return columns
        model_name = self._source_model_name(source_contract)
        model_fields = set(getattr(self.env[model_name], "_fields", {}) or {}) if model_name in self.env else set()
        try:
            rec = self.env["sc.user.view.preference"].sudo().search(
                [
                    ("user_id", "=", self.env.user.id),
                    ("preference_key", "=", "list_columns"),
                    ("view_type", "in", ["list", "tree"]),
                    ("action_id", "=", action_id),
                ],
                order="id desc",
                limit=1,
            )
        except Exception:
            _logger.debug("ui.contract.v2 user list preference lookup skipped", exc_info=True)
            return columns
        value = rec.value_json if rec and isinstance(getattr(rec, "value_json", None), dict) else {}
        preferred = []
        for key in ("visible_columns", "column_order"):
            rows = value.get(key) if isinstance(value.get(key), list) else []
            for raw in rows:
                name = str(raw or "").strip()
                if not name or name in preferred:
                    continue
                if model_fields and name not in model_fields:
                    continue
                preferred.append(name)
        if not preferred:
            return columns
        return [*preferred, *[name for name in columns if name not in preferred]]

    def _user_visible_list_columns(self, columns: list[Any]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for raw in columns:
            name = str(raw or "").strip()
            if not name or name in BUSINESS_OPERATION_TECHNICAL_AUDIT_FIELDS or name in seen:
                continue
            seen.add(name)
            out.append(name)
        return out

    def _apply_list_profile_layout(self, contract_v2: dict[str, Any], source_contract: dict[str, Any]) -> None:
        if not isinstance(contract_v2, dict) or not isinstance(source_contract, dict):
            return
        page_info = contract_v2.get("pageInfo") if isinstance(contract_v2.get("pageInfo"), dict) else {}
        view_type = str(
            contract_v2.get("viewType")
            or page_info.get("viewType")
            or source_contract.get("view_type")
            or ""
        ).strip().lower()
        if view_type not in {"tree", "list"}:
            return
        profile = source_contract.get("list_profile") if isinstance(source_contract.get("list_profile"), dict) else {}
        columns = self._user_visible_list_columns(profile.get("columns") if isinstance(profile.get("columns"), list) else [])
        if not columns:
            return
        labels = profile.get("column_labels") if isinstance(profile.get("column_labels"), dict) else {}
        field_map = source_contract.get("fields") if isinstance(source_contract.get("fields"), dict) else {}

        def widget_for(name: str) -> dict[str, Any]:
            field = field_map.get(name) if isinstance(field_map.get(name), dict) else {}
            field_type = str(field.get("type") or field.get("ttype") or "char").strip() or "char"
            label = str(labels.get(name) or field.get("string") or field.get("label") or name).strip()
            return {
                "widgetId": f"field.{name}",
                "widgetType": "table",
                "fieldCode": name,
                "label": label,
                "span": 12,
                "componentKey": "sc.table.data",
                "capabilities": ["sortable", "filterable"],
                "componentConfig": {
                    "readonly": True,
                    "required": False,
                    "fieldType": field_type,
                },
            }

        widgets = [widget_for(name) for name in columns]
        layout = contract_v2.get("layoutContract") if isinstance(contract_v2.get("layoutContract"), dict) else {}
        containers = layout.get("containerTree") if isinstance(layout.get("containerTree"), list) else []
        if not containers:
            return

        def apply_to_first_table_container(rows: list[Any]) -> bool:
            for node in rows:
                if not isinstance(node, dict):
                    continue
                if isinstance(node.get("widgetList"), list):
                    node["widgetList"] = deepcopy(widgets)
                    node["children"] = []
                    return True
                for key in ("children", "pages", "tabs", "nodes", "items"):
                    children = node.get(key)
                    if isinstance(children, list) and apply_to_first_table_container(children):
                        return True
            return False

        changed = apply_to_first_table_container(containers)
        if not changed and isinstance(containers[0], dict):
            containers[0]["widgetList"] = deepcopy(widgets)
            containers[0]["children"] = []
            changed = True
        if changed:
            layout["componentRegistry"] = {
                **(layout.get("componentRegistry") if isinstance(layout.get("componentRegistry"), dict) else {}),
                "sc.table.data": {"componentKey": "sc.table.data"},
            }
            self._set_v2_data_meta(contract_v2, {"fieldCount": len(columns)})

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
        self._inject_action_window_contract(
            source_contract,
            params=params,
            ui_params=ui_params,
        )
        self._inject_current_form_settings_action(
            source_contract,
            params=params,
            ui_params=ui_params,
            model=str(model or "").strip(),
            view_type=str(view_type or "").strip().lower(),
        )
        self._inject_record_business_category_context(
            source_contract,
            model=str(model or "").strip(),
            record_id=params.get("record_id") or params.get("recordId") or ui_params.get("record_id") or ui_params.get("recordId"),
        )
        self._inject_business_category_form_policy(
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
        self._inject_standard_submit_header_button(
            source_contract,
            model=str(model or "").strip(),
            view_type=str(view_type or "").strip().lower(),
            render_profile=str(params.get("render_profile") or params.get("renderProfile") or params.get("profile") or "").strip().lower(),
            record_id=params.get("record_id") or params.get("recordId"),
        )
        self._inject_collaboration_contract(
            source_contract,
            model=str(model or "").strip(),
            view_type=str(view_type or "").strip().lower(),
        )
        self._inject_native_group_layout_columns(
            source_contract,
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
        hook_payload = call_extension_hook_first(
            self.env,
            "smart_core_finalize_projected_contract_data",
            self.env,
            source_contract,
            {
                "view_type": str(view_type or "").strip().lower(),
                "subject": "ui.contract.v2",
                "versions": {},
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "client_type": client_type,
                    "delivery_profile": delivery_profile,
                    "params": dict(params),
                    "ui_params": dict(ui_params),
                },
            },
        )
        if isinstance(hook_payload, dict):
            source_contract = dict(hook_payload)
        source_contract = self._apply_extension_projected_contract_normalizers(
            source_contract,
            view_type=str(view_type or "").strip().lower(),
            client_type=client_type,
            delivery_profile=delivery_profile,
        )
        contract_v2 = assemble_unified_page_contract_v2(
            source_contract,
            source_type="ui.contract",
            client_type=client_type,
            request_id=str(request_id),
        )
        self._apply_field_policies_to_v2_status(contract_v2, source_contract)
        self._ensure_native_layout_widget_status_visible(contract_v2)
        self._apply_legacy_visible_list_layout(contract_v2, source_contract)
        hook_payload = call_extension_hook_first(
            self.env,
            "smart_core_finalize_unified_page_contract_v2",
            self.env,
            contract_v2,
            {
                "source_contract": source_contract,
                "view_type": str(view_type or "").strip().lower(),
                "subject": "ui.contract.v2",
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "client_type": client_type,
                    "delivery_profile": delivery_profile,
                    "params": dict(params),
                    "ui_params": dict(ui_params),
                },
            },
        )
        if isinstance(hook_payload, dict):
            contract_v2 = dict(hook_payload)
        self._project_v2_source_policies(contract_v2, source_contract)
        contract_v2 = self._apply_extension_unified_page_contract_normalizers(
            contract_v2,
            source_contract=source_contract,
            view_type=str(view_type or "").strip().lower(),
            client_type=client_type,
            delivery_profile=delivery_profile,
        )
        self._apply_business_config_form_groups_to_v2(contract_v2, source_contract=source_contract)
        self._enforce_business_list_config_projection(contract_v2, source_contract)
        self._apply_list_profile_layout(contract_v2, source_contract)
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

    def _apply_business_config_form_groups_to_v2(
        self,
        contract: dict[str, Any],
        *,
        source_contract: dict[str, Any] | None = None,
    ) -> None:
        if not isinstance(contract, dict):
            return
        view_type = str(
            contract.get("viewType")
            or ((contract.get("pageInfo") or {}).get("viewType") if isinstance(contract.get("pageInfo"), dict) else "")
            or (source_contract or {}).get("view_type")
            or ""
        ).strip().lower()
        if view_type != "form":
            return
        layout_contract = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
        container_tree = layout_contract.get("containerTree") if isinstance(layout_contract.get("containerTree"), list) else []
        if not container_tree:
            return
        governance = self._form_layout_governance(source_contract)
        field_groups = governance.get("field_groups") if isinstance(governance.get("field_groups"), dict) else {}
        if not field_groups:
            return
        hidden_field_names = {
            str(item or "").strip()
            for item in (governance.get("hidden_field_names") or [])
            if str(item or "").strip()
        }

        configured_groups: list[tuple[str, list[str]]] = []
        configured_names: set[str] = set()
        for raw_title, raw_names in field_groups.items():
            title = str(raw_title or "").strip()
            if title and not self._form_layout_group_visible_from_governance(governance, title):
                continue
            names = [
                str(name or "").strip()
                for name in (raw_names if isinstance(raw_names, list) else [])
                if str(name or "").strip()
            ]
            names = [name for name in names if name not in hidden_field_names]
            names = [name for name in names if name not in configured_names]
            if not title or not names:
                continue
            configured_names.update(names)
            configured_groups.append((title, names))
        if not configured_groups:
            return

        moved_nodes: dict[str, dict[str, Any]] = {}

        def node_field_name(node: Any) -> str:
            if not isinstance(node, dict):
                return ""
            return str(node.get("name") or node.get("field") or node.get("fieldCode") or "").strip()

        def remove_configured_fields(nodes: list[Any]) -> list[Any]:
            out: list[Any] = []
            for node in nodes:
                if not isinstance(node, dict):
                    out.append(node)
                    continue
                node_type = str(node.get("type") or node.get("containerType") or "").strip().lower()
                name = node_field_name(node)
                if node_type == "field" and name in configured_names:
                    moved_nodes.setdefault(name, deepcopy(node))
                    continue
                next_node = node
                for key in ("children", "pages", "tabs", "nodes", "items", "widgetList"):
                    children = next_node.get(key)
                    if isinstance(children, list):
                        cleaned = remove_configured_fields(children)
                        if cleaned is not children:
                            next_node = dict(next_node)
                            next_node[key] = cleaned
                out.append(next_node)
            return out

        container_tree = remove_configured_fields(container_tree)

        def group_title(node: Any) -> str:
            if not isinstance(node, dict):
                return ""
            if str(node.get("type") or node.get("containerType") or "").strip().lower() != "group":
                return ""
            return str(node.get("string") or node.get("label") or node.get("title") or "").strip()

        def find_group(nodes: list[Any], title: str) -> dict[str, Any] | None:
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                if group_title(node) == title:
                    return node
                for key in ("children", "pages", "tabs", "nodes", "items"):
                    children = node.get(key)
                    if isinstance(children, list):
                        found = find_group(children, title)
                        if found is not None:
                            return found
            return None

        for index, (title, names) in enumerate(configured_groups, start=1):
            group = find_group(container_tree, title)
            if group is None:
                group = {
                    "type": "group",
                    "name": "business_config_group_%s" % index,
                    "string": title,
                    "label": title,
                    "children": [],
                    "widgetList": [],
                }
                container_tree.append(group)
            self._apply_form_layout_governance_to_group(group, title, source_contract=source_contract)
            children = group.get("children") if isinstance(group.get("children"), list) else []
            for name in names:
                node = moved_nodes.get(name)
                if isinstance(node, dict):
                    children.append(deepcopy(node))
            group["children"] = children

        self._set_v2_container_tree(contract, container_tree)

    def _form_layout_governance(self, source_contract: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(source_contract, dict):
            return {}
        profile = source_contract.get("business_operation_profile")
        if not isinstance(profile, dict):
            return {}
        governance = profile.get("form_structure_governance")
        return governance if isinstance(governance, dict) else {}

    def _form_layout_governance_columns(self, source_contract: dict[str, Any] | None, title: str = "") -> int:
        governance = self._form_layout_governance(source_contract)
        return self._form_layout_columns_from_governance(governance, title)

    def _form_layout_columns_from_governance(self, governance: dict[str, Any] | None, title: str = "") -> int:
        if not isinstance(governance, dict):
            return 0
        group_columns = governance.get("group_columns") if isinstance(governance.get("group_columns"), dict) else {}
        columns = 0
        key = str(title or "").strip()
        if key:
            try:
                columns = int(group_columns.get(key) or 0)
            except (TypeError, ValueError):
                columns = 0
        if columns <= 0:
            try:
                columns = int(governance.get("form_columns") or 0)
            except (TypeError, ValueError):
                columns = 0
        return columns if columns > 0 else 0

    def _form_layout_group_visible_from_governance(self, governance: dict[str, Any] | None, title: str = "") -> bool:
        if not isinstance(governance, dict):
            return True
        group_visibility = governance.get("group_visibility") if isinstance(governance.get("group_visibility"), dict) else {}
        key = str(title or "").strip()
        if not key or key not in group_visibility:
            return True
        return bool(group_visibility.get(key))

    def _apply_form_layout_governance_to_group(
        self,
        node: dict[str, Any],
        title: str = "",
        *,
        source_contract: dict[str, Any] | None = None,
    ) -> None:
        if not isinstance(node, dict):
            return
        resolved_title = str(
            title
            or node.get("string")
            or node.get("label")
            or node.get("title")
            or node.get("name")
            or ""
        ).strip()
        columns = self._form_layout_governance_columns(source_contract, resolved_title)
        if columns <= 0:
            return
        node["cols"] = columns
        node["columns"] = columns
        attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
        attrs["col"] = str(columns)
        node["attributes"] = attrs

    def _apply_legacy_visible_list_layout(self, contract_v2: dict[str, Any], source_contract: dict[str, Any]) -> None:
        profile = source_contract.get("list_profile") if isinstance(source_contract.get("list_profile"), dict) else {}
        columns = [
            str(name or "").strip()
            for name in (profile.get("columns") if isinstance(profile.get("columns"), list) else [])
            if str(name or "").strip()
        ]
        if not columns or not all(name.startswith("legacy_visible_") for name in columns):
            return
        model_name = str(
            source_contract.get("model")
            or ((source_contract.get("pageInfo") or {}).get("model") if isinstance(source_contract.get("pageInfo"), dict) else "")
            or ((source_contract.get("head") or {}).get("model") if isinstance(source_contract.get("head"), dict) else "")
            or ""
        ).strip()
        direct_order: list[str] = []
        if model_name and "ui.business.config.contract" in self.env:
            try:
                view_ids = source_contract.get("view_ids_by_type") if isinstance(source_contract.get("view_ids_by_type"), dict) else {}
                configs = self.env["ui.business.config.contract"]._effective_view_orchestration_contracts(
                    model_name,
                    view_type="form",
                    action_id=self._source_action_id(source_contract),
                    view_id=view_ids.get("form"),
                )
            except Exception:
                configs = []
            for config in configs:
                payload = config.contract_json if isinstance(config.contract_json, dict) else {}
                orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
                views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
                form_spec = views.get("form") if isinstance(views.get("form"), dict) else {}
                rows = form_spec.get("fields") if isinstance(form_spec.get("fields"), list) else []
                normalized_rows: list[tuple[int, str, bool]] = []
                for row in rows:
                    if isinstance(row, str):
                        normalized_rows.append((100, str(row or "").strip(), True))
                        continue
                    if not isinstance(row, dict):
                        continue
                    try:
                        sequence = int(row.get("sequence") or row.get("order") or 100)
                    except Exception:
                        sequence = 100
                    normalized_rows.append((
                        sequence,
                        str(row.get("name") or row.get("field") or row.get("field_name") or "").strip(),
                        row.get("visible") is not False,
                    ))
                for _sequence, name, visible in sorted(normalized_rows, key=lambda item: (item[0], item[1])):
                    if not name or not visible:
                        continue
                    if name.startswith("legacy_visible_") and name in columns and name not in direct_order:
                        direct_order.append(name)
        if direct_order:
            ordered = list(direct_order)
            ordered.extend([name for name in columns if name not in set(ordered)])
            columns = ordered
        labels = profile.get("column_labels") if isinstance(profile.get("column_labels"), dict) else {}
        labels = self._apply_legacy_visible_business_labels(source_contract, columns, labels)
        field_map = source_contract.get("fields") if isinstance(source_contract.get("fields"), dict) else {}

        def widget_for(name: str) -> dict[str, Any]:
            field = field_map.get(name) if isinstance(field_map.get(name), dict) else {}
            field_type = str(field.get("type") or field.get("ttype") or "char").strip() or "char"
            label = str(labels.get(name) or field.get("string") or field.get("label") or name).strip()
            label = self._legacy_visible_business_label(model_name, name, label)
            return {
                "widgetId": f"field.{name}",
                "widgetType": "table",
                "fieldCode": name,
                "label": label,
                "span": 12,
                "componentKey": "sc.table.data",
                "capabilities": ["sortable", "filterable"],
                "componentConfig": {
                    "readonly": True,
                    "required": False,
                    "fieldType": field_type,
                },
            }

        widgets = [widget_for(name) for name in columns]
        layout = contract_v2.get("layoutContract") if isinstance(contract_v2.get("layoutContract"), dict) else {}
        containers = layout.get("containerTree") if isinstance(layout.get("containerTree"), list) else []
        changed = False
        for container in containers:
            if not isinstance(container, dict):
                continue
            existing = container.get("widgetList")
            if isinstance(existing, list):
                container["widgetList"] = deepcopy(widgets)
                container["children"] = []
                changed = True
                break
        if not changed and containers:
            container = containers[0]
            if isinstance(container, dict):
                container["widgetList"] = deepcopy(widgets)
                container["children"] = []
                changed = True
        if changed:
            layout["componentRegistry"] = {
                **(layout.get("componentRegistry") if isinstance(layout.get("componentRegistry"), dict) else {}),
                "sc.table.data": {"componentKey": "sc.table.data"},
            }
            self._set_v2_data_meta(contract_v2, {"fieldCount": len(columns)})

    def _apply_field_policies_to_v2_status(self, contract_v2: dict[str, Any], source_contract: dict[str, Any]) -> None:
        field_policies = source_contract.get("field_policies") if isinstance(source_contract.get("field_policies"), dict) else {}
        if not field_policies:
            return
        business_policy = source_contract.get("business_form_policy") if isinstance(source_contract.get("business_form_policy"), dict) else {}
        render_profile = str(
            source_contract.get("render_profile")
            or business_policy.get("render_profile")
            or ""
        ).strip().lower()
        if render_profile in {"read", "view"}:
            render_profile = "readonly"
        if render_profile not in {"create", "edit", "readonly"}:
            render_profile = "edit"
        status_contract = contract_v2.get("statusContract") if isinstance(contract_v2.get("statusContract"), dict) else {}
        widget_status = status_contract.get("widgetStatus") if isinstance(status_contract.get("widgetStatus"), list) else []
        by_widget: dict[str, list[dict[str, Any]]] = {}
        for row in widget_status:
            if not isinstance(row, dict):
                continue
            widget_id = str(row.get("widgetId") or "").strip()
            if widget_id:
                by_widget.setdefault(widget_id, []).append(row)

        def apply_policy(row: dict[str, Any], policy: dict[str, Any]) -> None:
            visible_profiles = policy.get("visible_profiles")
            if isinstance(visible_profiles, list) and visible_profiles:
                row["visible"] = render_profile in {str(item) for item in visible_profiles}
            readonly_profiles = policy.get("readonly_profiles")
            if isinstance(readonly_profiles, list) and readonly_profiles:
                row["readonly"] = render_profile in {str(item) for item in readonly_profiles}
            required_profiles = policy.get("required_profiles")
            if isinstance(required_profiles, list) and required_profiles:
                row["required"] = render_profile in {str(item) for item in required_profiles}
            for key in ("visible", "readonly", "required", "disabled"):
                if isinstance(policy.get(key), bool):
                    row[key] = bool(policy.get(key))
            row["auth"] = "none" if row.get("visible") is False else "read" if row.get("readonly") else "edit"

        for field_name, policy in field_policies.items():
            if not isinstance(policy, dict):
                continue
            field_code = str(field_name or "").strip()
            if not field_code:
                continue
            widget_id = f"field.{field_code}"
            rows = by_widget.get(widget_id)
            if not rows:
                row = {
                    "widgetId": widget_id,
                    "visible": True,
                    "readonly": False,
                    "required": False,
                    "disabled": False,
                    "auth": "edit",
                }
                widget_status.append(row)
                rows = [row]
            for row in rows:
                apply_policy(row, policy)
        self._set_v2_widget_status(contract_v2, widget_status)

    def _ensure_native_layout_widget_status_visible(self, contract_v2: dict[str, Any]) -> None:
        layout_contract = contract_v2.get("layoutContract") if isinstance(contract_v2.get("layoutContract"), dict) else {}
        container_tree = layout_contract.get("containerTree") if isinstance(layout_contract.get("containerTree"), list) else []
        if not container_tree:
            return

        def modifier_true(value: Any) -> bool:
            if value is True or value == 1:
                return True
            if isinstance(value, str):
                return value.strip().lower() in {"1", "true", "yes"}
            return False

        def node_invisible(node: dict[str, Any]) -> bool:
            if modifier_true(node.get("invisible")):
                return True
            attributes = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
            modifiers = node.get("modifiers") if isinstance(node.get("modifiers"), dict) else {}
            attribute_modifiers = attributes.get("modifiers") if isinstance(attributes.get("modifiers"), dict) else {}
            return any(
                modifier_true(value)
                for value in (
                    attributes.get("invisible"),
                    modifiers.get("invisible"),
                    attribute_modifiers.get("invisible"),
                )
            )

        visible_widget_ids: set[str] = set()

        def walk(rows: list[Any]) -> None:
            for row in rows:
                if not isinstance(row, dict):
                    continue
                node_type = str(row.get("type") or row.get("containerType") or "").strip().lower()
                if node_type == "field" and not node_invisible(row):
                    widget_id = str(row.get("widgetId") or "").strip()
                    if not widget_id:
                        field_name = str(row.get("name") or row.get("field") or "").strip()
                        widget_id = f"field.{field_name}" if field_name else ""
                    if widget_id:
                        visible_widget_ids.add(widget_id)
                for key in ("children", "pages", "tabs", "nodes", "items"):
                    children = row.get(key)
                    if isinstance(children, list):
                        walk(children)

        walk(container_tree)
        if not visible_widget_ids:
            return
        status_contract = contract_v2.get("statusContract") if isinstance(contract_v2.get("statusContract"), dict) else {}
        widget_status = status_contract.get("widgetStatus") if isinstance(status_contract.get("widgetStatus"), list) else []
        seen: set[str] = set()
        for row in widget_status:
            if not isinstance(row, dict):
                continue
            widget_id = str(row.get("widgetId") or "").strip()
            if widget_id not in visible_widget_ids:
                continue
            seen.add(widget_id)
            row["visible"] = True
            if row.get("readonly") is True:
                row["auth"] = "read"
            elif row.get("disabled") is not True:
                row["auth"] = "edit"
        for widget_id in sorted(visible_widget_ids - seen):
            widget_status.append({
                "widgetId": widget_id,
                "visible": True,
                "readonly": False,
                "required": False,
                "disabled": False,
                "auth": "edit",
            })
        self._set_v2_widget_status(contract_v2, widget_status)

    def _inject_action_window_contract(
        self,
        source_contract: dict[str, Any],
        *,
        params: dict[str, Any],
        ui_params: dict[str, Any],
    ) -> None:
        head = source_contract.get("head") if isinstance(source_contract.get("head"), dict) else {}
        raw_action_id = (
            params.get("action_id")
            or params.get("actionId")
            or ui_params.get("action_id")
            or ui_params.get("actionId")
            or source_contract.get("action_id")
            or source_contract.get("actionId")
            or head.get("action_id")
        )
        action_id, action_error = parse_positive_int(raw_action_id, allow_empty=True)
        if action_error or not action_id:
            return
        try:
            Action = self.env["ir.actions.act_window"].sudo()
            action = Action.browse(action_id)
        except Exception:
            _logger.debug("ui.contract.v2 action metadata lookup skipped", exc_info=True)
            return
        try:
            if not action.exists():
                return
        except Exception:
            return

        action_name = str(getattr(action, "name", "") or "").strip()
        action_model = str(getattr(action, "res_model", "") or "").strip()
        action_domain_raw = getattr(action, "domain", None)
        action_context_raw = getattr(action, "context", None)
        action_domain = _safe_eval_action_value(action_domain_raw, [])
        action_context = _safe_eval_action_value(action_context_raw, {})

        source_contract["action_id"] = action_id
        if action_model:
            source_contract["model"] = action_model
        if action_name:
            source_contract["title"] = action_name
            head = source_contract.get("head") if isinstance(source_contract.get("head"), dict) else {}
            head = dict(head)
            head["title"] = action_name
            head["action_id"] = action_id
            source_contract["head"] = head

        if isinstance(action_domain, list):
            if not source_contract.get("domain"):
                source_contract["domain"] = deepcopy(action_domain)
            head = source_contract.get("head") if isinstance(source_contract.get("head"), dict) else {}
            head = dict(head)
            head.setdefault("domain", deepcopy(action_domain))
            source_contract["head"] = head
        if isinstance(action_domain_raw, str) and action_domain_raw.strip():
            if not source_contract.get("domain_raw"):
                source_contract["domain_raw"] = action_domain_raw

        if isinstance(action_context, dict):
            current_context = source_contract.get("context") if isinstance(source_contract.get("context"), dict) else {}
            merged_context = dict(action_context)
            merged_context.update(current_context)
            source_contract["context"] = merged_context
            head = source_contract.get("head") if isinstance(source_contract.get("head"), dict) else {}
            head = dict(head)
            head.setdefault("context", deepcopy(merged_context))
            source_contract["head"] = head
        if isinstance(action_context_raw, str) and action_context_raw.strip():
            if not source_contract.get("context_raw"):
                source_contract["context_raw"] = action_context_raw

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

    def _inject_business_category_form_policy(
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
        try:
            from ..app_config_engine.services.assemblers.page_assembler import PageAssembler

            request_context: dict[str, Any] = {}
            action_id, _action_id_error = parse_positive_int(
                params.get("action_id") or ui_params.get("action_id"),
                allow_empty=True,
            )
            if action_id:
                action = self.env["ir.actions.act_window"].sudo().browse(action_id)
                if action.exists() and action.res_model == model:
                    raw_action_context = action.context or "{}"
                    try:
                        action_context = (
                            dict(raw_action_context)
                            if isinstance(raw_action_context, dict)
                            else ast.literal_eval(raw_action_context)
                        )
                    except Exception:
                        action_context = {}
                    if isinstance(action_context, dict):
                        request_context.update(action_context)
            for raw_context in (params.get("context"), ui_params.get("context")):
                if isinstance(raw_context, dict):
                    request_context.update(raw_context)

            def normalize_allowed_business_category_codes(value: Any) -> list[str]:
                if value in (None, ""):
                    return []
                if isinstance(value, (list, tuple, set)):
                    raw_items = value
                else:
                    raw_items = str(value).replace(";", ",").split(",")
                result = []
                seen = set()
                for item in raw_items:
                    code = str(item or "").strip()
                    if not code or code in seen:
                        continue
                    seen.add(code)
                    result.append(code)
                return result

            for key in (
                "current_business_category_code",
                "default_business_category_code",
                "current_business_category_label",
                "default_business_category_label",
                "default_business_category_id",
                "default_type",
                "default_subject",
                "allowed_business_category_codes",
            ):
                if params.get(key) not in (None, ""):
                    request_context[key] = params.get(key)
                elif ui_params.get(key) not in (None, ""):
                    request_context[key] = ui_params.get(key)
            allowed_codes = normalize_allowed_business_category_codes(
                request_context.get("allowed_business_category_codes")
            )
            if allowed_codes:
                request_context["allowed_business_category_codes"] = allowed_codes
            if request_context:
                current_context = source_contract.get("context") if isinstance(source_contract.get("context"), dict) else {}
                merged_context = dict(current_context)
                merged_context.update(request_context)
                source_contract["context"] = merged_context
                head = source_contract.get("head") if isinstance(source_contract.get("head"), dict) else {}
                head = dict(head)
                head["context"] = merged_context
                source_contract["head"] = head
            else:
                merged_context = source_contract.get("context") if isinstance(source_contract.get("context"), dict) else {}
            render_profile = (
                params.get("render_profile")
                or params.get("renderProfile")
                or ui_params.get("render_profile")
                or ui_params.get("renderProfile")
                or source_contract.get("render_profile")
                or "edit"
            )
            normalized_render_profile = str(render_profile or "").strip().lower()
            if normalized_render_profile in {"read", "view"}:
                normalized_render_profile = "readonly"
            if normalized_render_profile not in {"create", "edit", "readonly"}:
                normalized_render_profile = "edit"
            source_contract["render_profile"] = normalized_render_profile
            assembler = PageAssembler(self.env, self.su_env)
            assembler._inject_business_category_form_policy(
                source_contract,
                model_name=model,
                render_profile=normalized_render_profile,
            )
            assembler._inject_relation_entry_contract(source_contract, model)
            if not source_contract.get("business_form_policy"):
                return
            business_policy_groups = deepcopy(
                source_contract.get("field_groups")
                if isinstance(source_contract.get("field_groups"), list)
                else []
            )
            business_policy_root = source_contract.get("business_form_policy") if isinstance(source_contract.get("business_form_policy"), dict) else {}
            business_policy_fields = deepcopy(
                business_policy_root.get("fields")
                if isinstance(business_policy_root.get("fields"), list)
                else []
            )
            contract_mode = resolve_contract_mode(params)
            contract_surface = resolve_contract_surface(params, contract_mode)
            governed = apply_contract_governance(
                source_contract,
                contract_mode,
                contract_surface=contract_surface,
                source_mode="ui.contract.v2",
                inject_contract_mode=False,
            )
            if isinstance(governed, dict):
                source_contract.clear()
                source_contract.update(governed)
                source_contract["render_profile"] = normalized_render_profile
                if merged_context:
                    source_contract["context"] = dict(merged_context)
                    head = source_contract.get("head") if isinstance(source_contract.get("head"), dict) else {}
                    head = dict(head)
                    head["context"] = dict(merged_context)
                    source_contract["head"] = head
            if business_policy_fields:
                business_policy = source_contract.get("business_form_policy") if isinstance(source_contract.get("business_form_policy"), dict) else {}
                field_aliases = self._form_field_aliases(model, source_contract)
                if field_aliases and isinstance(business_policy_fields, list):
                    business_policy_fields = [
                        {**item, "name": self._resolve_form_field_alias(item.get("name") or item.get("field"), field_aliases)}
                        if isinstance(item, dict) and str(item.get("name") or item.get("field") or "").strip() in field_aliases
                        else item
                        for item in business_policy_fields
                    ]
                business_policy["fields"] = business_policy_fields
                source_contract["business_form_policy"] = business_policy
            if business_policy_groups:
                field_aliases = self._form_field_aliases(model, source_contract)
                if field_aliases and isinstance(source_contract.get("fields"), dict):
                    normalized_groups = []
                    for group in business_policy_groups:
                        if not isinstance(group, dict):
                            normalized_groups.append(group)
                            continue
                        copied = dict(group)
                        fields = []
                        for raw_name in group.get("fields") if isinstance(group.get("fields"), list) else []:
                            name = self._resolve_form_field_alias(str(raw_name or "").strip(), field_aliases)
                            if name and name not in fields:
                                fields.append(name)
                        copied["fields"] = fields
                        normalized_groups.append(copied)
                    business_policy_groups = normalized_groups
                source_contract["field_groups"] = business_policy_groups
                self._ensure_business_policy_layout_fields_visible(source_contract, business_policy_groups)
            self._inject_relation_entry_policies(source_contract, model=model)
            self._inject_business_category_form_structure(source_contract, model=model)
            self._sync_contract_original_contract_relation_to_v2_nodes(source_contract)
        except Exception:
            _logger.debug("ui.contract.v2 business category form policy injection skipped", exc_info=True)

    def _inject_relation_entry_policies(self, source_contract: dict[str, Any], *, model: str) -> None:
        fields = source_contract.get("fields") if isinstance(source_contract.get("fields"), dict) else {}
        context = source_contract.get("context") if isinstance(source_contract.get("context"), dict) else {}
        record = source_contract.get("record") if isinstance(source_contract.get("record"), dict) else {}
        for field_name, descriptor in list(fields.items()):
            if not isinstance(descriptor, dict):
                continue
            policy = call_extension_hook_first(
                self.env,
                "smart_core_relation_entry_policy",
                self.env,
                {
                    "model": model,
                    "field_name": field_name,
                    "relation": str(descriptor.get("relation") or "").strip(),
                    "descriptor": descriptor,
                    "context": context,
                    "record": record,
                },
            )
            if not isinstance(policy, dict):
                continue
            relation_entry = descriptor.get("relation_entry") if isinstance(descriptor.get("relation_entry"), dict) else {}
            relation_entry = dict(relation_entry)
            if isinstance(policy.get("domain"), list):
                relation_entry["domain"] = list(policy.get("domain") or [])
            if "can_create" in policy:
                relation_entry["can_create"] = bool(policy.get("can_create"))
            if "can_open" in policy:
                relation_entry["can_open"] = bool(policy.get("can_open"))
            if str(policy.get("create_mode") or "").strip():
                relation_entry["create_mode"] = str(policy.get("create_mode") or "").strip()
            if str(policy.get("order") or "").strip():
                relation_entry["order"] = str(policy.get("order") or "").strip()
            if str(policy.get("display_field") or "").strip():
                relation_entry["display_field"] = str(policy.get("display_field") or "").strip()
            if isinstance(policy.get("ui_labels"), dict):
                ui_labels = relation_entry.get("ui_labels") if isinstance(relation_entry.get("ui_labels"), dict) else {}
                relation_entry["ui_labels"] = {**ui_labels, **(policy.get("ui_labels") or {})}
            descriptor["relation_entry"] = relation_entry
        source_contract["fields"] = fields

    def _sync_contract_original_contract_relation_to_v2_nodes(self, source_contract: dict[str, Any]) -> None:
        fields = source_contract.get("fields") if isinstance(source_contract.get("fields"), dict) else {}
        descriptor = fields.get("original_contract_id") if isinstance(fields.get("original_contract_id"), dict) else {}
        relation_entry = descriptor.get("relation_entry") if isinstance(descriptor.get("relation_entry"), dict) else {}
        if not relation_entry:
            return
        v2 = source_contract.get("contract_v2") if isinstance(source_contract.get("contract_v2"), dict) else {}
        if not v2:
            v2 = source_contract.get("unifiedPageContractV2") if isinstance(source_contract.get("unifiedPageContractV2"), dict) else {}
        layout = v2.get("layoutContract") if isinstance(v2.get("layoutContract"), dict) else {}
        roots = layout.get("containerTree") if isinstance(layout.get("containerTree"), list) else []
        if not roots:
            return

        def is_original_node(node: dict[str, Any]) -> bool:
            return str(
                node.get("name")
                or node.get("field")
                or node.get("fieldCode")
                or node.get("widgetId")
                or ""
            ).strip() in {"original_contract_id", "field.original_contract_id"}

        def apply(node: dict[str, Any]) -> None:
            field_info = node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}
            field_info = {**field_info, "relation_entry": deepcopy(relation_entry)}
            node["fieldInfo"] = field_info
            node["field_info"] = field_info
            component_config = node.get("componentConfig") if isinstance(node.get("componentConfig"), dict) else {}
            component_config = {**component_config, "relationEntry": deepcopy(relation_entry)}
            node["componentConfig"] = component_config

        def walk(items: list[Any]) -> None:
            for item in items:
                if not isinstance(item, dict):
                    continue
                if is_original_node(item):
                    apply(item)
                for key in ("children", "tabs", "pages", "groups", "fields", "widgetList", "nodes", "items"):
                    child = item.get(key)
                    if isinstance(child, list):
                        walk(child)

        walk(roots)

    def _ensure_business_policy_layout_fields_visible(
        self,
        source_contract: dict[str, Any],
        business_policy_groups: list[dict[str, Any]],
    ) -> None:
        business_policy = source_contract.get("business_form_policy") if isinstance(source_contract.get("business_form_policy"), dict) else {}
        explicit_visibility_fields = set()
        field_policies = source_contract.get("field_policies") if isinstance(source_contract.get("field_policies"), dict) else {}
        for row in business_policy.get("fields") if isinstance(business_policy.get("fields"), list) else []:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or row.get("field") or "").strip()
            if not name:
                continue
            policy = field_policies.get(name) if isinstance(field_policies.get(name), dict) else {}
            for key in ("visible_profiles", "readonly_profiles", "required_profiles"):
                if isinstance(row.get(key), list):
                    policy[key] = list(row.get(key) or [])
            if policy:
                field_policies[name] = policy
            if isinstance(row.get("visible_profiles"), list):
                explicit_visibility_fields.add(name)
        for group in business_policy_groups:
            if not isinstance(group, dict):
                continue
            for raw_name in group.get("fields") if isinstance(group.get("fields"), list) else []:
                name = str(raw_name or "").strip()
                if not name or name in explicit_visibility_fields:
                    continue
                policy = field_policies.get(name) if isinstance(field_policies.get(name), dict) else {}
                policy["visible_profiles"] = ["create", "edit", "readonly"]
                field_policies[name] = policy
        source_contract["field_policies"] = field_policies

    def _inject_business_category_form_structure(self, source_contract: dict[str, Any], *, model: str) -> None:
        policy = source_contract.get("business_form_policy") if isinstance(source_contract.get("business_form_policy"), dict) else {}
        groups = source_contract.get("field_groups") if isinstance(source_contract.get("field_groups"), list) else []
        field_map = source_contract.get("fields") if isinstance(source_contract.get("fields"), dict) else {}
        if not policy or not groups or not field_map:
            return
        field_aliases = self._form_field_aliases(model, source_contract)
        if field_aliases:
            normalized_groups = []
            for group in groups:
                if not isinstance(group, dict):
                    normalized_groups.append(group)
                    continue
                copied = dict(group)
                fields = []
                for raw_name in group.get("fields") if isinstance(group.get("fields"), list) else []:
                    name = self._resolve_form_field_alias(str(raw_name or "").strip(), field_aliases)
                    if name and name not in fields:
                        fields.append(name)
                copied["fields"] = fields
                normalized_groups.append(copied)
            groups = normalized_groups
        field_policies = source_contract.get("field_policies") if isinstance(source_contract.get("field_policies"), dict) else {}
        render_profile = str(
            source_contract.get("render_profile")
            or policy.get("render_profile")
            or ""
        ).strip().lower()
        if render_profile in {"read", "view"}:
            render_profile = "readonly"
        if render_profile not in {"create", "edit", "readonly"}:
            render_profile = "edit"
        explicit_visible_profiles: dict[str, list[str]] = {}
        policy_field_labels = policy.get("field_labels") if isinstance(policy.get("field_labels"), dict) else {}
        for row in policy.get("fields") if isinstance(policy.get("fields"), list) else []:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or row.get("field") or "").strip()
            profiles = row.get("visible_profiles")
            if name and isinstance(profiles, list) and profiles:
                explicit_visible_profiles[name] = [str(item) for item in profiles]
            label = str(row.get("label") or row.get("string") or "").strip()
            if name and label:
                policy_field_labels[name] = label

        def field_visible_for_profile(name: str) -> bool:
            if name in explicit_visible_profiles:
                return render_profile in set(explicit_visible_profiles.get(name) or [])
            field_policy = field_policies.get(name) if isinstance(field_policies.get(name), dict) else {}
            visible_profiles = field_policy.get("visible_profiles")
            if isinstance(visible_profiles, list) and visible_profiles:
                return render_profile in {str(item) for item in visible_profiles}
            if isinstance(field_policy.get("visible"), bool):
                return bool(field_policy.get("visible"))
            return True

        slots: list[dict[str, Any]] = []
        field_roles: dict[str, dict[str, Any]] = {}
        source_titles: list[str] = []
        for index, group in enumerate(groups):
            if not isinstance(group, dict):
                continue
            group_visible_profiles = group.get("visible_profiles")
            if isinstance(group_visible_profiles, list) and group_visible_profiles:
                allowed_profiles = {str(item).strip().lower() for item in group_visible_profiles if str(item).strip()}
                if render_profile not in allowed_profiles:
                    continue
            group_name = str(group.get("name") or f"business_category_section_{index + 1}").strip()
            title = str(group.get("label") or group.get("title") or group_name).strip()
            field_refs: list[str] = []
            for raw_name in group.get("fields") if isinstance(group.get("fields"), list) else []:
                name = str(raw_name or "").strip()
                if not name or name not in field_map or name in field_refs:
                    continue
                if not field_visible_for_profile(name):
                    continue
                field_refs.append(name)
                field_roles.setdefault(name, {
                    "role": "business_fact",
                    "slot": group_name,
                    "group": group_name,
                })
            if not field_refs:
                continue
            if title:
                source_titles.append(title)
            slots.append({
                "slot": group_name,
                "title": title or group_name,
                "role": "business_category_section",
                "groups": [{
                    "name": group_name,
                    "title": title or group_name,
                    "role": "business_category_fields",
                    "fieldRefs": field_refs,
                    "fieldLabels": {
                        name: str(
                            policy_field_labels.get(name)
                            or (field_map.get(name) if isinstance(field_map.get(name), dict) else {}).get("string")
                            or (field_map.get(name) if isinstance(field_map.get(name), dict) else {}).get("label")
                            or name
                        ).strip()
                        for name in field_refs
                    },
                }],
            })
        if not slots:
            return
        source_contract["form_structure_contract"] = {
            "source": "ui.contract.v2.business_category_form_policy",
            "structureVersion": "1.0",
            "model": model,
            "viewType": "form",
            "mode": "business_category_task_form",
            "layoutPolicy": "category_sections_as_task_tabs",
            "objectProfile": {
                "model": model,
                "kind": "business_form",
                "factAuthority": "sc.business.category.form_policy_json",
            },
            "navigation": {
                "title": str(policy.get("category_name") or "业务办理").strip() or "业务办理",
            },
            "sourceSectionTitles": source_titles,
            "field_labels": {
                name: str(label or "").strip()
                for name, label in policy_field_labels.items()
                if str(name or "").strip() and str(label or "").strip()
            },
            "slots": slots,
            "fieldRoles": field_roles,
            "fieldPolicies": field_policies,
            "sourceAuthority": {
                "kind": self.SOURCE_KIND,
                "runtime_carrier": "ui.contract.v2.business_category_form_policy",
                "projection_only": True,
                "no_business_fact_authority": True,
                "governed_form_structure": True,
                "governance_source": {
                    "source": policy.get("source"),
                    "category_id": policy.get("category_id"),
                    "category_code": policy.get("category_code"),
                    "target_model": policy.get("target_model"),
                },
            },
        }

    def _inject_business_operation_contract(self, source_contract: dict[str, Any], *, model: str, view_type: str) -> None:
        if view_type == "form" and isinstance(source_contract.get("business_form_policy"), dict):
            return
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

        form_structure_field_labels: dict[str, str] = {}

        def field_label(name: str) -> str:
            field_name = str(name or "").strip()
            override = form_structure_field_labels.get(field_name)
            if override:
                return override
            meta = descriptor(field_name)
            label = str(meta.get("string") or getattr(model_fields.get(field_name), "string", "") or field_name).strip()
            if field_name == "source_created_by":
                return "录入人"
            if field_name == "source_created_at":
                return "录入时间"
            if field_name.startswith("p1_visible_") and label.startswith("P1可见"):
                label = label[len("P1可见"):].strip()
            label = self._legacy_visible_business_label(model, field_name, label)
            return label or field_name

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
            if isinstance(governed_field_names, list) and (
                governed_field_names
                or form_structure_governance.get("field_groups")
                or form_structure_governance.get("hidden_field_names")
            ):
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
        form_structure_field_labels.update(
            {
                str(key or "").strip(): str(value or "").strip()
                for key, value in (form_structure_governance.get("field_labels") or {}).items()
                if str(key or "").strip() and str(value or "").strip()
            }
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
        field_aliases = self._form_field_aliases(model, source_contract)
        if field_aliases:
            common_fields = unique([self._resolve_form_field_alias(name, field_aliases) for name in common_fields])

        amount_fields = [
            name
            for name in common_fields
            if field_type(name) in {"float", "integer", "monetary"} or "amount" in name
        ]
        alias_targets = [target for target in field_aliases.values() if has_field(target)]
        if alias_targets:
            amount_fields = unique([self._resolve_form_field_alias(name, field_aliases) for name in amount_fields] + alias_targets)
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
        elif view_type == "kanban":
            self._merge_business_kanban_profile(
                source_contract,
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
            if attachment_field:
                collaboration = source_contract.get("collaboration") if isinstance(source_contract.get("collaboration"), dict) else {}
                attachments = collaboration.get("attachments") if isinstance(collaboration.get("attachments"), dict) else {}
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
                collaboration["attachments"] = attachments
                source_contract["collaboration"] = collaboration

    def _merge_business_kanban_profile(
        self,
        source_contract: dict[str, Any],
        *,
        label_for,
        type_for,
    ) -> None:
        views = source_contract.get("views") if isinstance(source_contract.get("views"), dict) else {}
        kanban = views.get("kanban") if isinstance(views.get("kanban"), dict) else {}
        raw_rows = kanban.get("fields") if isinstance(kanban.get("fields"), list) else []
        model_name = str(
            source_contract.get("model")
            or ((source_contract.get("pageInfo") or {}).get("model") if isinstance(source_contract.get("pageInfo"), dict) else "")
            or ((source_contract.get("head") or {}).get("model") if isinstance(source_contract.get("head"), dict) else "")
            or ""
        ).strip()
        try:
            model_fields = getattr(self.env[model_name], "_fields", {}) if model_name and model_name in self.env else {}
        except Exception:
            model_fields = {}

        def normalize_row(row: Any) -> tuple[int, str, str, bool]:
            if isinstance(row, str):
                return 100, str(row or "").strip(), "", True
            if not isinstance(row, dict):
                return 100, "", "", True
            try:
                sequence = int(row.get("sequence") or row.get("order") or 100)
            except Exception:
                sequence = 100
            name = str(row.get("name") or row.get("field") or row.get("field_name") or "").strip()
            label = str(row.get("label") or row.get("string") or row.get("display_label") or "").strip()
            return sequence, name, label, row.get("visible") is not False

        direct_rows: list[tuple[int, str, str, bool]] = []
        if model_name and "ui.business.config.contract" in self.env:
            try:
                configs = self.env["ui.business.config.contract"]._effective_view_orchestration_contracts(
                    model_name,
                    view_type="kanban",
                    action_id=self._source_action_id(source_contract),
                )
            except Exception:
                configs = []
            for config in configs:
                payload = config.contract_json if isinstance(config.contract_json, dict) else {}
                orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
                cfg_views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
                spec = cfg_views.get("kanban") if isinstance(cfg_views.get("kanban"), dict) else {}
                rows = spec.get("fields") if isinstance(spec.get("fields"), list) else []
                direct_rows.extend(normalize_row(row) for row in rows)

        rows = direct_rows or [normalize_row(row) for row in raw_rows]
        if not rows:
            return
        hidden: set[str] = set()
        fields: list[str] = []
        labels: dict[str, str] = {}
        for _sequence, name, label, visible in sorted(rows, key=lambda item: (item[0], item[1])):
            if not name or (model_fields and name not in model_fields):
                continue
            if not visible:
                hidden.add(name)
                fields = [item for item in fields if item != name]
                labels.pop(name, None)
                continue
            if name in hidden:
                hidden.remove(name)
            if name not in fields:
                fields.append(name)
            if label:
                labels[name] = label
        if not fields and not labels:
            return

        existing_fields = []
        for row in raw_rows:
            _sequence, name, _label, visible = normalize_row(row)
            if name and visible and name not in hidden and name not in fields and (not model_fields or name in model_fields):
                existing_fields.append(name)
        fields.extend(existing_fields)
        labels = {name: labels.get(name) or label_for(name) for name in fields}

        fields_map = source_contract.get("fields") if isinstance(source_contract.get("fields"), dict) else {}
        fields_map = dict(fields_map)
        for name in fields:
            descriptor = fields_map.get(name) if isinstance(fields_map.get(name), dict) else {}
            descriptor = dict(descriptor)
            descriptor["name"] = descriptor.get("name") or name
            descriptor["string"] = labels.get(name) or label_for(name)
            descriptor["label"] = labels.get(name) or label_for(name)
            descriptor["type"] = descriptor.get("type") or type_for(name) or "char"
            fields_map[name] = descriptor
        source_contract["fields"] = fields_map

        kanban.update({
            "fields": [
                {
                    "name": name,
                    "label": labels.get(name) or label_for(name),
                    "string": labels.get(name) or label_for(name),
                    "type": type_for(name) or "char",
                }
                for name in fields
            ],
            "field_labels": labels,
        })
        views["kanban"] = kanban
        source_contract["views"] = views

        profile = source_contract.get("list_profile") if isinstance(source_contract.get("list_profile"), dict) else {}
        profile_labels = profile.get("column_labels") if isinstance(profile.get("column_labels"), dict) else {}
        profile["column_labels"] = {**profile_labels, **labels}
        source_contract["list_profile"] = profile

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
        form_layout_overlay = bool(view_trace.get("form_layout_overlay") or view_governance.get("form_layout_overlay"))
        field_names: list[str] = []
        field_labels: dict[str, str] = {}
        section_titles: list[str] = []
        field_groups: dict[str, list[str]] = {}
        group_columns: dict[str, int] = {}
        group_visibility: dict[str, bool] = {}
        form_columns = 0
        config_summaries: list[dict[str, Any]] = []

        def normalize_columns(value: Any) -> int:
            try:
                columns = int(value)
            except (TypeError, ValueError):
                return 0
            return columns if columns > 0 else 0

        def collect_layout_group_columns(nodes: Any) -> None:
            for item in nodes if isinstance(nodes, list) else []:
                if not isinstance(item, dict):
                    continue
                node_type = str(item.get("type") or item.get("kind") or "").strip().lower()
                title = str(item.get("string") or item.get("label") or item.get("title") or item.get("name") or "").strip()
                attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
                columns = (
                    normalize_columns(item.get("columns"))
                    or normalize_columns(item.get("cols"))
                    or normalize_columns(item.get("col"))
                    or normalize_columns(attrs.get("columns"))
                    or normalize_columns(attrs.get("cols"))
                    or normalize_columns(attrs.get("col"))
                )
                if node_type == "group" and title and columns:
                    group_columns[title] = columns
                for child_key in ("children", "pages", "tabs", "nodes", "items"):
                    collect_layout_group_columns(item.get(child_key))
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
            form_columns = normalize_columns(form_spec.get("columns")) or normalize_columns(form_spec.get("cols")) or form_columns
            if isinstance(form_spec.get("layout"), list) and form_spec.get("layout"):
                form_layout_overlay = True
                collect_layout_group_columns(form_spec.get("layout"))
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
                label = str(row.get("string") or row.get("label") or "").strip() if isinstance(row, dict) else ""
                if name and label:
                    field_labels[name] = label
            sections = form_spec.get("sections") if isinstance(form_spec.get("sections"), list) else []
            for row in sections:
                if isinstance(row, dict):
                    title = str(row.get("title") or row.get("label") or row.get("name") or "").strip()
                    fields = [
                        str(item or "").strip()
                        for item in (row.get("fields") if isinstance(row.get("fields"), list) else [])
                        if str(item or "").strip()
                    ]
                else:
                    title = str(row or "").strip()
                    fields = []
                if title and title not in section_titles:
                    section_titles.append(title)
                if title and isinstance(row, dict) and isinstance(row.get("visible"), bool):
                    group_visibility[title] = bool(row.get("visible"))
                    if row.get("visible") is False:
                        hidden_field_names.update(fields)
                        hidden_set = set(fields)
                        field_names = [item for item in field_names if item not in hidden_set]
                if title and fields:
                    existing = field_groups.setdefault(title, [])
                    for name in fields:
                        if name not in existing:
                            existing.append(name)
                    if isinstance(row, dict):
                        columns = normalize_columns(row.get("columns")) or normalize_columns(row.get("cols"))
                        if columns:
                            group_columns[title] = columns
        applied = bool(view_governance.get("applied") or business_contracts or legacy_overlay or field_names)
        if not applied:
            return {}
        return {
            "source": "business_view_orchestration",
            "owner_layer": str(view_trace.get("owner_layer") or view_governance.get("owner_layer") or "business_view_orchestration"),
            "business_config_contracts": [dict(item) for item in business_contracts if isinstance(item, dict)] or config_summaries,
            "legacy_field_policy_overlay": legacy_overlay,
            "form_layout_overlay": form_layout_overlay,
            "field_names": field_names,
            "field_labels": field_labels,
            "section_titles": section_titles,
            "field_groups": field_groups,
            "hidden_field_names": sorted(hidden_field_names),
            "form_columns": form_columns,
            "group_columns": group_columns,
            "group_visibility": group_visibility,
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

        configured_field_groups = (
            governance.get("field_groups")
            if isinstance(governance, dict) and isinstance(governance.get("field_groups"), dict)
            else {}
        )
        if configured_field_groups:
            group_rows: list[dict[str, Any]] = []
            configured_roles: dict[str, dict[str, Any]] = {}
            assigned_configured_fields: set[str] = set()

            for index, (raw_title, raw_fields) in enumerate(configured_field_groups.items(), start=1):
                title = str(raw_title or "").strip() or "业务配置字段"
                if not self._form_layout_group_visible_from_governance(governance, title):
                    continue
                names = [
                    str(item or "").strip()
                    for item in (raw_fields if isinstance(raw_fields, list) else [])
                    if str(item or "").strip()
                ]
                refs = [
                    name
                    for name in fields_for(names)
                    if name not in assigned_configured_fields
                ]
                if not refs:
                    continue
                assigned_configured_fields.update(refs)
                group_name = "configured_group_%s" % index
                for name in refs:
                    configured_roles[name] = {
                        "role": "configured_field",
                        "slot": "configured_form",
                        "group": group_name,
                    }
                row = {
                    "name": group_name,
                    "title": title,
                    "role": "configured_field_group",
                    "fieldRefs": refs,
                    "fieldLabels": {name: field_display_label(name) for name in refs},
                }
                columns = self._form_layout_columns_from_governance(governance, title)
                if columns:
                    row["cols"] = columns
                    row["columns"] = columns
                group_rows.append(row)
            if group_rows:
                form_columns = self._form_layout_columns_from_governance(governance)
                return {
                    "source": "ui.contract.v2.form_structure_contract",
                    "structureVersion": "1.0",
                    "model": model,
                    "viewType": "form",
                    **({"columns": form_columns} if form_columns > 0 else {}),
                    "mode": "business_task_form",
                    "layoutPolicy": "business_config_sections",
                    "objectProfile": {
                        "model": model,
                        "kind": "business_form",
                        "factAuthority": "business_object_model_and_view",
                    },
                    "navigation": {"title": "业务办理"},
                    "sourceSectionTitles": [row.get("title") for row in group_rows if row.get("title")],
                    "slots": [{
                        "slot": "configured_form",
                        "title": "表单字段",
                        "role": "configured_form",
                        "groups": group_rows,
                    }],
                    "fieldRoles": configured_roles,
                    "sourceAuthority": {
                        "kind": self.SOURCE_KIND,
                        "runtime_carrier": "ui.contract.v2.form_structure_contract",
                        "projection_only": True,
                        "no_business_fact_authority": True,
                        "governed_form_structure": True,
                        "governance_source": dict(governance or {}),
                    },
                }

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
        tree_schema_rows = tree.get("columns_schema") if isinstance(tree.get("columns_schema"), list) else []
        direct_orchestration_columns: list[str] = []
        direct_orchestration_labels: dict[str, str] = {}
        direct_orchestration_hidden: set[str] = set()
        model_name = str(
            source_contract.get("model")
            or ((source_contract.get("pageInfo") or {}).get("model") if isinstance(source_contract.get("pageInfo"), dict) else "")
            or ((source_contract.get("head") or {}).get("model") if isinstance(source_contract.get("head"), dict) else "")
            or ""
        ).strip()
        if model_name and "ui.business.config.contract" in self.env:
            try:
                view_ids = source_contract.get("view_ids_by_type") if isinstance(source_contract.get("view_ids_by_type"), dict) else {}
                direct_configs = self.env["ui.business.config.contract"]._effective_view_orchestration_contracts(
                    model_name,
                    view_type="tree",
                    action_id=self._source_action_id(source_contract),
                    view_id=view_ids.get("tree") or view_ids.get("list"),
                )
            except Exception:
                direct_configs = []
            for config in direct_configs:
                payload = config.contract_json if isinstance(config.contract_json, dict) else {}
                orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
                cfg_views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
                spec = cfg_views.get("tree") if isinstance(cfg_views.get("tree"), dict) else cfg_views.get("list")
                if not isinstance(spec, dict):
                    continue
                rows = spec.get("columns") if isinstance(spec.get("columns"), list) else spec.get("fields")
                if not isinstance(rows, list):
                    continue
                normalized_rows = []
                for index, row in enumerate(rows):
                    if isinstance(row, str):
                        name = str(row or "").strip()
                        label = ""
                        visible = True
                        sequence = 100
                    elif isinstance(row, dict):
                        name = str(row.get("name") or row.get("field") or row.get("field_name") or "").strip()
                        label = str(row.get("label") or row.get("string") or row.get("display_label") or "").strip()
                        visible = row.get("visible") is not False
                        try:
                            sequence = int(row.get("sequence") or row.get("order") or 100)
                        except Exception:
                            sequence = 100
                    else:
                        continue
                    if not name:
                        continue
                    normalized_rows.append((sequence, index, name, label, visible))
                for _sequence, _index, name, label, visible in sorted(normalized_rows, key=lambda item: (item[0], item[1])):
                    if not visible:
                        direct_orchestration_hidden.add(name)
                        direct_orchestration_columns = [item for item in direct_orchestration_columns if item != name]
                        continue
                    if name not in direct_orchestration_columns:
                        direct_orchestration_columns.append(name)
                    if label:
                        direct_orchestration_labels[name] = label
        governance = source_contract.get("governance") if isinstance(source_contract.get("governance"), dict) else {}
        view_governance = governance.get("view_orchestration") if isinstance(governance.get("view_orchestration"), dict) else {}
        source_trace = source_contract.get("source_trace") if isinstance(source_contract.get("source_trace"), dict) else {}
        view_trace = source_trace.get("view_orchestration") if isinstance(source_trace.get("view_orchestration"), dict) else {}
        business_view_orchestration_applied = bool(
            view_governance.get("applied")
            or view_governance.get("business_config_contracts")
            or view_trace.get("business_config_contracts")
            or direct_orchestration_columns
            or direct_orchestration_labels
        )
        action_view_override = None if business_view_orchestration_applied else self._action_scoped_visible_list_columns(source_contract)
        action_view_columns = list(action_view_override.get("columns") or []) if action_view_override else []
        action_view_labels = dict(action_view_override.get("column_labels") or {}) if action_view_override else {}
        legacy_view_columns = []
        for row in [*raw_columns, *tree_schema_rows]:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()
            if name.startswith("legacy_visible_") and name not in legacy_view_columns:
                legacy_view_columns.append(name)
        legacy_override = None if direct_orchestration_columns else self._scbs55_legacy_visible_list_override(source_contract)
        columns: list[str] = []
        explicit_view_columns: list[str] = []
        has_explicit_view_columns = False
        for row in raw_columns:
            name = str(row.get("name") if isinstance(row, dict) else row or "").strip()
            if name and name not in columns:
                columns.append(name)
                explicit_view_columns.append(name)
                has_explicit_view_columns = True
        if direct_orchestration_columns:
            columns = list(direct_orchestration_columns)
            explicit_view_columns = list(direct_orchestration_columns)
            has_explicit_view_columns = True
        profile = source_contract.get("list_profile") if isinstance(source_contract.get("list_profile"), dict) else {}
        if not direct_orchestration_columns:
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
        elif action_view_columns:
            columns = action_view_columns
            override_labels = dict(action_view_labels)
            strict_columns = True
        elif (
            legacy_view_columns
            and explicit_view_columns
            and all(name.startswith("legacy_visible_") for name in explicit_view_columns)
        ):
            columns = legacy_view_columns
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

        columns = self._user_visible_list_columns(columns)
        if not columns:
            return

        columns = self._merge_user_list_preference_columns(source_contract, columns)
        columns = self._user_visible_list_columns(columns)
        if not columns:
            return
        labels = profile.get("column_labels") if isinstance(profile.get("column_labels"), dict) else {}
        view_column_labels = {}
        for row in [*raw_columns, *tree_schema_rows]:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()
            if not name:
                continue
            if not business_view_orchestration_applied and not name.startswith("legacy_visible_"):
                continue
            label = str(row.get("label") or row.get("string") or "").strip()
            if label:
                view_column_labels[name] = label
        labels = {**{name: label_for(name) for name in columns}, **labels, **view_column_labels, **direct_orchestration_labels, **override_labels}
        labels = self._apply_legacy_visible_business_labels(source_contract, columns, labels)
        deduped_columns: list[str] = []
        preserve_duplicate_labels = bool(direct_orchestration_columns) or (
            bool(columns) and all(str(name or "").startswith("legacy_visible_") for name in columns)
        )
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
        fields_map = source_contract.get("fields") if isinstance(source_contract.get("fields"), dict) else {}
        if fields_map:
            fields_map = dict(fields_map)
            for name, label in labels.items():
                field = fields_map.get(name)
                if not isinstance(field, dict):
                    continue
                descriptor = dict(field)
                descriptor["string"] = label
                descriptor["label"] = label
                fields_map[name] = descriptor
            source_contract["fields"] = fields_map
        derived_status_field = str(profile.get("status_field") or status_field or "").strip()
        if not derived_status_field:
            derived_status_field = next(
                (
                    name
                    for name in columns
                    if any(token in str(name or "").lower() for token in ("state", "status"))
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
                "allow_visibility": True,
                "allow_order": True,
                "allow_width": True,
                "locked_columns": [],
                "must_request_columns": columns,
            },
        })
        if direct_orchestration_columns:
            profile["column_policy"] = {
                "mode": "strict",
                "reason": "business_list_config_contract_authoritative",
                "owner_layer": "ui.business.config.contract.view_orchestration",
            }
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
                    "string": labels.get(name) or label_for(name),
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

    def _source_action_id(self, source_contract: dict[str, Any]) -> int:
        for raw in (
            source_contract.get("action_id"),
            source_contract.get("actionId"),
            (source_contract.get("head") or {}).get("action_id") if isinstance(source_contract.get("head"), dict) else None,
            (source_contract.get("head") or {}).get("actionId") if isinstance(source_contract.get("head"), dict) else None,
            (source_contract.get("source_meta") or {}).get("action_id") if isinstance(source_contract.get("source_meta"), dict) else None,
        ):
            try:
                action_id = int(raw or 0)
            except Exception:
                action_id = 0
            if action_id > 0:
                return action_id
        return 0

    def _source_model_name(self, source_contract: dict[str, Any]) -> str:
        for raw in (
            source_contract.get("model"),
            source_contract.get("res_model"),
            (source_contract.get("head") or {}).get("model") if isinstance(source_contract.get("head"), dict) else None,
            (source_contract.get("head") or {}).get("res_model") if isinstance(source_contract.get("head"), dict) else None,
            (source_contract.get("source_meta") or {}).get("model") if isinstance(source_contract.get("source_meta"), dict) else None,
            (source_contract.get("source_meta") or {}).get("res_model") if isinstance(source_contract.get("source_meta"), dict) else None,
        ):
            model_name = str(raw or "").strip()
            if model_name:
                return model_name
        action_id = self._source_action_id(source_contract)
        if action_id > 0 and "ir.actions.act_window" in self.env:
            try:
                action = self.env["ir.actions.act_window"].sudo().browse(action_id).exists()
                return str(getattr(action, "res_model", "") or "").strip()
            except Exception:
                _logger.debug("ui.contract.v2 source model lookup skipped", exc_info=True)
        return ""

    def _action_scoped_visible_list_columns(self, source_contract: dict[str, Any]) -> dict[str, Any] | None:
        action_id = self._source_action_id(source_contract)
        if action_id <= 0:
            return None
        try:
            action = self.env["ir.actions.act_window"].sudo().browse(action_id).exists()
        except Exception:
            _logger.debug("ui.contract.v2 action-scoped visible list lookup skipped", exc_info=True)
            return None
        if not action:
            return None

        candidate_views = []
        try:
            if action.view_id and action.view_id.type in {"tree", "list"}:
                candidate_views.append(action.view_id)
        except Exception:
            pass
        try:
            for relation in action.view_ids:
                view = relation.view_id
                if view and view.type in {"tree", "list"} and view not in candidate_views:
                    candidate_views.append(view)
        except Exception:
            pass

        model_name = str(source_contract.get("model") or (source_contract.get("head") or {}).get("model") or "").strip()
        model_fields = {}
        try:
            model_fields = getattr(self.env[model_name], "_fields", {}) if model_name in self.env else {}
        except Exception:
            model_fields = {}

        for view in candidate_views:
            try:
                try:
                    arch = view.sudo().read_combined(["arch"]).get("arch") or ""
                except Exception:
                    arch = view.sudo().arch_db or ""
                if not arch:
                    continue
                root = etree.fromstring(arch.encode("utf-8"))
            except Exception:
                _logger.debug("ui.contract.v2 action-scoped visible list arch parse skipped", exc_info=True)
                continue
            columns: list[str] = []
            labels: dict[str, str] = {}
            for node in root.xpath(".//field"):
                name = str(node.get("name") or "").strip()
                if not name:
                    continue
                if not (name.startswith("p1_visible_") or name.startswith("legacy_visible_")):
                    continue
                if model_fields and name not in model_fields:
                    continue
                if name in columns:
                    continue
                columns.append(name)
                label = str(node.get("string") or "").strip()
                if label:
                    labels[name] = label
            if columns and all(name.startswith("p1_visible_") for name in columns):
                return {
                    "source": "ir.actions.act_window.tree_view",
                    "action_id": action_id,
                    "view_id": int(view.id),
                    "columns": columns,
                    "column_labels": labels,
                }
        return None

    def _scbs55_legacy_visible_list_override(self, source_contract: dict[str, Any]) -> dict[str, Any] | None:
        action_id = self._source_action_id(source_contract)
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

        collaboration = source_contract.get("collaboration") if isinstance(source_contract.get("collaboration"), dict) else {}
        chatter = collaboration.get("chatter") if isinstance(collaboration.get("chatter"), dict) else {}
        attachments = collaboration.get("attachments") if isinstance(collaboration.get("attachments"), dict) else {}
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

    def _inject_standard_submit_header_button(self, source_contract: dict[str, Any], *, model: str, view_type: str, render_profile: str = "", record_id: Any = None) -> None:
        try:
            has_model = bool(model and model in self.env)
        except Exception:
            return
        if view_type != "form" or not has_model:
            return
        profile = str(render_profile or source_contract.get("render_profile") or "").strip().lower()
        if profile in {"read", "view"}:
            profile = "readonly"
        record_id_int, _record_id_error = parse_positive_int(record_id, allow_empty=True)
        if profile == "create" and not record_id_int:
            return
        try:
            model_obj = self.env[model]
            if getattr(model_obj, "_transient", False):
                return
        except Exception:
            _logger.debug("ui.contract.v2 submit header injection skipped: model inspect failed", exc_info=True)
            return
        method = next(
            (
                name
                for name in ("action_submit", "action_submit_progress", "action_confirm", "button_confirm")
                if hasattr(model_obj, name)
            ),
            "",
        )
        if not method:
            return
        header_buttons = source_contract.get("header_buttons") if isinstance(source_contract.get("header_buttons"), list) else []
        for button in header_buttons:
            if not isinstance(button, dict):
                continue
            payload = button.get("payload") if isinstance(button.get("payload"), dict) else {}
            existing_method = str(button.get("name") or payload.get("method") or "").strip()
            if existing_method == method:
                source_contract["header_buttons"] = header_buttons
                return
        header_buttons.append({
            "name": method,
            "label": "提交",
            "kind": "object",
            "level": "header",
            "selection": "none",
            "visible_profiles": ["edit", "readonly"],
            "intent": "execute",
            "action_safety": {
                "classification": "danger",
                "requires_confirm": False,
                "confirm_message": "确认提交？",
                "reason_code": "STANDARD_SUBMIT_ACTION",
            },
            "payload": {
                "method": method,
                "type": "object",
                "url": "",
                "confirm": "",
                "groups_xmlids": [],
            },
            "source_authority": {
                "kind": "ui_contract_v2_standard_submit_projection",
                "authorities": ["odoo.model.method", "ir.model"],
                "projection_only": True,
                "rebuildable": True,
                "no_business_fact_authority": True,
                "runtime_carrier": "ui.contract.v2.standard_submit",
            },
        })
        source_contract["header_buttons"] = header_buttons

    def _inject_record_business_category_context(self, source_contract: dict[str, Any], *, model: str, record_id: Any) -> None:
        if not model:
            return
        try:
            model_available = model in self.env
        except Exception:
            return
        if not model_available:
            return
        record_id_int, _record_id_error = parse_positive_int(record_id, allow_empty=True)
        record_id_int = int(record_id_int or 0)
        if record_id_int <= 0:
            return
        Model = self.env[model]
        if "business_category_id" not in getattr(Model, "_fields", {}):
            return
        try:
            record = Model.browse(record_id_int).exists()
            category = record.business_category_id if record else None
        except Exception:
            _logger.debug("ui.contract.v2 business category context injection skipped", exc_info=True)
            return
        if not category:
            return
        code = str(getattr(category, "code", "") or "").strip()
        label = str(getattr(category, "name", "") or getattr(category, "display_name", "") or code).strip()
        if not code and not label:
            return
        context = source_contract.get("context") if isinstance(source_contract.get("context"), dict) else {}
        merged_context = dict(context)
        if code:
            merged_context.setdefault("current_business_category_code", code)
            merged_context.setdefault("default_business_category_code", code)
        if label:
            merged_context.setdefault("current_business_category_label", label)
            merged_context.setdefault("default_business_category_label", label)
        source_contract["context"] = merged_context
        head = source_contract.get("head") if isinstance(source_contract.get("head"), dict) else {}
        head = dict(head)
        head_context = head.get("context") if isinstance(head.get("context"), dict) else {}
        merged_head_context = dict(head_context)
        merged_head_context.update(merged_context)
        head["context"] = merged_head_context
        source_contract["head"] = head

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
        record_snapshot_fields = {
            "id",
            "display_name",
            "name",
            "document_no",
            "state",
            "company_id",
            "project_id",
            "business_category_id",
            "operation_strategy",
        }
        field_names = []
        for name in field_map.keys():
            field_name = str(name).strip()
            if not field_name:
                continue
            field = self.env[model]._fields.get(field_name) if model in self.env else None
            field_type = str(getattr(field, "type", "") or "")
            if field_name not in record_snapshot_fields and field_type in {"one2many", "many2many", "binary", "html"}:
                continue
            if field_name in record_snapshot_fields or len(field_names) < 80:
                field_names.append(field_name)
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

    def _inject_native_group_layout_columns(self, source_contract: dict[str, Any], *, view_type: str) -> None:
        if view_type != "form" or not isinstance(source_contract, dict):
            return
        views = source_contract.get("views") if isinstance(source_contract.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        layout = form.get("layout") if isinstance(form.get("layout"), list) else []
        if not layout:
            return
        meta = form.get("meta") if isinstance(form.get("meta"), dict) else {}
        projection = meta.get("projection_identity") if isinstance(meta.get("projection_identity"), dict) else {}
        trace = form.get("source_trace") if isinstance(form.get("source_trace"), dict) else {}
        orchestration = trace.get("view_orchestration") if isinstance(trace.get("view_orchestration"), dict) else {}
        raw_view_id = projection.get("source_view_id") or projection.get("view_id") or orchestration.get("view_id")
        try:
            view_id = int(raw_view_id or 0)
        except (TypeError, ValueError):
            view_id = 0
        if not view_id:
            return
        view = self.env["ir.ui.view"].sudo().browse(view_id).exists()
        if not view:
            return
        arch = str(view.arch_db or "")
        if not arch:
            return
        try:
            root = etree.fromstring(arch.encode("utf-8"))
        except Exception:
            _logger.debug("ui.contract.v2 native group column extraction skipped: invalid arch", exc_info=True)
            return

        def normalize_columns(value: Any) -> int | None:
            try:
                columns = int(value)
            except (TypeError, ValueError):
                return None
            return columns if columns > 0 else None

        def field_names(el: etree._Element) -> list[str]:
            names: list[str] = []
            for field in el.xpath(".//field[@name]"):
                name = str(field.get("name") or "").strip()
                if name and name not in names:
                    names.append(name)
            return names

        group_rows: list[dict[str, Any]] = []
        for group in root.xpath(".//group[@col]"):
            columns = normalize_columns(group.get("col"))
            if not columns:
                continue
            group_rows.append({
                "label": str(group.get("string") or group.get("name") or "").strip(),
                "fields": field_names(group),
                "cols": columns,
            })
        if not group_rows:
            return

        def dominant_group_columns() -> int | None:
            counts: dict[int, int] = {}
            for row in group_rows:
                columns = normalize_columns(row.get("cols"))
                if columns:
                    counts[columns] = counts.get(columns, 0) + 1
            if not counts:
                return None
            return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]

        def node_fields(node: dict[str, Any]) -> list[str]:
            names: list[str] = []

            def collect(value: Any) -> None:
                if isinstance(value, list):
                    for item in value:
                        collect(item)
                    return
                if not isinstance(value, dict):
                    return
                if str(value.get("type") or value.get("kind") or "").strip().lower() == "field":
                    name = str(value.get("name") or value.get("field") or "").strip()
                    if name and name not in names:
                        names.append(name)
                for key in ("children", "pages", "tabs", "nodes", "items", "groups", "fields"):
                    collect(value.get(key))

            collect(node.get("children"))
            return names

        def apply_columns(node: dict[str, Any]) -> None:
            node_type = str(node.get("type") or node.get("kind") or "").strip().lower()
            if node_type == "group" and not normalize_columns(node.get("cols")):
                label = str(node.get("string") or node.get("label") or node.get("title") or "").strip()
                fields = node_fields(node)
                match = next((row for row in group_rows if row.get("label") and row.get("label") == label), None)
                if not match and fields:
                    field_set = set(fields)
                    match = next((row for row in group_rows if row.get("fields") and set(row.get("fields") or []) == field_set), None)
                columns = match.get("cols") if match else dominant_group_columns()
                if columns:
                    node["cols"] = columns
                    node["columns"] = columns
                    attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
                    attrs["col"] = str(columns)
                    node["attributes"] = attrs
            for key in ("children", "pages", "tabs", "nodes", "items"):
                child_rows = node.get(key)
                if isinstance(child_rows, list):
                    for child in child_rows:
                        if isinstance(child, dict):
                            apply_columns(child)

        for row in layout:
            if isinstance(row, dict):
                apply_columns(row)

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
        if view_type == "list":
            ui_params["view_type"] = "tree"
            if "viewType" in ui_params:
                ui_params["viewType"] = "tree"
            view_type = "tree"
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


def _safe_eval_action_value(value: Any, default: Any) -> Any:
    if value in (None, False, ""):
        return default
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return default
    try:
        from odoo.tools.safe_eval import safe_eval

        return safe_eval(text)
    except Exception:
        try:
            return ast.literal_eval(text)
        except Exception:
            return default


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
                "label": "记录沟通",
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
