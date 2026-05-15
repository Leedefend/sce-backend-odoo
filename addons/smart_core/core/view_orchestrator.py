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
        return out

    def _apply_business_config_contract(self, contract: dict, config, view_type: str, model_name: str) -> dict:
        payload = config.contract_json if isinstance(config.contract_json, dict) else {}
        spec = self._view_spec(payload, view_type)
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

    def _apply_form_spec(self, contract: dict, spec: dict, model_name: str) -> dict:
        rows = self._normalized_rows(spec.get("fields") or spec.get("field_slots"))
        if not rows:
            return contract
        fields_meta = self.env[model_name].fields_get() if model_name in self.env else {}
        effective = {row["name"]: row for row in rows if row.get("name") in fields_meta}
        if not effective:
            return contract
        hidden = {name for name, row in effective.items() if row.get("visible") is False}
        layout = contract.get("layout")
        if isinstance(layout, list):
            contract["layout"] = self._apply_node_field_rules(layout, effective, hidden)
            self._append_missing_form_fields(contract["layout"], effective, fields_meta)
        field_modifiers = contract.get("field_modifiers")
        if isinstance(field_modifiers, dict):
            for name in hidden:
                field_modifiers.pop(name, None)
            contract["field_modifiers"] = field_modifiers
        return contract

    def _apply_list_spec(self, contract: dict, spec: dict) -> dict:
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
                if row.get("label"):
                    col["label"] = row["label"]
                    col["string"] = row["label"]
                ordered.append(col)
            used = {self._column_name(row) for row in ordered}
            ordered.extend(
                dict(row)
                for row in schema
                if self._column_name(row) not in used and self._column_name(row) not in hidden_names
            )
            contract["columns_schema"] = ordered
        return contract

    def _apply_search_spec(self, contract: dict, spec: dict) -> dict:
        search = contract.get("search") if isinstance(contract.get("search"), dict) else {}
        filters = spec.get("filters")
        group_by = spec.get("group_by") or spec.get("groupBys")
        if isinstance(filters, list):
            search["filters"] = [dict(row) for row in filters if isinstance(row, dict)]
        if isinstance(group_by, list):
            search["group_by"] = [dict(row) for row in group_by if isinstance(row, dict)]
        contract["search"] = search
        return contract

    def _apply_analysis_spec(self, contract: dict, spec: dict, view_type: str) -> dict:
        key = "pivot" if view_type == "pivot" else "graph"
        node = contract.get(key) if isinstance(contract.get(key), dict) else {}
        for target_key in ("measures", "dimensions", "defaults"):
            value = spec.get(target_key)
            if isinstance(value, (list, dict)):
                node[target_key] = deepcopy(value)
        contract[key] = node
        return contract

    def _apply_generic_spec(self, contract: dict, spec: dict, view_type: str) -> dict:
        node = contract.get(view_type) if isinstance(contract.get(view_type), dict) else {}
        slots = spec.get("slots")
        if isinstance(slots, dict):
            node["slots"] = deepcopy(slots)
        actions = spec.get("actions")
        if isinstance(actions, list):
            node["actions"] = [dict(row) for row in actions if isinstance(row, dict)]
        if node:
            contract[view_type] = node
        return contract

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
            })
        return sorted(normalized, key=lambda item: (item["sequence"], item["name"]))

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
                    label = effective[name].get("label")
                    if label:
                        node["string"] = label
                        node["label"] = label
                        field_info = node.get("fieldInfo")
                        if isinstance(field_info, dict):
                            field_info["label"] = label
            for child_key in ("children", "pages", "tabs", "nodes", "items"):
                children = node.get(child_key)
                if isinstance(children, list):
                    node[child_key] = self._apply_node_field_rules(children, effective, hidden)
                    node[child_key].sort(key=lambda child: self._node_sort_key(child, effective))
            result.append(node)
        return result

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
