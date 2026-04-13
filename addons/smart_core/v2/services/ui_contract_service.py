from __future__ import annotations

import importlib
from typing import Any, Dict

from ..contracts.results import UIContractResultV2


class UIContractServiceV2:
    @staticmethod
    def _resolve_render_profile(payload: Dict[str, Any]) -> str:
        value = str(
            (payload or {}).get("render_profile")
            or (payload or {}).get("renderProfile")
            or (payload or {}).get("profile")
            or (payload or {}).get("mode")
            or ""
        ).strip().lower()
        if value in {"read", "view"}:
            value = "readonly"
        if value in {"create", "edit", "readonly"}:
            return value
        record_id = int((payload or {}).get("record_id") or 0)
        return "edit" if record_id > 0 else "create"

    @staticmethod
    def _apply_render_profile(contract_data: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(contract_data, dict):
            return {}
        profile = UIContractServiceV2._resolve_render_profile(payload if isinstance(payload, dict) else {})
        contract_data["render_profile"] = profile

        permissions = contract_data.get("permissions") if isinstance(contract_data.get("permissions"), dict) else {}
        effective = permissions.get("effective") if isinstance(permissions.get("effective"), dict) else {}
        rights = effective.get("rights") if isinstance(effective.get("rights"), dict) else {}
        fields_meta = contract_data.get("fields") if isinstance(contract_data.get("fields"), dict) else {}

        if profile == "readonly":
            rights["create"] = False
            rights["write"] = False
            rights["unlink"] = False
            for meta in fields_meta.values():
                if isinstance(meta, dict):
                    meta["readonly"] = True
        elif profile == "create":
            rights["create"] = True
            rights["write"] = False
            rights["unlink"] = False
            contract_data.pop("res_id", None)
            head = contract_data.get("head") if isinstance(contract_data.get("head"), dict) else {}
            if isinstance(head, dict):
                head.pop("res_id", None)
                contract_data["head"] = head

        effective["rights"] = rights
        effective["render_profile"] = profile
        permissions["effective"] = effective
        contract_data["permissions"] = permissions
        contract_data["fields"] = fields_meta
        return contract_data

    @staticmethod
    def _build_render_surfaces(contract_data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(contract_data, dict):
            return {}
        fields_meta = contract_data.get("fields") if isinstance(contract_data.get("fields"), dict) else {}
        views = contract_data.get("views") if isinstance(contract_data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        subviews = form.get("subviews") if isinstance(form.get("subviews"), dict) else {}

        header_buttons = [row for row in (form.get("header_buttons") if isinstance(form.get("header_buttons"), list) else []) if isinstance(row, dict)]
        stat_buttons = [row for row in (form.get("stat_buttons") if isinstance(form.get("stat_buttons"), list) else []) if isinstance(row, dict)]
        button_box = [row for row in (form.get("button_box") if isinstance(form.get("button_box"), list) else []) if isinstance(row, dict)]

        create_fields: list[str] = []
        edit_fields: list[str] = []
        readonly_fields: list[str] = []
        for name, meta in fields_meta.items():
            if not isinstance(meta, dict):
                continue
            field_name = str(name or "").strip()
            if not field_name:
                continue
            is_readonly = bool(meta.get("readonly", False))
            create_fields.append(field_name)
            edit_fields.append(field_name)
            readonly_fields.append(field_name)
            if is_readonly:
                continue

        create_actions = [
            row for row in header_buttons
            if str((row.get("name") or "")).strip().lower() not in {"action_sc_submit"}
        ]
        edit_actions = list(header_buttons)
        readonly_actions: list[Dict[str, Any]] = []

        def _project_subviews(mode: str) -> Dict[str, Any]:
            out: Dict[str, Any] = {}
            for field_name, node in subviews.items():
                if not isinstance(node, dict):
                    continue
                policies = node.get("policies") if isinstance(node.get("policies"), dict) else {}
                next_policies = dict(policies)
                if mode == "readonly":
                    next_policies["can_create"] = False
                    next_policies["can_unlink"] = False
                    next_policies["inline_edit"] = False
                elif mode == "create":
                    next_policies.setdefault("can_create", True)
                    next_policies.setdefault("can_unlink", False)
                    next_policies.setdefault("inline_edit", True)
                else:
                    next_policies.setdefault("can_create", True)
                    next_policies.setdefault("can_unlink", True)
                    next_policies.setdefault("inline_edit", True)
                out[field_name] = {
                    "relation_model": str(node.get("relation_model") or ""),
                    "policies": next_policies,
                }
            return out

        contract_data["render_surfaces"] = {
            "create": {
                "field_names": sorted(set(create_fields)),
                "readonly": False,
                "actions": {
                    "header_buttons": create_actions,
                    "button_box": [],
                    "stat_buttons": [],
                },
                "subviews": _project_subviews("create"),
            },
            "edit": {
                "field_names": sorted(set(edit_fields)),
                "readonly": False,
                "actions": {
                    "header_buttons": edit_actions,
                    "button_box": button_box,
                    "stat_buttons": stat_buttons,
                },
                "subviews": _project_subviews("edit"),
            },
            "readonly": {
                "field_names": sorted(set(readonly_fields)),
                "readonly": True,
                "actions": {
                    "header_buttons": readonly_actions,
                    "button_box": [],
                    "stat_buttons": stat_buttons,
                },
                "subviews": _project_subviews("readonly"),
            },
        }
        return contract_data

    @staticmethod
    def _iter_layout_nodes(node):
        if isinstance(node, dict):
            yield node
            for key in ("children", "tabs", "pages", "nodes", "items"):
                children = node.get(key)
                if isinstance(children, list):
                    for child in children:
                        yield from UIContractServiceV2._iter_layout_nodes(child)
            return
        if isinstance(node, list):
            for item in node:
                yield from UIContractServiceV2._iter_layout_nodes(item)

    @staticmethod
    def _canonical_field_type(meta: Dict[str, Any]) -> str:
        return str(meta.get("type") or meta.get("ttype") or "").strip().lower()

    @staticmethod
    def _canonical_widget_by_type(field_type: str) -> str:
        mapping = {
            "many2one": "many2one",
            "one2many": "one2many_list",
            "many2many": "many2many_tags",
            "boolean": "boolean",
            "date": "date",
            "datetime": "datetime",
            "text": "textarea",
            "html": "html",
            "binary": "image",
        }
        ftype = str(field_type or "").strip().lower()
        return mapping.get(ftype, ftype)

    @staticmethod
    def _sync_form_layout_field_info(contract_data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(contract_data, dict):
            return {}
        fields_meta = contract_data.get("fields") if isinstance(contract_data.get("fields"), dict) else {}
        views = contract_data.get("views") if isinstance(contract_data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        layout = form.get("layout")
        if not fields_meta or not isinstance(layout, (list, dict)):
            return contract_data

        for node in UIContractServiceV2._iter_layout_nodes(layout):
            if str(node.get("type") or "").strip().lower() != "field":
                continue
            field_name = str(node.get("name") or "").strip()
            if not field_name:
                continue
            canonical = fields_meta.get(field_name)
            if not isinstance(canonical, dict):
                continue

            info = node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}
            canonical_type = UIContractServiceV2._canonical_field_type(canonical)
            next_info: Dict[str, Any] = {"name": field_name}
            for key in ("label", "widget", "colspan", "modifiers"):
                value = info.get(key)
                if key == "label" and isinstance(value, str) and value.strip():
                    next_info[key] = value.strip()
                elif key == "widget" and isinstance(value, str) and value.strip():
                    next_info[key] = value.strip()
                elif key == "colspan" and value is not None:
                    next_info[key] = value
                elif key == "modifiers" and isinstance(value, dict):
                    next_info[key] = value

            canonical_label = str(canonical.get("string") or field_name)
            current_label = str(next_info.get("label") or "").strip()
            if (not current_label) or current_label == field_name:
                next_info["label"] = canonical_label

            current_widget = str(next_info.get("widget") or "").strip().lower()
            canonical_widget = str(canonical.get("widget") or UIContractServiceV2._canonical_widget_by_type(canonical_type) or "")
            needs_widget_fix = not current_widget
            if canonical_type in {"many2one", "one2many", "many2many"} and current_widget in {"", "char", "text", "input"}:
                needs_widget_fix = True
            if canonical_type in {"html", "boolean", "selection"} and current_widget in {"", "char", "text", "input"}:
                needs_widget_fix = True
            if needs_widget_fix and canonical_widget:
                next_info["widget"] = canonical_widget

            node["fieldInfo"] = next_info
        return contract_data

    @staticmethod
    def _normalize_form_structure_semantics(contract_data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(contract_data, dict):
            return {}
        views = contract_data.get("views") if isinstance(contract_data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        if not form:
            return contract_data

        for key in ("header_buttons", "button_box", "stat_buttons"):
            value = form.get(key)
            if isinstance(value, list):
                continue
            if isinstance(value, dict):
                form[key] = [item for item in value.values() if isinstance(item, dict)]
            else:
                form[key] = []

        layout = form.get("layout")
        group_index = 1
        for node in UIContractServiceV2._iter_layout_nodes(layout):
            node_type = str(node.get("type") or "").strip().lower()
            if node_type == "group":
                label = str(node.get("label") or "").strip()
                synthetic = label.startswith("信息分组")
                inferred = UIContractServiceV2._infer_group_semantic_label(node)
                normalized_existing = UIContractServiceV2._normalize_group_label(
                    label,
                    UIContractServiceV2._collect_group_field_names(node),
                ) if label else ""
                if normalized_existing and normalized_existing != label:
                    node["label"] = normalized_existing
                elif inferred and ((not label) or synthetic):
                    node["label"] = inferred
                elif not label:
                    node["label"] = f"信息分组{group_index}"
                    group_index += 1
                continue

            if node_type == "page":
                title = str(
                    node.get("title")
                    or node.get("label")
                    or node.get("name")
                    or (node.get("attributes") or {}).get("string")
                    or ""
                ).strip()
                if title:
                    node["title"] = title
                    if not str(node.get("label") or "").strip():
                        node["label"] = title
                continue

            if node_type == "notebook":
                tabs = node.get("tabs") if isinstance(node.get("tabs"), list) else []
                pages = node.get("pages") if isinstance(node.get("pages"), list) else []
                children = node.get("children") if isinstance(node.get("children"), list) else []
                page_children = [
                    row for row in children
                    if isinstance(row, dict) and str(row.get("type") or "").strip().lower() == "page"
                ]
                derived_tabs = tabs or pages or page_children
                normalized_tabs = [row for row in derived_tabs if isinstance(row, dict)]
                node["tabs"] = normalized_tabs
                node["pages"] = list(normalized_tabs)
                notebook_label = str(
                    node.get("label")
                    or node.get("title")
                    or node.get("name")
                    or (node.get("attributes") or {}).get("string")
                    or ""
                ).strip()
                if (not notebook_label) and normalized_tabs:
                    first_tab = normalized_tabs[0] if isinstance(normalized_tabs[0], dict) else {}
                    notebook_label = str(
                        first_tab.get("title")
                        or first_tab.get("label")
                        or first_tab.get("name")
                        or ""
                    ).strip()
                if notebook_label:
                    node["label"] = notebook_label
                if page_children:
                    node["children"] = [
                        row for row in children
                        if not (isinstance(row, dict) and str(row.get("type") or "").strip().lower() == "page")
                    ]
                continue

            if node_type == "button":
                button_label = str(node.get("label") or "").strip()
                if not button_label:
                    button_label = str(
                        node.get("name")
                        or (node.get("attributes") or {}).get("string")
                        or (node.get("attributes") or {}).get("title")
                        or "动作"
                    ).strip()
                    node["label"] = button_label

        views["form"] = form
        contract_data["views"] = views

        semantic_page = contract_data.get("semantic_page") if isinstance(contract_data.get("semantic_page"), dict) else {}
        form_semantics = semantic_page.get("form_semantics") if isinstance(semantic_page.get("form_semantics"), dict) else {}
        form_semantics.pop("layout", None)
        form_semantics["layout_source"] = "views.form.layout"
        if isinstance(layout, list):
            form_semantics["layout_section_count"] = len(layout)
        elif isinstance(layout, dict):
            form_semantics["layout_section_count"] = 1
        semantic_page["form_semantics"] = form_semantics
        contract_data["semantic_page"] = semantic_page
        return contract_data

    @staticmethod
    def _fill_statusbar_states_from_selection(contract_data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(contract_data, dict):
            return {}
        views = contract_data.get("views") if isinstance(contract_data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        statusbar = form.get("statusbar") if isinstance(form.get("statusbar"), dict) else {}
        field_name = str(statusbar.get("field") or "").strip()
        if not field_name:
            return contract_data

        states = statusbar.get("states") if isinstance(statusbar.get("states"), list) else []
        if states:
            if not str(statusbar.get("states_source") or "").strip():
                statusbar["states_source"] = "view.statusbar"
            form["statusbar"] = statusbar
            views["form"] = form
            contract_data["views"] = views
            return contract_data

        fields = contract_data.get("fields") if isinstance(contract_data.get("fields"), dict) else {}
        field_meta = fields.get(field_name) if isinstance(fields.get(field_name), dict) else {}
        selection = field_meta.get("selection") if isinstance(field_meta.get("selection"), list) else []
        out_states = []
        for index, item in enumerate(selection):
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                value = str(item[0] or "").strip()
                label = str(item[1] or value).strip()
            elif isinstance(item, dict):
                value = str(item.get("value") or item.get("key") or "").strip()
                label = str(item.get("label") or value).strip()
            else:
                continue
            if not value:
                continue
            out_states.append({"value": value, "label": label or value, "sequence": index + 1})

        if out_states:
            statusbar["states"] = out_states
            statusbar["states_source"] = "fields.selection"
            if not str(statusbar.get("label") or "").strip():
                statusbar["label"] = str(field_meta.get("string") or field_name)
            statusbar.pop("states_reason", None)
        else:
            statusbar["states"] = []
            statusbar["states_source"] = "unresolved"
            statusbar["states_reason"] = "selection_not_available"

        form["statusbar"] = statusbar
        views["form"] = form
        contract_data["views"] = views
        return contract_data

    @staticmethod
    def _infer_group_semantic_label(node: Dict[str, Any]) -> str:
        item = node if isinstance(node, dict) else {}
        field_names = UIContractServiceV2._collect_group_field_names(item)
        attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
        for key in ("string", "title", "name"):
            value = str(item.get(key) or attrs.get(key) or "").strip()
            if value and not value.startswith("信息分组"):
                return UIContractServiceV2._normalize_group_label(value, field_names)

        children = item.get("children") if isinstance(item.get("children"), list) else []
        for child in children:
            if not isinstance(child, dict):
                continue
            child_type = str(child.get("type") or "").strip().lower()
            if child_type != "separator":
                continue
            child_attrs = child.get("attributes") if isinstance(child.get("attributes"), dict) else {}
            sep_title = str(
                child.get("label")
                or child.get("title")
                or child.get("name")
                or child_attrs.get("string")
                or ""
            ).strip()
            if sep_title:
                return UIContractServiceV2._normalize_group_label(sep_title, field_names)

        for child in children:
            if not isinstance(child, dict):
                continue
            child_type = str(child.get("type") or "").strip().lower()
            if child_type == "field":
                info = child.get("fieldInfo") if isinstance(child.get("fieldInfo"), dict) else {}
                field_label = str(info.get("label") or "").strip()
                if field_label:
                    return UIContractServiceV2._normalize_group_label(field_label, field_names)
            if child_type == "group":
                sub_label = str(child.get("label") or "").strip()
                if sub_label and not sub_label.startswith("信息分组"):
                    return UIContractServiceV2._normalize_group_label(sub_label, field_names)
        return ""

    @staticmethod
    def _collect_group_field_names(node: Dict[str, Any]) -> list[str]:
        out: list[str] = []

        def walk(item: Any) -> None:
            if not isinstance(item, dict):
                return
            node_type = str(item.get("type") or "").strip().lower()
            if node_type == "field":
                name = str(item.get("name") or "").strip()
                if name and name not in out:
                    out.append(name)
            for key in ("children", "tabs", "pages", "nodes", "items"):
                rows = item.get(key)
                if isinstance(rows, list):
                    for row in rows:
                        walk(row)

        walk(node)
        return out

    @staticmethod
    def _normalize_group_label(label: str, field_names: list[str]) -> str:
        raw = str(label or "").strip()
        if not raw:
            return raw

        fields = {str(name or "").strip() for name in (field_names or []) if str(name or "").strip()}
        weak_literals = {
            "任务名称", "名称", "name", "Name", "Name of the Tasks",
            "已启用", "Active", "active",
        }
        if raw in weak_literals:
            if {"name", "partner_id", "company_id"} & fields:
                return "主体信息"
            if {"active", "user_id", "date_start", "date"} & fields:
                return "管理信息"
            if {"project_id", "project_manager_id"} & fields:
                return "项目归属"
            return "基本信息"

        normalized_map = {
            "Visibility": "可见性",
            "Accept Emails From": "接收邮件来自",
            "Tasks": "任务",
            "Time Management": "时间管理",
            "Analytics": "分析",
        }
        return normalized_map.get(raw, raw)

    @staticmethod
    def _action_identity(action: Dict[str, Any]) -> str:
        row = action if isinstance(action, dict) else {}
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        name = str(row.get("name") or "").strip()
        method = str(payload.get("method") or "").strip()
        action_id = payload.get("action_id")
        ref = str(payload.get("ref") or payload.get("xml_id") or "").strip()
        if name or method or ref or action_id not in (None, ""):
            return f"name:{name}|method:{method}|action_id:{action_id}|ref:{ref}"
        for key in ("xml_id", "key", "id"):
            value = row.get(key)
            if value not in (None, ""):
                return f"{key}:{value}"
        label = str(row.get("label") or row.get("string") or "").strip()
        return f"label:{label}" if label else "unknown"

    @staticmethod
    def _canonicalize_action_row(action: Dict[str, Any], canonical: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        row = dict(action or {})
        key = UIContractServiceV2._action_identity(row)
        source = canonical.get(key) if isinstance(canonical.get(key), dict) else {}
        if source:
            merged = dict(source)
            merged.update(row)
            payload_src = source.get("payload") if isinstance(source.get("payload"), dict) else {}
            payload_row = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            if payload_src or payload_row:
                payload = dict(payload_src)
                payload.update(payload_row)
                merged["payload"] = payload
            row = merged
        label = str(row.get("label") or row.get("string") or "").strip()
        if label:
            row["label"] = label
        return row

    @staticmethod
    def _dedupe_action_rows(rows: Any) -> list[Dict[str, Any]]:
        out: list[Dict[str, Any]] = []
        seen: set[str] = set()
        for item in (rows if isinstance(rows, list) else []):
            if not isinstance(item, dict):
                continue
            key = UIContractServiceV2._action_identity(item)
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        return out

    @staticmethod
    def _normalize_text(value: Any) -> str:
        return str(value or "").strip().lower()

    @staticmethod
    def _field_token_index(fields_meta: Dict[str, Any]) -> tuple[set[str], set[str]]:
        relation_names: set[str] = set()
        relation_labels: set[str] = set()
        for field_name, meta in (fields_meta or {}).items():
            if not isinstance(meta, dict):
                continue
            field_type = str(meta.get("type") or meta.get("ttype") or "").strip().lower()
            if field_type not in {"one2many", "many2many"}:
                continue
            name = str(field_name or "").strip().lower()
            if not name:
                continue
            relation_names.add(name)
            if name.endswith("_ids") and len(name) > 4:
                relation_names.add(name[:-4])
            label = str(meta.get("string") or "").strip().lower()
            if label:
                relation_labels.add(label)
        return relation_names, relation_labels

    @staticmethod
    def _looks_like_stat_button(action: Dict[str, Any], relation_names: set[str], relation_labels: set[str]) -> bool:
        row = action if isinstance(action, dict) else {}
        attrs = row.get("attributes") if isinstance(row.get("attributes"), dict) else {}
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}

        class_tokens = UIContractServiceV2._normalize_text(
            row.get("class")
            or attrs.get("class")
            or attrs.get("className")
            or attrs.get("classes")
        )
        widget = UIContractServiceV2._normalize_text(
            row.get("widget")
            or attrs.get("widget")
            or payload.get("widget")
        )
        stat_field = UIContractServiceV2._normalize_text(
            row.get("stat_field")
            or attrs.get("stat_field")
            or attrs.get("data-stat-field")
            or payload.get("stat_field")
        )
        if "oe_stat_button" in class_tokens or widget in {"statinfo", "stat_info", "stat"} or stat_field:
            return True

        name = UIContractServiceV2._normalize_text(row.get("name") or payload.get("method") or "")
        label = UIContractServiceV2._normalize_text(row.get("label") or row.get("string") or attrs.get("string") or "")
        merged = f"{name} {label}"

        if name.startswith("action_view_"):
            return True
        if any(token and token in merged for token in relation_names):
            return True
        if label and label in relation_labels:
            return True
        return False

    @staticmethod
    def _build_stat_button_payload(action: Dict[str, Any], relation_names: set[str]) -> Dict[str, Any]:
        row = dict(action or {})
        attrs = row.get("attributes") if isinstance(row.get("attributes"), dict) else {}
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}

        name = str(row.get("name") or payload.get("method") or "").strip()
        label = str(row.get("label") or row.get("string") or attrs.get("string") or name or "统计按钮").strip()
        clickable = bool(row.get("visible", True) is not False)
        stat_field = str(
            row.get("stat_field")
            or attrs.get("stat_field")
            or attrs.get("data-stat-field")
            or payload.get("stat_field")
            or ""
        ).strip()
        if not stat_field:
            lower_name = name.lower()
            for token in sorted(relation_names, key=len, reverse=True):
                if not token or token.endswith("_ids"):
                    continue
                if token in lower_name:
                    stat_field = f"{token}_count"
                    break

        row["label"] = label
        row["clickable"] = clickable
        row["payload"] = payload
        row["stat_field"] = stat_field
        row["widget"] = str(row.get("widget") or "statinfo").strip()
        return row

    @staticmethod
    def _dedupe_form_action_surfaces(contract_data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(contract_data, dict):
            return {}
        views = contract_data.get("views") if isinstance(contract_data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        if not form:
            return contract_data

        fields_meta = contract_data.get("fields") if isinstance(contract_data.get("fields"), dict) else {}
        relation_names, relation_labels = UIContractServiceV2._field_token_index(fields_meta)

        top_buttons = UIContractServiceV2._dedupe_action_rows(contract_data.get("buttons"))
        header_buttons = UIContractServiceV2._dedupe_action_rows(form.get("header_buttons"))
        raw_button_box = UIContractServiceV2._dedupe_action_rows(form.get("button_box"))
        raw_stat_buttons = UIContractServiceV2._dedupe_action_rows(form.get("stat_buttons"))

        canonical: Dict[str, Dict[str, Any]] = {}
        for row in top_buttons + header_buttons + raw_button_box + raw_stat_buttons:
            key = UIContractServiceV2._action_identity(row)
            if key not in canonical:
                canonical[key] = dict(row)

        header_buttons = [UIContractServiceV2._canonicalize_action_row(row, canonical) for row in header_buttons]
        raw_button_box = [UIContractServiceV2._canonicalize_action_row(row, canonical) for row in raw_button_box]
        raw_stat_buttons = [UIContractServiceV2._canonicalize_action_row(row, canonical) for row in raw_stat_buttons]

        stat_buttons: list[Dict[str, Any]] = []
        button_box: list[Dict[str, Any]] = []

        for item in raw_button_box:
            if UIContractServiceV2._looks_like_stat_button(item, relation_names, relation_labels):
                stat_buttons.append(UIContractServiceV2._build_stat_button_payload(item, relation_names))
            else:
                button_box.append(item)

        for item in raw_stat_buttons:
            stat_buttons.append(UIContractServiceV2._build_stat_button_payload(item, relation_names))

        stat_buttons = UIContractServiceV2._dedupe_action_rows(stat_buttons)
        stat_keys = {UIContractServiceV2._action_identity(item) for item in stat_buttons}
        if stat_keys:
            button_box = [
                item for item in button_box
                if UIContractServiceV2._action_identity(item) not in stat_keys
            ]

        form["button_box"] = button_box
        form["stat_buttons"] = stat_buttons
        form["header_buttons"] = UIContractServiceV2._dedupe_action_rows(header_buttons)
        views["form"] = form
        contract_data["views"] = views

        action_groups = contract_data.get("action_groups")
        if isinstance(action_groups, list):
            normalized_groups: list[Dict[str, Any]] = []
            seen_group_actions: set[str] = set()
            for group in action_groups:
                if not isinstance(group, dict):
                    continue
                actions = group.get("actions") if isinstance(group.get("actions"), list) else []
                next_actions: list[Dict[str, Any]] = []
                for action in actions:
                    if not isinstance(action, dict):
                        continue
                    row = UIContractServiceV2._canonicalize_action_row(action, canonical)
                    key = UIContractServiceV2._action_identity(row)
                    if key in seen_group_actions:
                        continue
                    seen_group_actions.add(key)
                    next_actions.append(row)
                next_group = dict(group)
                next_group["actions"] = next_actions
                normalized_groups.append(next_group)
            contract_data["action_groups"] = normalized_groups

        return contract_data

    @staticmethod
    def _fill_chatter_attachment_surface(contract_data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(contract_data, dict):
            return {}
        fields_meta = contract_data.get("fields") if isinstance(contract_data.get("fields"), dict) else {}
        views = contract_data.get("views") if isinstance(contract_data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        if not form:
            return contract_data

        layout = form.get("layout")
        has_chatter_node = False
        has_attachment_node = False
        for node in UIContractServiceV2._iter_layout_nodes(layout):
            node_type = str(node.get("type") or "").strip().lower()
            attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
            css_class = str(attrs.get("class") or "")
            field_info = node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}
            widget = str(
                node.get("widget")
                or field_info.get("widget")
                or attrs.get("widget")
                or ""
            ).strip().lower()
            if (
                node_type in {"chatter", "mail_thread", "mail_activity"}
                or widget in {"mail_thread", "mail_activity", "mail_followers"}
                or "oe_chatter" in css_class
            ):
                has_chatter_node = True
            if widget in {"many2many_binary", "binary"} or "oe_attachment_box" in css_class:
                has_attachment_node = True

        chatter_markers = {"message_ids", "message_follower_ids", "activity_ids", "activity_state", "message_main_attachment_id"}
        attachment_markers = {"message_main_attachment_id", "attachment_ids"}
        has_chatter_fields = any(name in fields_meta for name in chatter_markers)
        has_attachment_fields = any(name in fields_meta for name in attachment_markers)

        chatter = form.get("chatter") if isinstance(form.get("chatter"), dict) else {}
        attachments = form.get("attachments") if isinstance(form.get("attachments"), dict) else {}

        chatter_enabled = bool(chatter.get("enabled", False)) or has_chatter_node or has_chatter_fields
        attachment_enabled = bool(attachments.get("enabled", False)) or has_attachment_node or has_attachment_fields or chatter_enabled

        chatter["enabled"] = chatter_enabled
        if chatter_enabled:
            chatter["source"] = "layout_or_model_features"
            chatter.pop("reason", None)
        else:
            chatter["source"] = "model_features"
            chatter["reason"] = "mail_features_not_available"

        attachments["enabled"] = attachment_enabled
        if attachment_enabled:
            attachments["source"] = "model_features"
            attachments.pop("reason", None)
        else:
            attachments["source"] = "model_features"
            attachments["reason"] = "attachment_features_not_available"

        form["chatter"] = chatter
        form["attachments"] = attachments
        views["form"] = form
        contract_data["views"] = views
        return contract_data

    @staticmethod
    def _infer_relation_tree_columns(env: Any, relation_model: str) -> list[str]:
        model = str(relation_model or "").strip()
        if not model:
            return ["display_name"]
        relation_fields: Dict[str, Any] = {}
        try:
            relation_fields = env[model].sudo().fields_get() if env is not None else {}
        except Exception:
            relation_fields = {}
        if not isinstance(relation_fields, dict) or not relation_fields:
            return ["display_name"]

        preferred = ["name", "display_name", "stage_id", "state", "user_id"]
        selected = [field for field in preferred if field in relation_fields]
        if not selected:
            selected = [field for field in relation_fields.keys() if not str(field).startswith("_")][:3]
        if "display_name" not in selected and "display_name" in relation_fields:
            selected.insert(0, "display_name")
        return selected[:6] or ["display_name"]

    @staticmethod
    def _infer_relation_fields_meta(env: Any, relation_model: str, columns: list[str]) -> Dict[str, Any]:
        model = str(relation_model or "").strip()
        if not model:
            return {}
        relation_fields: Dict[str, Any] = {}
        try:
            relation_fields = env[model].sudo().fields_get() if env is not None else {}
        except Exception:
            relation_fields = {}
        if not isinstance(relation_fields, dict) or not relation_fields:
            return {}

        out: Dict[str, Any] = {}
        for name in [str(col or "").strip() for col in (columns or []) if str(col or "").strip()]:
            meta = relation_fields.get(name)
            if not isinstance(meta, dict):
                continue
            item: Dict[str, Any] = {
                "type": str(meta.get("type") or ""),
                "label": str(meta.get("string") or name),
                "required": bool(meta.get("required", False)),
                "readonly": bool(meta.get("readonly", False)),
            }
            relation = str(meta.get("relation") or "").strip()
            if relation:
                item["relation"] = relation
            selection = meta.get("selection")
            if isinstance(selection, list) and selection:
                item["selection"] = selection
            out[name] = item
        return out

    @staticmethod
    def _ensure_form_x2many_subviews(contract_data: Dict[str, Any], env: Any) -> Dict[str, Any]:
        if not isinstance(contract_data, dict):
            return {}
        fields_meta = contract_data.get("fields") if isinstance(contract_data.get("fields"), dict) else {}
        if not fields_meta:
            return contract_data

        views = contract_data.get("views") if isinstance(contract_data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        if not form:
            return contract_data

        subviews = form.get("subviews") if isinstance(form.get("subviews"), dict) else {}
        for field_name, meta in fields_meta.items():
            if not isinstance(meta, dict):
                continue
            field_type = str(meta.get("type") or meta.get("ttype") or "").strip().lower()
            if field_type not in {"one2many", "many2many"}:
                continue

            relation = str(meta.get("relation") or meta.get("comodel_name") or "").strip()
            current = subviews.get(field_name) if isinstance(subviews.get(field_name), dict) else {}
            tree_cfg = current.get("tree") if isinstance(current.get("tree"), dict) else {}
            columns = tree_cfg.get("columns") if isinstance(tree_cfg.get("columns"), list) else []
            if not columns:
                tree_cfg["columns"] = UIContractServiceV2._infer_relation_tree_columns(env, relation)
            columns = tree_cfg.get("columns") if isinstance(tree_cfg.get("columns"), list) else []

            policies = current.get("policies") if isinstance(current.get("policies"), dict) else {}
            policies.setdefault("inline_edit", True)
            policies.setdefault("can_create", True)
            policies.setdefault("can_unlink", True)
            policies.setdefault("can_open", True)

            fields_map = current.get("fields") if isinstance(current.get("fields"), dict) else {}
            inferred_fields = UIContractServiceV2._infer_relation_fields_meta(env, relation, columns)
            for col, meta_item in inferred_fields.items():
                if not isinstance(meta_item, dict):
                    continue
                existing = fields_map.get(col) if isinstance(fields_map.get(col), dict) else {}
                next_meta = dict(existing)
                for key, value in meta_item.items():
                    if key not in next_meta or next_meta.get(key) in (None, "", []):
                        next_meta[key] = value
                fields_map[col] = next_meta

            current["tree"] = tree_cfg
            current["fields"] = fields_map
            current["relation_model"] = relation
            current.setdefault("entry", {"default": "list", "can_open": True})
            current["policies"] = policies
            subviews[field_name] = current

        form["subviews"] = subviews
        views["form"] = form
        contract_data["views"] = views
        return contract_data

    @staticmethod
    def _resolve_odoo_request():
        try:
            http_mod = importlib.import_module("odoo.http")
            return getattr(http_mod, "request", None)
        except Exception:
            return None

    @staticmethod
    def _build_fallback_contract(*, payload: Dict[str, Any], model: str, view_type: str, contract_surface: str, source_mode: str) -> Dict[str, Any]:
        fields = {
            "id": {"type": "integer", "readonly": True},
            "name": {"type": "char", "readonly": False},
        }
        if model == "project.project":
            fields.update(
                {
                    "project_code": {"type": "char", "readonly": True},
                    "state": {"type": "selection", "readonly": False},
                }
            )
        form_layout = {
            "type": "group",
            "children": [
                {"type": "field", "name": "name"},
            ],
        }
        if "project_code" in fields:
            form_layout["children"].append({"type": "field", "name": "project_code"})

        contract = {
            "model": model,
            "view_type": "tree" if view_type == "list" else view_type,
            "fields": fields,
            "views": {
                "form": {
                    "layout": form_layout,
                    "header_buttons": [],
                    "stat_buttons": [],
                },
                "list": {
                    "columns": ["id", "name"],
                },
            },
            "semantic_page": {
                "form_semantics": {
                    "layout_source": "views.form.layout",
                    "layout_section_count": 1,
                }
            },
            "contract_mode": "user",
            "contract_surface": contract_surface,
            "render_mode": "native" if contract_surface == "native" else "governed",
            "source_mode": source_mode,
            "governed_from_native": contract_surface != "native",
            "surface_mapping": {
                "native_to_governed": {
                    "fields": {"native_count": len(fields), "governed_count": len(fields), "removed": [], "added": [], "reordered": False}
                }
            },
        }
        return contract

    @staticmethod
    def _build_runtime_contract(*, payload: Dict[str, Any], contract_surface: str, source_mode: str) -> Dict[str, Any]:
        request_obj = UIContractServiceV2._resolve_odoo_request()
        if request_obj is None or getattr(request_obj, "env", None) is None:
            raise RuntimeError("odoo request context unavailable")

        odoo_mod = importlib.import_module("odoo")
        api_mod = getattr(odoo_mod, "api")
        super_uid = int(getattr(odoo_mod, "SUPERUSER_ID"))

        dispatch_mod = importlib.import_module("odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher")
        governance_mod = importlib.import_module("odoo.addons.smart_core.utils.contract_governance")
        action_dispatcher_cls = getattr(dispatch_mod, "ActionDispatcher")
        apply_governance = getattr(governance_mod, "apply_contract_governance")

        runtime_ctx = dict(request_obj.env.context or {})
        runtime_env = api_mod.Environment(request_obj.env.cr, request_obj.env.user.id, runtime_ctx)
        runtime_su_env = api_mod.Environment(request_obj.env.cr, super_uid, runtime_ctx)

        op = str((payload or {}).get("op") or "model").strip().lower() or "model"
        view_type = str((payload or {}).get("view_type") or "form").strip().lower() or "form"
        if op == "action_open":
            dispatch_payload = {
                "subject": "action",
                "action_id": int((payload or {}).get("action_id") or 0),
                "view_type": view_type,
                "record_id": int((payload or {}).get("record_id") or 0) or None,
                "source_mode": source_mode,
            }
        else:
            dispatch_payload = {
                "subject": "model",
                "model": str((payload or {}).get("model") or "").strip(),
                "view_type": view_type,
                "record_id": int((payload or {}).get("record_id") or 0) or None,
                "source_mode": source_mode,
            }

        contract_data, _versions = action_dispatcher_cls(runtime_env, runtime_su_env).dispatch(dispatch_payload)
        contract_data = UIContractServiceV2._sync_form_layout_field_info(
            contract_data if isinstance(contract_data, dict) else {}
        )
        contract_data = UIContractServiceV2._normalize_form_structure_semantics(
            contract_data if isinstance(contract_data, dict) else {}
        )
        contract_data = UIContractServiceV2._fill_statusbar_states_from_selection(
            contract_data if isinstance(contract_data, dict) else {}
        )
        contract_data = UIContractServiceV2._dedupe_form_action_surfaces(contract_data)
        contract_data = UIContractServiceV2._fill_chatter_attachment_surface(
            contract_data if isinstance(contract_data, dict) else {}
        )
        contract_data = UIContractServiceV2._ensure_form_x2many_subviews(contract_data, runtime_env)
        contract_data = apply_governance(
            contract_data if isinstance(contract_data, dict) else {},
            "user",
            contract_surface=contract_surface,
            source_mode=source_mode,
            inject_contract_mode=True,
        )
        contract_data = UIContractServiceV2._normalize_form_structure_semantics(
            contract_data if isinstance(contract_data, dict) else {}
        )
        contract_data = UIContractServiceV2._apply_render_profile(
            contract_data if isinstance(contract_data, dict) else {},
            payload if isinstance(payload, dict) else {},
        )
        contract_data = UIContractServiceV2._build_render_surfaces(
            contract_data if isinstance(contract_data, dict) else {}
        )
        return contract_data if isinstance(contract_data, dict) else {}

    def _resolve_model(self, payload: Dict[str, Any]) -> str:
        explicit_model = str((payload or {}).get("model") or "").strip()
        if explicit_model:
            return explicit_model

        action_id = int((payload or {}).get("action_id") or 0)
        if action_id <= 0:
            return ""

        request_obj = self._resolve_odoo_request()
        if request_obj is None or getattr(request_obj, "env", None) is None:
            return ""
        try:
            action = request_obj.env["ir.actions.act_window"].sudo().browse(action_id)
            if action.exists():
                return str(action.res_model or "").strip()
        except Exception:
            return ""
        return ""

    def build_contract_stub(self, *, payload: Dict[str, Any], context: Dict[str, Any]) -> UIContractResultV2:
        if bool((payload or {}).get("raise_handler_error")):
            raise RuntimeError("ui.contract handler forced error")

        model = self._resolve_model(payload or {})
        view_type = str((payload or {}).get("view_type") or "form").strip().lower() or "form"
        contract_surface = str((payload or {}).get("contract_surface") or (payload or {}).get("surface") or "user").strip().lower() or "user"
        if contract_surface not in {"native", "user", "hud"}:
            contract_surface = "user"
        render_mode = "native" if contract_surface == "native" else "governed"
        source_mode = str((payload or {}).get("source_mode") or "v2_dispatch").strip().lower() or "v2_dispatch"
        governed_from_native = render_mode != "native"

        contract_data: Dict[str, Any]
        try:
            contract_data = self._build_runtime_contract(
                payload=payload or {},
                contract_surface=contract_surface,
                source_mode=source_mode,
            )
        except Exception:
            contract_data = self._build_fallback_contract(
                payload=payload or {},
                model=model,
                view_type=view_type,
                contract_surface=contract_surface,
                source_mode=source_mode,
            )
        if not model:
            model = str((contract_data or {}).get("model") or model or "").strip()

        surface_mapping = (contract_data or {}).get("surface_mapping") if isinstance(contract_data, dict) else {}
        if not isinstance(surface_mapping, dict):
            surface_mapping = {}
        return UIContractResultV2(
            intent="ui.contract",
            contract=contract_data if isinstance(contract_data, dict) else {},
            model=model,
            view_type=view_type,
            contract_surface=contract_surface,
            render_mode=render_mode,
            source_mode=source_mode,
            governed_from_native=governed_from_native,
            surface_mapping=surface_mapping,
            schema_validated=bool((payload or {}).get("schema_validated")),
            trace_id=str((context or {}).get("trace_id") or ""),
            status="execution_closure",
            version="v2",
            phase="boundary_closure",
        )
