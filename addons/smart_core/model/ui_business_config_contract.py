# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.smart_core.utils.backend_contract_boundaries import (
    classify_view_orchestration_contract,
    view_orchestration_apply_order_key,
)

FORMAL_LIST_ACTION_IDS = {
    506, 525, 529, 530, 531, 545, 549, 565, 566, 615,
    642, 644, 645, 646, 647, 669, 701, 751, 752, 753,
    754, 756, 757, 758, 759, 761, 762, 764, 768, 769,
    770, 771, 772, 773, 776, 777, 778, 779, 780, 781,
    782, 783, 784, 786, 787, 805, 814, 841, 859, 862,
    868, 869, 871, 901, 902, 906, 907, 935, 936, 949,
    963, 964,
}
TEST_PLACEHOLDER_TOKENS = ("CODEX_", "codex_view_orch_surface")


class UIBusinessConfigContract(models.Model):
    _name = "ui.business.config.contract"
    _description = "UI Business Config Contract"
    _order = "write_date desc, id desc"

    name = fields.Char(required=True)
    model = fields.Char(required=True, index=True)
    view_type = fields.Selection([
        ("form", "Form"),
        ("tree", "Tree/List"),
        ("list", "List"),
        ("kanban", "Kanban"),
        ("search", "Search"),
        ("pivot", "Pivot"),
        ("graph", "Graph"),
        ("calendar", "Calendar"),
        ("gantt", "Gantt"),
        ("activity", "Activity"),
        ("dashboard", "Dashboard"),
    ], index=True)
    action_id = fields.Many2one("ir.actions.act_window", string="Action", ondelete="cascade", index=True)
    view_id = fields.Many2one("ir.ui.view", string="View", ondelete="cascade", index=True)
    role_key = fields.Char(index=True)
    priority = fields.Integer(default=100, index=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, index=True)
    active = fields.Boolean(default=True)
    status = fields.Selection([("draft", "Draft"), ("published", "Published")], default="draft", required=True)
    version_no = fields.Integer(default=1, required=True)
    contract_json = fields.Json(required=True, default=dict)
    created_by = fields.Many2one("res.users", default=lambda self: self.env.user, readonly=True)
    published_at = fields.Datetime()

    _sql_constraints = [
        ("name_company_unique", "unique(name, company_id)", "同公司下业务配置名称必须唯一。"),
    ]

    def _normalize_view_orchestration_view_type(self, view_type: str | None) -> str:
        normalized = str(view_type or "").strip()
        return "tree" if normalized == "list" else normalized

    @staticmethod
    def _contains_test_placeholder(value) -> bool:
        text = str(value or "")
        return any(token in text for token in TEST_PLACEHOLDER_TOKENS)

    @api.constrains("name", "contract_json", "action_id", "active", "status")
    def _check_formal_surface_no_test_placeholders(self):
        for rec in self:
            if not rec.active or rec.status != "published":
                continue
            if int(rec.action_id.id or 0) not in FORMAL_LIST_ACTION_IDS:
                continue
            if rec._contains_test_placeholder(rec.name) or rec._contains_test_placeholder(rec.contract_json):
                raise ValidationError(
                    "正式产品列表配置不能发布测试占位内容：%s" % (rec.action_id.display_name or rec.name)
                )

    @staticmethod
    def _simple_view_orchestration_field_name(value) -> str:
        if not isinstance(value, str):
            return ""
        candidate = value.strip()
        if not candidate:
            return ""
        if "." in candidate or "(" in candidate or ")" in candidate or " " in candidate:
            return ""
        if not candidate.replace("_", "").isalnum():
            return ""
        return candidate

    @classmethod
    def _unknown_view_orchestration_fields(cls, payload: dict, model_fields) -> list[str]:
        if not isinstance(payload, dict):
            return []
        orchestration = payload.get("view_orchestration")
        if not isinstance(orchestration, dict):
            return []
        views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
        known_fields = set(model_fields or [])
        unknown: list[str] = []

        def add_ref(view_type: str, key: str, value) -> None:
            field_name = cls._simple_view_orchestration_field_name(value)
            if field_name and field_name not in known_fields:
                unknown.append("%s.%s:%s" % (view_type, key, field_name))

        def add_row_ref(view_type: str, key: str, row) -> None:
            if isinstance(row, str):
                add_ref(view_type, key, row)
                return
            if not isinstance(row, dict):
                return
            for ref_key in ("field", "name", "field_name"):
                if row.get(ref_key):
                    add_ref(view_type, key, row.get(ref_key))
                    return

        def add_slot_refs(view_type: str, key: str, value) -> None:
            if not isinstance(value, dict):
                return
            for slot_key, slot_value in value.items():
                if isinstance(slot_value, str):
                    add_ref(view_type, "%s.%s" % (key, slot_key), slot_value)
                elif isinstance(slot_value, list):
                    for item in slot_value:
                        if isinstance(item, str):
                            add_ref(view_type, "%s.%s" % (key, slot_key), item)
                        elif isinstance(item, dict):
                            for nested_key in ("field", "name", "field_name"):
                                if item.get(nested_key):
                                    add_ref(view_type, "%s.%s" % (key, slot_key), item.get(nested_key))
                                    break

        def add_layout_refs(view_type: str, rows, path: str = "layout") -> None:
            if not isinstance(rows, list):
                return
            for idx, row in enumerate(rows):
                if not isinstance(row, dict):
                    continue
                if str(row.get("type") or "").strip().lower() == "field":
                    add_row_ref(view_type, "%s[%s]" % (path, idx), row)
                for child_key in ("children", "pages", "tabs", "nodes", "items"):
                    children = row.get(child_key)
                    if isinstance(children, list):
                        add_layout_refs(view_type, children, "%s[%s].%s" % (path, idx, child_key))

        for view_type, spec in views.items():
            if not isinstance(spec, dict):
                continue
            for key in ("fields", "columns", "measures", "dimensions"):
                rows = spec.get(key) if isinstance(spec.get(key), list) else []
                for row in rows:
                    add_row_ref(view_type, key, row)
            for key in ("filters", "group_by", "groupBys"):
                rows = spec.get(key) if isinstance(spec.get(key), list) else []
                for row in rows:
                    if isinstance(row, str):
                        add_ref(view_type, key, row)
                    elif isinstance(row, dict) and row.get("field"):
                        add_ref(view_type, key, row.get("field"))
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
                add_slot_refs(view_type, key, spec.get(key))
            add_layout_refs(view_type, spec.get("layout"))
            for key in ("default_group_by", "order", "default_order"):
                add_ref(view_type, key, spec.get(key))
        return sorted(set(unknown))

    @api.constrains("contract_json", "model")
    def _check_contract_json(self):
        for rec in self:
            payload = rec.contract_json if isinstance(rec.contract_json, dict) else {}
            rec._check_view_orchestration_payload(payload)
            if rec.model and rec.model in self.env:
                unknown_fields = rec._unknown_view_orchestration_fields(payload, self.env[rec.model]._fields)
                if unknown_fields:
                    raise ValidationError("view_orchestration 引用了不存在字段：%s" % ", ".join(unknown_fields))
            objects = payload.get("objects") if isinstance(payload.get("objects"), list) else []
            object_fields_map: dict[str, set[str]] = {}
            for obj in objects:
                if not isinstance(obj, dict):
                    raise ValidationError("objects 节点必须是对象数组。")
                obj_name = str(obj.get("name") or "").strip()
                if not obj_name:
                    raise ValidationError("业务对象 name 不能为空。")
                fields_rows = obj.get("fields") if isinstance(obj.get("fields"), list) else []
                object_fields_map.setdefault(obj_name, set())
                for row in fields_rows:
                    if not isinstance(row, dict):
                        raise ValidationError("fields 节点必须是对象数组。")
                    field_name = str(row.get("name") or "").strip()
                    field_type = str(row.get("type") or "").strip()
                    if not field_name:
                        raise ValidationError("字段 name 不能为空。")
                    if field_type not in {"string", "float", "date", "selection", "integer", "boolean", "text"}:
                        raise ValidationError("字段类型不支持：%s" % field_type)
                    if field_name and not field_name.replace("_", "").isalnum():
                        raise ValidationError("字段名不合法：%s" % field_name)
                    object_fields_map[obj_name].add(field_name)
                    default_value = row.get("default")
                    if default_value is not None and field_type in {"float", "integer"} and not isinstance(default_value, (int, float)):
                        raise ValidationError("字段默认值类型不匹配：%s 需要数字" % field_name)
                    if default_value is not None and field_type == "boolean" and not isinstance(default_value, bool):
                        raise ValidationError("字段默认值类型不匹配：%s 需要布尔值" % field_name)
                    if field_type == "selection":
                        options = row.get("options") if isinstance(row.get("options"), list) else []
                        if not options:
                            raise ValidationError("selection 字段必须提供 options：%s" % field_name)
                        for option in options:
                            if not isinstance(option, dict):
                                raise ValidationError("selection 字段 options 必须是对象数组：%s" % field_name)
                            value = str(option.get("value") or "").strip()
                            label = str(option.get("label") or "").strip()
                            if not value or not label:
                                raise ValidationError("selection 字段 option 必须包含 value/label：%s" % field_name)

            layout = payload.get("layout") if isinstance(payload.get("layout"), dict) else {}
            for section in ("form", "list", "kanban"):
                nodes = layout.get(section) if isinstance(layout.get(section), list) else []
                for node in nodes:
                    if not isinstance(node, dict):
                        raise ValidationError("layout.%s 节点必须是对象数组。" % section)
                    target_obj = str(node.get("object") or "").strip()
                    target_field = str(node.get("field") or "").strip()
                    if target_obj and target_field and target_obj in object_fields_map and target_field not in object_fields_map[target_obj]:
                        raise ValidationError("layout 引用了不存在字段：%s.%s" % (target_obj, target_field))

            rules = payload.get("rules") if isinstance(payload.get("rules"), list) else []
            for rule in rules:
                if not isinstance(rule, dict):
                    raise ValidationError("rules 节点必须是对象数组。")
                trigger = str(rule.get("trigger") or "").strip()
                if trigger not in {"on_create", "on_update", "scheduled"}:
                    raise ValidationError("规则触发器不支持：%s" % trigger)
                action = rule.get("action") if isinstance(rule.get("action"), dict) else {}
                target_obj = str(action.get("object") or "").strip()
                target_field = str(action.get("field") or "").strip()
                if target_obj and target_field and target_obj in object_fields_map and target_field not in object_fields_map[target_obj]:
                    raise ValidationError("规则动作引用不存在字段：%s.%s" % (target_obj, target_field))

    @api.constrains("model", "action_id", "view_id")
    def _check_view_scope(self):
        for rec in self:
            if rec.model and rec.model not in self.env:
                raise ValidationError("模型不存在：%s" % rec.model)
            if rec.action_id and rec.action_id.res_model != rec.model:
                raise ValidationError("动作不属于当前模型：%s" % rec.action_id.display_name)
            if rec.view_id and rec.view_id.model != rec.model:
                raise ValidationError("视图不属于当前模型：%s" % rec.view_id.display_name)
            if (
                rec.view_id
                and rec.view_type
                and self._normalize_view_orchestration_view_type(rec.view_id.type)
                != self._normalize_view_orchestration_view_type(rec.view_type)
            ):
                raise ValidationError("视图类型与配置范围不一致：%s" % rec.view_id.display_name)

    def _check_view_orchestration_payload(self, payload: dict) -> None:
        orchestration = payload.get("view_orchestration")
        if orchestration is None:
            return
        if not isinstance(orchestration, dict):
            raise ValidationError("view_orchestration 必须是对象。")
        views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
        allowed = {"form", "tree", "list", "kanban", "search", "pivot", "graph", "calendar", "gantt", "activity", "dashboard"}
        list_keys = {
            "fields",
            "columns",
            "filters",
            "group_by",
            "groupBys",
            "measures",
            "dimensions",
            "actions",
            "quick_actions",
            "row_classes",
            "cards",
            "kpis",
            "sections",
            "layout",
        }
        dict_keys = {
            "defaults",
            "slots",
            "action_slots",
            "context",
            "domain",
            "chart_policy",
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
        }
        for view_type, spec in views.items():
            if view_type not in allowed:
                raise ValidationError("view_orchestration.views 不支持视图类型：%s" % view_type)
            if not isinstance(spec, dict):
                raise ValidationError("view_orchestration.views.%s 必须是对象。" % view_type)
            for key in list_keys:
                rows = spec.get(key)
                if rows is None:
                    continue
                if key == "columns" and view_type == "form":
                    if isinstance(rows, int) and rows in {1, 2, 3}:
                        continue
                    raise ValidationError("view_orchestration.views.form.columns 必须是 1、2 或 3。")
                if not isinstance(rows, list):
                    raise ValidationError("view_orchestration.views.%s.%s 必须是数组。" % (view_type, key))
                if key in {"measures", "dimensions"}:
                    invalid = [row for row in rows if not isinstance(row, (str, dict))]
                    if invalid:
                        raise ValidationError("view_orchestration.views.%s.%s 必须是字符串或对象数组。" % (view_type, key))
                    continue
                for row in rows:
                    if key == "row_classes" and isinstance(row, str):
                        continue
                    if not isinstance(row, dict):
                        raise ValidationError("view_orchestration.views.%s.%s 必须是对象数组。" % (view_type, key))
            for key in dict_keys:
                value = spec.get(key)
                if value is not None and not isinstance(value, dict):
                    raise ValidationError("view_orchestration.views.%s.%s 必须是对象。" % (view_type, key))

    @api.model
    def _effective_view_orchestration_contracts(
        self,
        model_name: str,
        *,
        view_type: str | None = None,
        action_id: int | None = None,
        view_id: int | None = None,
        role_key: str | None = None,
    ):
        if not model_name:
            return self.browse()
        normalized_view_type = self._normalize_view_orchestration_view_type(view_type)
        domain = [
            ("active", "=", True),
            ("status", "=", "published"),
            ("model", "=", model_name),
            "|",
            ("company_id", "=", False),
            ("company_id", "=", self.env.company.id),
        ]
        records = self.sudo().search(domain, order="priority, version_no, id")
        role_key = str(role_key or "").strip()

        def applies(contract) -> bool:
            contract_view_type = self._normalize_view_orchestration_view_type(contract.view_type)
            if contract_view_type and contract_view_type != normalized_view_type:
                return False
            contract_action = int(contract.action_id.id or 0)
            contract_view = int(contract.view_id.id or 0)
            contract_role = str(contract.role_key or "").strip()
            if contract_action and contract_action != int(action_id or 0):
                return False
            if contract_view and contract_view != int(view_id or 0):
                return False
            if contract_role and contract_role != role_key:
                return False
            return True

        effective = [contract for contract in records if applies(contract)]

        effective = sorted(effective, key=view_orchestration_apply_order_key)
        return self.browse([contract.id for contract in effective])

    @api.model
    def source_authority_contract(self) -> dict:
        return {
            "kind": "ui_business_config_contract_orchestration_config",
            "authorities": ["ui.business.config.contract", "ui.business.config.contract.version"],
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": True,
            "runtime_carrier": "ui.business.config.contract",
            "boundary_classifier": "smart_core.utils.backend_contract_boundaries",
        }

    def boundary_contract(self) -> dict:
        self.ensure_one()
        return classify_view_orchestration_contract(self.name, self.contract_json or {})

    def action_publish(self):
        for rec in self:
            rec.status = "published"
            rec.published_at = fields.Datetime.now()
            rec.version_no = int(rec.version_no or 1) + 1
            self.env["ui.business.config.contract.version"].create({
                "contract_id": rec.id,
                "version_no": rec.version_no,
                "snapshot_json": rec.contract_json or {},
                "status": rec.status,
                "created_by": self.env.user.id,
            })


class UIBusinessConfigContractVersion(models.Model):
    _name = "ui.business.config.contract.version"
    _description = "UI Business Config Contract Version"
    _order = "id desc"

    contract_id = fields.Many2one("ui.business.config.contract", required=True, ondelete="cascade", index=True)
    version_no = fields.Integer(required=True)
    status = fields.Selection([("draft", "Draft"), ("published", "Published")], default="draft", required=True)
    snapshot_json = fields.Json(required=True, default=dict)
    created_by = fields.Many2one("res.users", default=lambda self: self.env.user, readonly=True)
