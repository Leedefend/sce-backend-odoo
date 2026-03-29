# -*- coding: utf-8 -*-
"""Page-policy helpers for assembled contracts.

This service keeps policy-style decisions separate from page aggregation flow.
It must not assemble view blocks or fetch initial data.
"""

from __future__ import annotations


class PagePolicyService:
    def __init__(self, env, system_relation_degrade_models=None):
        self.env = env
        self.system_relation_degrade_models = set(system_relation_degrade_models or [])

    @staticmethod
    def normalize_field_list(values):
        out = []
        for item in values or []:
            name = str(item or "").strip()
            if name and name not in out:
                out.append(name)
        return out

    def restrict_form_fields_to_layout(self, data):
        if not isinstance(data, dict):
            return
        views = data.get("views") if isinstance(data.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        layout = form.get("layout")
        fields_map = data.get("fields") if isinstance(data.get("fields"), dict) else {}
        if not isinstance(layout, list) or not fields_map:
            return

        field_order = []

        def collect(nodes):
            for node in nodes or []:
                if not isinstance(node, dict):
                    continue
                if node.get("type") == "field":
                    name = str(node.get("name") or "").strip()
                    if name and name in fields_map and name not in field_order:
                        field_order.append(name)
                for key in ("children", "tabs", "pages", "items", "nodes"):
                    nested = node.get(key)
                    if isinstance(nested, list):
                        collect(nested)

        collect(layout)
        if not field_order:
            return

        keep_names = list(field_order)

        tree = views.get("tree") if isinstance(views.get("tree"), dict) else {}
        keep_names.extend(self.normalize_field_list(tree.get("columns") if isinstance(tree.get("columns"), list) else []))

        kanban = views.get("kanban") if isinstance(views.get("kanban"), dict) else {}
        keep_names.extend(self.normalize_field_list(kanban.get("fields") if isinstance(kanban.get("fields"), list) else []))

        search = data.get("search") if isinstance(data.get("search"), dict) else {}
        keep_names.extend(
            self.normalize_field_list(
                item.get("field")
                for item in (search.get("group_by") if isinstance(search.get("group_by"), list) else [])
                if isinstance(item, dict)
            )
        )

        statusbar = form.get("statusbar") if isinstance(form.get("statusbar"), dict) else {}
        status_field = str(statusbar.get("field") or "").strip()
        if status_field:
            keep_names.append(status_field)

        keep_names = self.normalize_field_list(keep_names)
        data["fields"] = {name: fields_map.get(name) for name in keep_names if name in fields_map}
        data["visible_fields"] = list(field_order)

    def safe_model_can_read(self, model_name):
        name = str(model_name or "").strip()
        if not name:
            return True
        try:
            return bool(self.env[name].check_access_rights("read", raise_exception=False))
        except Exception:
            return True

    def extract_core_field_names(self, data):
        if not isinstance(data, dict):
            return []
        fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}

        groups = data.get("field_groups")
        if isinstance(groups, list):
            for item in groups:
                if not isinstance(item, dict):
                    continue
                if str(item.get("name") or "").strip().lower() != "core":
                    continue
                rows = self.normalize_field_list(item.get("fields") if isinstance(item.get("fields"), list) else [])
                if rows:
                    return rows

        form_view = (data.get("views") or {}).get("form") if isinstance(data.get("views"), dict) else {}
        form_profile = form_view.get("form_profile") if isinstance(form_view, dict) else {}
        if not isinstance(form_profile, dict):
            form_profile = data.get("form_profile") if isinstance(data.get("form_profile"), dict) else {}
        if isinstance(form_profile, dict):
            rows = self.normalize_field_list(
                form_profile.get("core_fields") if isinstance(form_profile.get("core_fields"), list) else []
            )
            if rows:
                return rows

        semantic_core = []
        for name, desc in fields.items():
            if not isinstance(desc, dict):
                continue
            role = str(desc.get("surface_role") or "").strip().lower()
            if role == "core":
                semantic_core.append(str(name or "").strip())
        semantic_core = self.normalize_field_list(semantic_core)
        if semantic_core:
            return semantic_core

        required_relation = []
        for name, desc in fields.items():
            if not isinstance(desc, dict):
                continue
            ttype = str(desc.get("type") or desc.get("ttype") or "").strip().lower()
            relation = str(desc.get("relation") or "").strip()
            if ttype in {"many2one", "many2many", "one2many"} and relation and bool(desc.get("required")):
                required_relation.append(str(name or "").strip())
        return self.normalize_field_list(required_relation)

    def apply_access_policy(self, data, model_name=""):
        if not isinstance(data, dict):
            return
        fields = data.get("fields")
        if not isinstance(fields, dict):
            fields = {}

        blocked_fields = []
        degraded_fields = []
        policy_source = "none"

        model = str(model_name or "").strip()
        if model and not self.safe_model_can_read(model):
            blocked_fields.append(
                {
                    "field": "__model__",
                    "model": model,
                    "reason_code": "MODEL_READ_FORBIDDEN",
                }
            )
            policy_source = "model_acl"
        else:
            core_fields = set(self.extract_core_field_names(data))
            if core_fields:
                policy_source = "core_fields"
            for field_name, desc in fields.items():
                if not isinstance(desc, dict):
                    continue
                relation_entry = desc.get("relation_entry")
                if not isinstance(relation_entry, dict):
                    continue
                can_read = relation_entry.get("can_read")
                if can_read is not False:
                    continue
                relation = str(desc.get("relation") or relation_entry.get("model") or "").strip()
                row = {
                    "field": str(field_name or "").strip(),
                    "model": relation,
                    "reason_code": str(relation_entry.get("reason_code") or "RELATION_READ_FORBIDDEN"),
                }
                relation_model = str(relation or "").strip().lower()
                if (
                    str(field_name or "").strip() in core_fields
                    and relation_model not in self.system_relation_degrade_models
                ):
                    blocked_fields.append(row)
                else:
                    degraded_fields.append(row)

        mode = "allow"
        reason_code = ""
        message = ""
        if blocked_fields:
            mode = "block"
            first = blocked_fields[0]
            reason_code = str(first.get("reason_code") or "RELATION_READ_FORBIDDEN_CORE")
            if reason_code == "RELATION_READ_FORBIDDEN":
                reason_code = "RELATION_READ_FORBIDDEN_CORE"
            label = str(first.get("field") or first.get("model") or "unknown")
            message = f"core field access blocked: {label}"
        elif degraded_fields:
            mode = "degrade"
            first = degraded_fields[0]
            reason_code = str(first.get("reason_code") or "RELATION_READ_FORBIDDEN")
            label = str(first.get("field") or first.get("model") or "unknown")
            message = f"relation access degraded: {label}"

        data["access_policy"] = {
            "mode": mode,
            "reason_code": reason_code,
            "message": message,
            "policy_source": policy_source,
            "blocked_fields": blocked_fields,
            "degraded_fields": degraded_fields,
        }

        if mode in {"block", "degrade"}:
            warnings = data.get("warnings") if isinstance(data.get("warnings"), list) else []
            marker = f"access_policy:{mode}:{reason_code or 'UNKNOWN'}"
            if marker not in warnings:
                warnings.append(marker)
            data["warnings"] = warnings
