# -*- coding: utf-8 -*-
"""Runtime business view orchestration.

This service consumes existing business configuration contracts.  It does not
introduce a parallel profile/template model.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .view_orchestration_contract import source_authority_contract


class ViewOrchestrator:
    SOURCE_KIND = "business_view_orchestration"
    SOURCE_AUTHORITIES = ("ui.business.config.contract", "ui.form.field.policy", "odoo_native_view_parse_snapshot")
    NO_BUSINESS_FACT_AUTHORITY = True

    def __init__(self, env):
        self.env = env

    def compose(
        self,
        contract: dict | None,
        *,
        model_name: str,
        view_type: str,
        action_id: int | None = None,
        view_id: int | None = None,
        role_key: str | None = None,
        ctx: dict | None = None,
    ) -> dict:
        out = deepcopy(contract or {})
        if not model_name or not view_type:
            return out
        normalized_view_type = "tree" if view_type == "list" else str(view_type or "").strip()
        applied_contracts = []
        if "ui.business.config.contract" in self.env:
            configs = self.env["ui.business.config.contract"]._effective_view_orchestration_contracts(
                model_name,
                view_type=normalized_view_type,
                action_id=action_id,
                view_id=view_id,
                role_key=role_key,
            )
            for config in configs:
                before = deepcopy(out)
                out = self._apply_business_config_contract(out, config, normalized_view_type, model_name)
                if out != before:
                    applied_contracts.append({
                        "id": int(config.id),
                        "name": config.name,
                        "version_no": int(config.version_no or 1),
                    })

        # Compatibility: legacy form field policy remains an orchestration input
        # until low-code writes into ui.business.config.contract directly.
        legacy_policy_applied = False
        if normalized_view_type == "form" and "ui.form.field.policy" in self.env:
            before = deepcopy(out)
            out = self.env["ui.form.field.policy"].apply_to_view_contract(
                out,
                model_name=model_name,
                view_type=normalized_view_type,
                action_id=action_id,
                view_id=view_id,
            )
            legacy_policy_applied = out != before

        governance = out.get("governance") if isinstance(out.get("governance"), dict) else {}
        governance["view_orchestration"] = {
            "applied": bool(applied_contracts or legacy_policy_applied),
            "owner_layer": self.SOURCE_KIND,
            "source_authority": source_authority_contract(),
            "business_config_contracts": applied_contracts,
            "legacy_field_policy_overlay": bool(legacy_policy_applied),
        }
        out["governance"] = governance
        source_trace = out.get("source_trace") if isinstance(out.get("source_trace"), dict) else {}
        source_trace["view_orchestration"] = {
            "owner_layer": self.SOURCE_KIND,
            "model": model_name,
            "view_type": normalized_view_type,
            "action_id": int(action_id or 0),
            "view_id": int(view_id or 0),
            "business_config_contracts": applied_contracts,
            "legacy_field_policy_overlay": bool(legacy_policy_applied),
        }
        out["source_trace"] = source_trace
        return out

    def _apply_business_config_contract(self, contract: dict, config, view_type: str, model_name: str) -> dict:
        payload = config.contract_json if isinstance(config.contract_json, dict) else {}
        spec = self._view_spec(payload, view_type)
        if not spec:
            return contract
        spec = self._sanitize_spec_field_refs(spec, model_name)
        if not spec:
            return contract
        out = deepcopy(contract or {})
        if view_type == "form":
            return self._apply_form_spec(out, spec, model_name)
        if view_type in {"tree", "list"}:
            return self._apply_list_spec(out, spec)
        if view_type == "search":
            return self._apply_search_spec(out, spec)
        if view_type in {"pivot", "graph"}:
            return self._apply_analysis_spec(out, spec, view_type)
        return self._apply_generic_spec(out, spec, view_type)

    def _view_spec(self, payload: dict, view_type: str) -> dict:
        orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
        views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
        spec = views.get(view_type)
        if not isinstance(spec, dict) and view_type == "tree":
            spec = views.get("list")
        if isinstance(spec, dict):
            return spec
        legacy_layout = payload.get("layout") if isinstance(payload.get("layout"), dict) else {}
        legacy_spec = legacy_layout.get(view_type)
        return {"fields": legacy_spec} if isinstance(legacy_spec, list) else {}

    def _sanitize_spec_field_refs(self, spec: dict, model_name: str) -> dict:
        if model_name not in self.env:
            return spec
        model_fields = set(getattr(self.env[model_name], "_fields", {}) or {})
        if not model_fields:
            return spec
        out = deepcopy(spec)

        def simple_field(value) -> str:
            if not isinstance(value, str):
                return ""
            candidate = value.strip()
            if not candidate or "." in candidate or "(" in candidate or ")" in candidate or " " in candidate:
                return ""
            if not candidate.replace("_", "").isalnum():
                return ""
            return candidate

        def row_field(row) -> str:
            if isinstance(row, str):
                return simple_field(row)
            if not isinstance(row, dict):
                return ""
            for key in ("field", "name", "field_name"):
                if row.get(key):
                    return simple_field(row.get(key))
            return ""

        def row_known(row) -> bool:
            name = row_field(row)
            return bool(name and name in model_fields)

        def filter_field_rows(key: str) -> None:
            rows = out.get(key)
            if isinstance(rows, list):
                out[key] = [row for row in rows if row_known(row)]

        def filter_optional_field_rows(key: str) -> None:
            rows = out.get(key)
            if not isinstance(rows, list):
                return
            filtered = []
            for row in rows:
                if isinstance(row, str):
                    if row_known(row):
                        filtered.append(row)
                elif isinstance(row, dict):
                    field_name = simple_field(row.get("field"))
                    if field_name and field_name not in model_fields:
                        continue
                    filtered.append(row)
            out[key] = filtered

        def sanitize_slot_dict(key: str) -> None:
            value = out.get(key)
            if not isinstance(value, dict):
                return
            clean = {}
            for slot_key, slot_value in value.items():
                if isinstance(slot_value, str):
                    field_name = simple_field(slot_value)
                    if field_name and field_name in model_fields:
                        clean[slot_key] = slot_value
                elif isinstance(slot_value, list):
                    items = []
                    for item in slot_value:
                        if isinstance(item, str):
                            field_name = simple_field(item)
                            if field_name and field_name in model_fields:
                                items.append(item)
                        elif isinstance(item, dict):
                            field_name = row_field(item)
                            if not field_name or field_name in model_fields:
                                items.append(item)
                    if items:
                        clean[slot_key] = items
                elif isinstance(slot_value, dict):
                    field_name = row_field(slot_value)
                    if not field_name or field_name in model_fields:
                        clean[slot_key] = slot_value
            out[key] = clean

        for key in ("fields", "columns", "measures", "dimensions"):
            filter_field_rows(key)
        for key in ("filters", "group_by", "groupBys"):
            filter_optional_field_rows(key)
        for key in (
            "slots",
            "date_slots",
            "resource_slots",
            "color_slots",
            "dependency_slots",
            "activity_type_slots",
            "deadline_slots",
            "assignee_slots",
            "metric_slots",
            "chart_slots",
        ):
            sanitize_slot_dict(key)
        default_group_by = simple_field(out.get("default_group_by"))
        if default_group_by and default_group_by not in model_fields:
            out.pop("default_group_by", None)
        return out

    def _apply_form_spec(self, contract: dict, spec: dict, model_name: str) -> dict:
        self._apply_view_options(contract, spec, scalar_keys=("title",), dict_keys=("defaults", "context", "domain"))
        rows = self._normalized_rows(spec.get("fields") or spec.get("field_slots"))
        if rows:
            fields_meta = self.env[model_name].fields_get() if model_name in self.env else {}
            effective = {row["name"]: row for row in rows if row.get("name") in fields_meta}
            if effective:
                hidden = {name for name, row in effective.items() if row.get("visible") is False}
                layout = contract.get("layout")
                if isinstance(layout, list):
                    contract["layout"] = self._apply_node_field_rules(layout, effective, hidden)
                    self._sort_form_field_nodes(contract["layout"], effective)
                    self._append_missing_form_fields(contract["layout"], effective, fields_meta)
                field_modifiers = contract.get("field_modifiers")
                if isinstance(field_modifiers, dict):
                    for name in hidden:
                        field_modifiers.pop(name, None)
                    contract["field_modifiers"] = field_modifiers
        self._apply_action_slots(contract, spec, default_key="header_buttons")
        return contract

    def _apply_list_spec(self, contract: dict, spec: dict) -> dict:
        self._apply_view_options(
            contract,
            spec,
            scalar_keys=("order", "default_order", "page_size"),
            list_keys=("row_classes",),
            dict_keys=("defaults", "context", "domain"),
        )
        rows = self._normalized_rows(spec.get("columns") or spec.get("fields"))
        if not rows:
            return contract
        visible_names = [row["name"] for row in rows if row.get("visible") is not False]
        if visible_names:
            existing = contract.get("columns")
            if isinstance(existing, list):
                existing_names = [self._column_name(row) for row in existing]
                tail = [name for name in existing_names if name and name not in set(row["name"] for row in rows)]
                contract["columns"] = visible_names + tail
            else:
                contract["columns"] = visible_names
        schema = contract.get("columns_schema")
        if isinstance(schema, list):
            by_name = {self._column_name(row): dict(row) for row in schema if self._column_name(row)}
            hidden_names = {row["name"] for row in rows if row.get("visible") is False}
            ordered = []
            for row in rows:
                if row.get("visible") is False:
                    continue
                col = by_name.get(row["name"], {"name": row["name"]})
                self._apply_column_display_policy(col, row)
                ordered.append(col)
            used = {self._column_name(row) for row in ordered}
            ordered.extend(
                dict(row)
                for row in schema
                if self._column_name(row) not in used and self._column_name(row) not in hidden_names
            )
            contract["columns_schema"] = ordered
        self._apply_action_slots(contract, spec, default_key="row_actions")
        return contract

    def _apply_search_spec(self, contract: dict, spec: dict) -> dict:
        search = contract.get("search") if isinstance(contract.get("search"), dict) else {}
        self._apply_view_options(search, spec, dict_keys=("defaults", "context", "domain"))
        filters = spec.get("filters")
        group_by = spec.get("group_by") or spec.get("groupBys")
        if isinstance(filters, list):
            search["filters"] = [dict(row) for row in filters if isinstance(row, dict)]
        if isinstance(group_by, list):
            search["group_by"] = [dict(row) for row in group_by if isinstance(row, dict)]
        self._apply_action_slots(search, spec, default_key="actions")
        contract["search"] = search
        return contract

    def _apply_analysis_spec(self, contract: dict, spec: dict, view_type: str) -> dict:
        key = "pivot" if view_type == "pivot" else "graph"
        node = contract.get(key) if isinstance(contract.get(key), dict) else {}
        self._apply_view_options(node, spec, scalar_keys=("order",), dict_keys=("context", "domain"))
        for target_key in ("measures", "dimensions", "defaults", "chart_policy"):
            value = spec.get(target_key)
            if isinstance(value, (list, dict)):
                node[target_key] = deepcopy(value)
        self._apply_action_slots(node, spec, default_key="actions")
        contract[key] = node
        return contract

    def _apply_generic_spec(self, contract: dict, spec: dict, view_type: str) -> dict:
        node = contract.get(view_type) if isinstance(contract.get(view_type), dict) else {}
        self._apply_view_options(
            node,
            spec,
            scalar_keys=("title", "default_group_by", "page_size", "quick_create"),
            list_keys=("cards", "kpis", "row_classes"),
            dict_keys=("defaults", "context", "domain"),
        )
        for key in (
            "slots",
            "date_slots",
            "resource_slots",
            "color_slots",
            "dependency_slots",
            "activity_type_slots",
            "deadline_slots",
            "assignee_slots",
            "metric_slots",
            "chart_slots",
            "navigation_slots",
        ):
            value = spec.get(key)
            if isinstance(value, dict):
                node[key] = deepcopy(value)
        for key in ("actions", "quick_actions"):
            value = spec.get(key)
            if isinstance(value, list):
                node[key] = [dict(row) for row in value if isinstance(row, dict)]
        if node:
            contract[view_type] = node
        return contract

    def _apply_view_options(
        self,
        node: dict,
        spec: dict,
        *,
        scalar_keys: tuple[str, ...] = (),
        list_keys: tuple[str, ...] = (),
        dict_keys: tuple[str, ...] = (),
    ) -> None:
        for key in scalar_keys:
            value = spec.get(key)
            if isinstance(value, (str, int, float, bool)) and value != "":
                node[key] = value
        for key in list_keys:
            value = spec.get(key)
            if isinstance(value, list):
                node[key] = deepcopy(value)
        for key in dict_keys:
            value = spec.get(key)
            if isinstance(value, dict):
                node[key] = deepcopy(value)

    def _apply_action_slots(self, node: dict, spec: dict, *, default_key: str) -> None:
        actions = spec.get("actions")
        if isinstance(actions, list):
            node[default_key] = [dict(row) for row in actions if isinstance(row, dict)]
        action_slots = spec.get("action_slots")
        if isinstance(action_slots, dict):
            for key, value in action_slots.items():
                if isinstance(value, list):
                    node[str(key)] = [dict(row) for row in value if isinstance(row, dict)]

    def _normalized_rows(self, rows: Any) -> list[dict[str, Any]]:
        if not isinstance(rows, list):
            return []
        normalized = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or row.get("field") or row.get("field_name") or "").strip()
            if not name:
                continue
            visible = row.get("visible")
            if isinstance(visible, str):
                visible = visible.strip().lower() not in {"0", "false", "no", "hide", "hidden"}
            normalized.append({
                "name": name,
                "label": str(row.get("label") or row.get("string") or row.get("display_label") or "").strip(),
                "visible": visible if isinstance(visible, bool) else None,
                "sequence": int(row.get("sequence") or row.get("order") or 100),
                "readonly": self._optional_bool(row.get("readonly")),
                "required": self._optional_bool(row.get("required")),
                "help": str(row.get("help") or "").strip(),
                "widget": str(row.get("widget") or "").strip(),
                "width": str(row.get("width") or "").strip(),
                "class": str(row.get("class") or row.get("className") or "").strip(),
            })
        return sorted(normalized, key=lambda item: (item["sequence"], item["name"]))

    def _optional_bool(self, raw: Any):
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, str):
            value = raw.strip().lower()
            if value in {"1", "true", "yes", "on", "required", "readonly"}:
                return True
            if value in {"0", "false", "no", "off"}:
                return False
        return None

    def _apply_field_display_policy(self, node: dict, policy: dict) -> None:
        label = policy.get("label")
        if label:
            node["string"] = label
            node["label"] = label
        for key in ("readonly", "required"):
            if isinstance(policy.get(key), bool):
                node[key] = bool(policy[key])
        for key in ("help", "widget", "class"):
            if policy.get(key):
                node[key] = policy[key]
        field_info = node.get("fieldInfo")
        if isinstance(field_info, dict):
            if label:
                field_info["label"] = label
                field_info["string"] = label
            for key in ("readonly", "required"):
                if isinstance(policy.get(key), bool):
                    field_info[key] = bool(policy[key])
            for key in ("help", "widget"):
                if policy.get(key):
                    field_info[key] = policy[key]

    def _apply_column_display_policy(self, col: dict, policy: dict) -> None:
        label = policy.get("label")
        if label:
            col["label"] = label
            col["string"] = label
        for key in ("readonly", "required"):
            if isinstance(policy.get(key), bool):
                col[key] = bool(policy[key])
        for key in ("help", "widget", "width", "class"):
            if policy.get(key):
                col[key] = policy[key]

    def _apply_node_field_rules(self, nodes: list, effective: dict[str, dict[str, Any]], hidden: set[str]) -> list:
        result = []
        for raw in nodes:
            if not isinstance(raw, dict):
                continue
            node = dict(raw)
            if str(node.get("type") or "").strip().lower() == "field":
                name = str(node.get("name") or "").strip()
                if name in hidden:
                    continue
                if name in effective:
                    self._apply_field_display_policy(node, effective[name])
            for child_key in ("children", "pages", "tabs", "nodes", "items"):
                children = node.get(child_key)
                if isinstance(children, list):
                    node[child_key] = self._apply_node_field_rules(children, effective, hidden)
            result.append(node)
        return result

    def _sort_form_field_nodes(self, nodes: list, effective: dict[str, dict[str, Any]]) -> None:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            for child_key in ("children", "pages", "tabs", "nodes", "items"):
                children = node.get(child_key)
                if isinstance(children, list):
                    self._sort_form_field_nodes(children, effective)
        nodes.sort(key=lambda node: self._node_sort_key(node, effective))

    def _append_missing_form_fields(self, layout: list, effective: dict[str, dict[str, Any]], fields_meta: dict) -> None:
        existing = set()

        def collect(nodes: list) -> None:
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                if str(node.get("type") or "").strip().lower() == "field":
                    name = str(node.get("name") or "").strip()
                    if name:
                        existing.add(name)
                for key in ("children", "pages", "tabs", "nodes", "items"):
                    children = node.get(key)
                    if isinstance(children, list):
                        collect(children)

        collect(layout)
        missing = [name for name, row in effective.items() if row.get("visible") is not False and name not in existing]
        if not missing:
            return
        target = self._find_sheet(layout)
        parent = target.setdefault("children", []) if target is not None else layout
        parent.append({
            "type": "group",
            "name": "business_config_orchestration_fields",
            "children": [
                {
                    "type": "field",
                    "name": name,
                    "fieldInfo": {
                        "name": name,
                        "label": effective[name].get("label") or fields_meta.get(name, {}).get("string") or name,
                        "type": fields_meta.get(name, {}).get("type") or "char",
                    },
                    **({"string": effective[name]["label"], "label": effective[name]["label"]} if effective[name].get("label") else {}),
                    **({"readonly": bool(effective[name]["readonly"])} if isinstance(effective[name].get("readonly"), bool) else {}),
                    **({"required": bool(effective[name]["required"])} if isinstance(effective[name].get("required"), bool) else {}),
                    **({"help": effective[name]["help"]} if effective[name].get("help") else {}),
                    **({"widget": effective[name]["widget"]} if effective[name].get("widget") else {}),
                    **({"class": effective[name]["class"]} if effective[name].get("class") else {}),
                }
                for name in sorted(missing, key=lambda value: (effective[value].get("sequence") or 100, value))
            ],
        })

    def _find_sheet(self, nodes: list) -> dict | None:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if str(node.get("type") or "").strip().lower() == "sheet":
                return node
            for key in ("children", "pages", "tabs", "nodes", "items"):
                children = node.get(key)
                if isinstance(children, list):
                    found = self._find_sheet(children)
                    if found is not None:
                        return found
        return None

    def _node_sort_key(self, node: dict, effective: dict[str, dict[str, Any]]) -> tuple[int, str]:
        if isinstance(node, dict) and str(node.get("type") or "").strip().lower() == "field":
            name = str(node.get("name") or "").strip()
            if name in effective:
                return int(effective[name].get("sequence") or 100), name
        return 10000, str(node.get("name") or node.get("type") or "")

    def _column_name(self, row: Any) -> str:
        if isinstance(row, str):
            return row
        if isinstance(row, dict):
            return str(row.get("name") or row.get("field") or "").strip()
        return ""
