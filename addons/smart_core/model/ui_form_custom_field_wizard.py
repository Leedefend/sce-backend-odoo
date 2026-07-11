# -*- coding: utf-8 -*-
"""Controlled custom-field creation for business form configuration."""

from __future__ import annotations

import re
import time

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class UIFormCustomFieldWizard(models.TransientModel):
    _name = "ui.form.custom.field.wizard"
    _description = "UI Form Custom Field Wizard"

    SAFE_TYPES = (
        ("char", "单行文本"),
        ("text", "多行文本"),
        ("integer", "整数"),
        ("float", "小数"),
        ("boolean", "是/否"),
        ("date", "日期"),
        ("datetime", "日期时间"),
        ("html", "富文本"),
    )
    FIELD_NAME_RE = re.compile(r"^x_[a-z][a-z0-9_]{1,54}$")

    model_id = fields.Many2one(
        "ir.model",
        string="模型",
        required=True,
        domain=[("transient", "=", False)],
    )
    model = fields.Char(related="model_id.model", string="数据模型")
    field_name = fields.Char(string="字段标识", default="x_custom_field")
    label = fields.Char(string="字段标题", required=True)
    ttype = fields.Selection(SAFE_TYPES, string="字段类型", required=True, default="char")
    help = fields.Char(string="帮助说明")
    required = fields.Boolean(string="必填")
    index = fields.Boolean(string="建立索引")
    active_policy = fields.Boolean(string="创建后立即显示", default=True)
    company_id = fields.Many2one("res.company", string="公司", default=lambda self: self.env.company)
    action_id = fields.Many2one("ir.actions.act_window", string="业务页面", ondelete="cascade")
    view_id = fields.Many2one("ir.ui.view", string="表单视图", ondelete="cascade")
    group_title = fields.Char(string="显示分组", default="业务配置字段")
    sequence = fields.Integer(string="显示顺序", default=100)
    note = fields.Text(string="说明")

    @api.onchange("action_id")
    def _onchange_action_id(self):
        for rec in self:
            if rec.action_id and rec.action_id.res_model:
                model_rec = self.env["ir.model"].search([("model", "=", rec.action_id.res_model)], limit=1)
                if model_rec:
                    rec.model_id = model_rec
                    if rec.view_id and rec.view_id.model != model_rec.model:
                        rec.view_id = False

    @api.onchange("model_id")
    def _onchange_model_id(self):
        for rec in self:
            if rec.model_id:
                if rec.action_id and rec.action_id.res_model != rec.model_id.model:
                    rec.action_id = False
                if rec.view_id and rec.view_id.model != rec.model_id.model:
                    rec.view_id = False

    @api.onchange("label")
    def _onchange_label(self):
        for rec in self:
            if not rec.field_name or str(rec.field_name).strip() in {"x_", "x_custom_field"}:
                rec.field_name = rec._suggest_field_name()

    @api.constrains("model_id", "field_name", "ttype", "action_id", "view_id")
    def _check_custom_field_spec(self):
        for rec in self:
            rec._validate_custom_field_spec()

    def action_create_field_policy(self):
        self.ensure_one()
        if not self.field_name or str(self.field_name).strip() in {"x_", "x_custom_field"}:
            self.field_name = self._suggest_field_name()
        self._validate_custom_field_spec()
        model_rec = self._business_model()
        field = self._create_manual_field()
        policy = self.env["ui.form.field.policy"].create({
            "active": bool(self.active_policy),
            "model_id": model_rec.id,
            "model": model_rec.model,
            "field_id": field.id,
            "field_name": field.name,
            "label": self.label,
            "visible": True,
            "company_id": self.company_id.id or False,
            "action_id": self.action_id.id or False,
            "view_id": self.view_id.id or False,
            "group_title": self.group_title or "业务配置字段",
            "sequence": self.sequence or 100,
            "note": self.note,
        })
        return {
            "type": "ir.actions.act_window",
            "name": "表单字段配置",
            "res_model": "ui.form.field.policy",
            "res_id": policy.id,
            "view_mode": "form",
            "target": "current",
        }

    def _validate_custom_field_spec(self):
        self.ensure_one()
        model = self._business_model()
        model_name = model.model if model else ""
        field_name = str(self.field_name or "").strip()
        if not model or not model_name:
            raise ValidationError("请先选择要配置的业务页面。")
        if model.transient:
            raise ValidationError("临时向导模型不能新增业务字段：%s" % model_name)
        if model_name not in self.env:
            raise ValidationError("模型不存在：%s" % model_name)
        if not self.FIELD_NAME_RE.match(field_name):
            raise ValidationError("技术字段名必须以 x_ 开头，并且只能包含小写字母、数字和下划线。")
        if field_name in self.env[model_name]._fields:
            raise ValidationError("字段已经存在：%s.%s" % (model_name, field_name))
        if self.ttype not in dict(self.SAFE_TYPES):
            raise ValidationError("不支持的字段类型：%s" % (self.ttype or "-"))
        if not self.action_id:
            raise ValidationError("请先选择要配置的业务页面。")
        if self.required:
            raise ValidationError("新增自定义字段暂不开放必填属性，请先创建非必填字段，再通过业务流程约束控制必填。")
        if self.action_id and self.action_id.res_model != model_name:
            raise ValidationError("限定动作不属于当前模型：%s" % self.action_id.display_name)
        if self.view_id and (self.view_id.model != model_name or self.view_id.type != "form"):
            raise ValidationError("限定视图必须是当前模型的表单视图：%s" % self.view_id.display_name)

    def _create_manual_field(self):
        self.ensure_one()
        model_rec = self._business_model()
        vals = {
            "name": str(self.field_name or "").strip(),
            "field_description": str(self.label or "").strip(),
            "model_id": model_rec.id,
            "ttype": self.ttype,
            "state": "manual",
            "required": bool(self.required),
            "index": bool(self.index),
            "help": str(self.help or "").strip(),
            "copied": True,
        }
        return self.env["ir.model.fields"].sudo().create(vals)

    def _business_model(self):
        self.ensure_one()
        model = self.model_id
        if model and model.exists():
            return model
        action_model = str(self.action_id.res_model or "").strip() if self.action_id else ""
        if action_model:
            model = self.env["ir.model"].search([("model", "=", action_model)], limit=1)
            if model:
                return model
        return self.env["ir.model"]

    def _suggest_field_name(self):
        self.ensure_one()
        label = str(self.label or "").strip()
        ascii_slug = re.sub(r"[^a-z0-9_]+", "_", label.lower()).strip("_")
        if not ascii_slug or not re.match(r"^[a-z]", ascii_slug):
            ascii_slug = "custom_field"
        ascii_slug = re.sub(r"_+", "_", ascii_slug)[:40].strip("_") or "custom_field"
        base = "x_%s" % ascii_slug
        model = self._business_model()
        model_name = model.model if model else ""
        candidate = base
        index = 2
        while model_name and candidate in self.env[model_name]._fields:
            candidate = "%s_%s" % (base[:50], index)
            index += 1
        if candidate == base and model_name:
            exists = self.env["ir.model.fields"].sudo().search_count([("model", "=", model_name), ("name", "=", candidate)])
            if exists:
                candidate = "%s_%s" % (base[:45], int(time.time()) % 100000)
        return candidate[:56]
