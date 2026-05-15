# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class UIBusinessConfigContract(models.Model):
    _name = "ui.business.config.contract"
    _description = "UI Business Config Contract"
    _order = "write_date desc, id desc"

    name = fields.Char(required=True)
    model = fields.Char(required=True, index=True)
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

    @api.constrains("contract_json", "model")
    def _check_contract_json(self):
        for rec in self:
            payload = rec.contract_json if isinstance(rec.contract_json, dict) else {}
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
