# -*- coding: utf-8 -*-
"""Business-managed form field visibility policies."""

from __future__ import annotations

from typing import Any

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class UIFormFieldPolicy(models.Model):
    _name = "ui.form.field.policy"
    _description = "表单字段配置"
    _order = "model, sequence, id"

    SOURCE_KIND = "ui_form_field_policy_overlay"
    SOURCE_AUTHORITIES = ("ui.form.field.policy", "ir.model.fields", "app.view.config")
    NO_BUSINESS_FACT_AUTHORITY = True

    name = fields.Char(string="配置名称", compute="_compute_name", store=True)
    active = fields.Boolean(string="启用", default=True)
    model_id = fields.Many2one("ir.model", string="业务对象", ondelete="cascade", index=True)
    model = fields.Char(string="数据模型", required=True, index=True)
    field_name = fields.Char(string="字段标识", required=True, index=True)
    field_id = fields.Many2one("ir.model.fields", string="选择字段", ondelete="cascade")
    action_id = fields.Many2one("ir.actions.act_window", string="业务页面", ondelete="cascade")
    view_id = fields.Many2one("ir.ui.view", string="限定表单视图", ondelete="cascade")
    company_id = fields.Many2one("res.company", string="公司", default=lambda self: self.env.company)
    role_group_ids = fields.Many2many(
        "res.groups",
        "ui_form_field_policy_group_rel",
        "policy_id",
        "group_id",
        string="适用业务角色",
        help="留空表示对当前公司所有用户生效；填写后仅对这些业务角色中的用户生效。",
    )
    visible = fields.Boolean(string="显示", default=True)
    label = fields.Char(string="显示名称")
    sequence = fields.Integer(string="显示顺序", default=100)
    group_title = fields.Char(default="业务配置字段")
    field_type = fields.Char(string="字段类型", compute="_compute_policy_summary")
    field_label = fields.Char(string="字段名称", compute="_compute_policy_summary")
    scope_summary = fields.Char(string="生效范围", compute="_compute_policy_summary")
    effect_summary = fields.Char(string="显示效果", compute="_compute_policy_summary")
    note = fields.Text(string="说明")

    @api.depends("model", "field_name", "visible", "label")
    def _compute_name(self):
        for rec in self:
            state = "显示" if rec.visible else "隐藏"
            title = rec.label or rec.field_label or rec.field_name or "-"
            rec.name = "%s.%s %s" % (rec.model or "-", title, state)

    @api.depends("model", "field_name", "field_id", "label", "visible", "company_id", "action_id", "view_id", "role_group_ids")
    def _compute_policy_summary(self):
        for rec in self:
            field = rec.field_id
            if not field and rec.model and rec.field_name:
                field = self.env["ir.model.fields"].search(
                    [("model", "=", rec.model), ("name", "=", rec.field_name)],
                    limit=1,
                )
            rec.field_type = field.ttype if field else ""
            rec.field_label = rec.label or (field.field_description if field else "")
            scope = []
            scope.append(rec.company_id.display_name if rec.company_id else "所有公司")
            if rec.action_id:
                scope.append("动作：%s" % rec.action_id.display_name)
            if rec.view_id:
                scope.append("视图：%s" % rec.view_id.display_name)
            groups = rec.role_group_ids.mapped("display_name")
            scope.append("业务角色：%s" % "、".join(groups) if groups else "业务角色：全部")
            if not rec.action_id and not rec.view_id:
                scope.append("全部表单")
            rec.scope_summary = " / ".join(scope)
            verb = "显示" if rec.visible else "隐藏"
            rec.effect_summary = "%s字段：%s" % (verb, rec.field_label or rec.field_name or "-")

    @api.onchange("field_id")
    def _onchange_field_id(self):
        for rec in self:
            if rec.field_id:
                rec.model_id = rec.field_id.model_id
                rec.model = rec.field_id.model
                rec.field_name = rec.field_id.name
                if not rec.label:
                    rec.label = rec.field_id.field_description

    @api.onchange("action_id")
    def _onchange_action_id(self):
        for rec in self:
            if rec.action_id and rec.action_id.res_model:
                model_rec = self.env["ir.model"].search([("model", "=", rec.action_id.res_model)], limit=1)
                if model_rec:
                    rec.model_id = model_rec
                    rec.model = model_rec.model
                    if rec.field_id and rec.field_id.model_id != model_rec:
                        rec.field_id = False
                        rec.field_name = False
                    if rec.view_id and rec.view_id.model != model_rec.model:
                        rec.view_id = False

    @api.onchange("model_id")
    def _onchange_model_id(self):
        for rec in self:
            if rec.model_id:
                rec.model = rec.model_id.model
                if rec.field_id and rec.field_id.model_id != rec.model_id:
                    rec.field_id = False
                    rec.field_name = False
                if rec.action_id and rec.action_id.res_model != rec.model:
                    rec.action_id = False
                if rec.view_id and rec.view_id.model != rec.model:
                    rec.view_id = False

    @api.onchange("model")
    def _onchange_model(self):
        for rec in self:
            model_name = str(rec.model or "").strip()
            if not model_name:
                rec.model_id = False
                continue
            model_rec = self.env["ir.model"].search([("model", "=", model_name)], limit=1)
            if model_rec:
                rec.model_id = model_rec

    @api.constrains("model_id", "model", "field_name", "field_id", "action_id", "view_id")
    def _check_field_exists(self):
        for rec in self:
            if not rec.model or not rec.field_name:
                continue
            if rec.model not in self.env:
                raise ValidationError("模型不存在：%s" % rec.model)
            model_rec = rec.model_id or self.env["ir.model"].search([("model", "=", rec.model)], limit=1)
            if model_rec and model_rec.transient:
                raise ValidationError("临时向导模型不能配置表单字段：%s" % rec.model)
            if rec.field_name not in self.env[rec.model]._fields:
                raise ValidationError("字段不存在：%s.%s" % (rec.model, rec.field_name))
            if rec.field_id and (rec.field_id.model != rec.model or rec.field_id.name != rec.field_name):
                raise ValidationError("字段记录与模型/字段名不一致")
            field_rec = rec.field_id or self.env["ir.model.fields"].search(
                [("model", "=", rec.model), ("name", "=", rec.field_name)],
                limit=1,
            )
            if field_rec and field_rec.ttype == "binary":
                raise ValidationError("二进制字段不能作为业务表单字段配置：%s.%s" % (rec.model, rec.field_name))
            if rec.action_id and rec.action_id.res_model != rec.model:
                raise ValidationError("动作不属于当前模型：%s" % rec.action_id.display_name)
            if rec.view_id and (rec.view_id.model != rec.model or rec.view_id.type != "form"):
                raise ValidationError("视图必须是当前模型的表单视图：%s" % rec.view_id.display_name)

    @api.constrains("active", "model", "field_name", "company_id", "action_id", "view_id", "role_group_ids")
    def _check_unique_effective_policy(self):
        for rec in self:
            if not rec.active or not rec.model or not rec.field_name:
                continue
            domain = [
                ("id", "!=", rec.id),
                ("active", "=", True),
                ("model", "=", rec.model),
                ("field_name", "=", rec.field_name),
                ("company_id", "=", rec.company_id.id or False),
                ("action_id", "=", rec.action_id.id or False),
                ("view_id", "=", rec.view_id.id or False),
            ]
            same_scope = self.search(domain)
            rec_group_ids = set(rec.role_group_ids.ids)
            for other in same_scope:
                other_group_ids = set(other.role_group_ids.ids)
                if not rec_group_ids and not other_group_ids:
                    raise ValidationError("同一模型/字段/公司/动作/视图/业务角色范围内只能保留一条启用的字段策略。")
                if rec_group_ids and other_group_ids and rec_group_ids & other_group_ids:
                    raise ValidationError("同一模型/字段/公司/动作/视图/业务角色范围内只能保留一条启用的字段策略。")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._normalize_field_policy_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals or {})
        self._normalize_field_policy_vals(vals)
        return super().write(vals)

    def _normalize_field_policy_vals(self, vals: dict) -> None:
        field_id = vals.get("field_id")
        if field_id:
            field = self.env["ir.model.fields"].browse(int(field_id))
            if field.ttype == "binary":
                raise ValidationError("二进制字段不能作为业务表单字段配置：%s.%s" % (field.model, field.name))
            if field.model_id.transient:
                raise ValidationError("临时向导模型不能配置表单字段：%s" % field.model)
            vals.setdefault("model_id", field.model_id.id)
            vals.setdefault("model", field.model)
            vals.setdefault("field_name", field.name)
            if not vals.get("label"):
                vals["label"] = field.field_description
            return
        model_id = vals.get("model_id")
        model_rec = self.env["ir.model"].browse(int(model_id)) if model_id else self.env["ir.model"]
        if model_rec:
            if model_rec.transient:
                raise ValidationError("临时向导模型不能配置表单字段：%s" % model_rec.model)
            if not vals.get("model"):
                vals["model"] = model_rec.model
        model_name = str(vals.get("model") or "").strip()
        field_name = str(vals.get("field_name") or "").strip()
        if model_name and field_name:
            field = self.env["ir.model.fields"].search([("model", "=", model_name), ("name", "=", field_name)], limit=1)
            if field.ttype == "binary":
                raise ValidationError("二进制字段不能作为业务表单字段配置：%s.%s" % (model_name, field_name))

    def action_probe_contract_effect(self):
        self.ensure_one()
        if not self.model or not self.field_name:
            raise ValidationError("请先选择模型和字段。")
        context = {"contract_projection_readonly": True}
        if self.action_id:
            context["contract_action_id"] = self.action_id.id
        if self.view_id:
            context["contract_view_id"] = self.view_id.id
        view_config = self.env["app.view.config"].with_context(**context)._generate_from_fields_view_get(self.model, "form")
        contract = view_config.get_contract_api(filter_runtime=True, check_model_acl=True)
        nodes = self._collect_contract_field_nodes(contract.get("layout") or [])
        field_node = nodes.get(self.field_name)
        hidden = field_node is None
        invisible = bool(field_node and self._contract_node_has_invisible(field_node))
        expected_ok = (not hidden and not invisible) if self.visible else hidden
        if self.visible:
            detail = "已显示" if expected_ok else "未显示或仍有隐藏条件"
        else:
            detail = "已隐藏" if expected_ok else "仍然出现在表单契约中"
        governance = (contract.get("governance") or {}).get("form_field_policy") or {}
        if expected_ok:
            notif_type = "success"
            title = "字段策略已生效"
        else:
            notif_type = "warning"
            title = "字段策略未完全生效"
        message = "%s：%s；范围：%s；治理标记：%s" % (
            self.field_label or self.field_name,
            detail,
            self.scope_summary or "-",
            "已命中" if governance.get("applied") else "未命中",
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
                "type": notif_type,
                "sticky": not expected_ok,
            },
        }

    def _collect_contract_field_nodes(self, nodes: list) -> dict[str, dict]:
        result = {}
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            if str(node.get("type") or "").strip().lower() == "field":
                name = str(node.get("name") or "").strip()
                if name:
                    result[name] = node
            for key in ("children", "pages", "tabs", "nodes", "items"):
                children = node.get(key)
                if isinstance(children, list):
                    result.update(self._collect_contract_field_nodes(children))
        return result

    def _contract_node_has_invisible(self, node: dict) -> bool:
        candidates = [node]
        for key in ("attributes", "fieldInfo"):
            value = node.get(key)
            if isinstance(value, dict):
                candidates.append(value)
        for candidate in candidates:
            if candidate.get("invisible"):
                return True
            modifiers = candidate.get("modifiers")
            if isinstance(modifiers, dict) and "invisible" in modifiers:
                return True
        return False

    @api.model
    def source_authority_contract(self) -> dict[str, Any]:
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": self.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": "ui.form.field.policy",
        }

    @api.model
    def apply_to_view_contract(
        self,
        contract: dict | None,
        *,
        model_name: str,
        view_type: str,
        action_id: int | None = None,
        view_id: int | None = None,
        excluded_field_names: set[str] | list[str] | tuple[str, ...] | None = None,
    ) -> dict:
        if view_type != "form" or not isinstance(contract, dict) or not model_name:
            return contract or {}
        if model_name not in self.env:
            return contract

        policies = self._effective_policies(model_name, action_id=action_id, view_id=view_id, user=self.env.user)
        if not policies:
            return contract

        fields_meta = self.env[model_name].fields_get()
        available_fields = set(fields_meta.keys())
        excluded_fields = {
            str(name or "").strip()
            for name in (excluded_field_names or [])
            if str(name or "").strip()
        }
        effective: dict[str, dict[str, Any]] = {}
        skipped_by_business_config = []
        for policy in policies:
            field_name = str(policy.field_name or "").strip()
            if not field_name or field_name not in available_fields:
                continue
            if field_name in excluded_fields:
                skipped_by_business_config.append(field_name)
                continue
            label = str(policy.label or "").strip()
            effective[field_name] = {
                "visible": bool(policy.visible),
                "label": label,
                "sequence": int(policy.sequence or 100),
                "group_title": str(policy.group_title or "业务配置字段").strip() or "业务配置字段",
                "policy_id": int(policy.id),
                "role_group_ids": [int(group_id) for group_id in policy.role_group_ids.ids],
                "field_info": self._field_contract_info(fields_meta.get(field_name) or {}, label),
            }
        if not effective:
            if skipped_by_business_config:
                meta = contract.get("governance") if isinstance(contract.get("governance"), dict) else {}
                meta["form_field_policy"] = {
                    "applied": False,
                    "source_authority": self.source_authority_contract(),
                    "model": model_name,
                    "skipped_by_business_config_fields": sorted(set(skipped_by_business_config)),
                }
                contract["governance"] = meta
            return contract

        visible = {name for name, rule in effective.items() if rule.get("visible")}
        hidden = set(effective) - visible
        layout = contract.get("layout")
        if isinstance(layout, list):
            layout = self._apply_layout_policy(layout, effective)
            self._append_visible_policy_fields(layout, visible, effective)
            contract["layout"] = layout

        field_modifiers = contract.get("field_modifiers")
        if isinstance(field_modifiers, dict):
            for field_name in hidden:
                field_modifiers.pop(field_name, None)
            for field_name in visible:
                if isinstance(field_modifiers.get(field_name), dict):
                    field_modifiers[field_name].pop("invisible", None)
            contract["field_modifiers"] = field_modifiers

        meta = contract.get("governance") if isinstance(contract.get("governance"), dict) else {}
        meta["form_field_policy"] = {
            "applied": True,
            "source_authority": self.source_authority_contract(),
            "model": model_name,
            "visible_fields": sorted(visible),
            "hidden_fields": sorted(hidden),
            "role_group_scoped": any(bool(rule.get("role_group_ids")) for rule in effective.values()),
            "skipped_by_business_config_fields": sorted(set(skipped_by_business_config)),
        }
        contract["governance"] = meta
        return contract

    def _effective_policies(self, model_name: str, *, action_id: int | None = None, view_id: int | None = None, user=None):
        domain = [
            ("active", "=", True),
            ("model", "=", model_name),
            "|",
            ("company_id", "=", False),
            ("company_id", "=", self.env.company.id),
        ]
        records = self.sudo().search(domain, order="sequence, id")
        user = user or self.env.user
        user_group_ids = set(user.groups_id.ids) if user else set()

        def applies(policy) -> bool:
            policy_action = int(policy.action_id.id or 0)
            policy_view = int(policy.view_id.id or 0)
            policy_group_ids = set(policy.role_group_ids.ids)
            if policy_action and policy_action != int(action_id or 0):
                return False
            if policy_view and policy_view != int(view_id or 0):
                return False
            if policy_group_ids and not (policy_group_ids & user_group_ids):
                return False
            return True

        def scope_weight(policy) -> tuple[int, int, int, int]:
            return (
                1 if policy.action_id else 0,
                1 if policy.view_id else 0,
                1 if policy.company_id else 0,
                len(policy.role_group_ids),
            )

        return sorted([rec for rec in records if applies(rec)], key=lambda rec: (*scope_weight(rec), rec.sequence or 0, rec.id))

    def _apply_layout_policy(self, nodes: list, effective: dict[str, dict[str, Any]]) -> list:
        hidden = {name for name, rule in effective.items() if not rule.get("visible")}
        result = []
        for raw in nodes:
            if not isinstance(raw, dict):
                continue
            node = dict(raw)
            node_type = str(node.get("type") or "").strip().lower()
            field_name = str(node.get("name") or "").strip()
            if node_type == "field" and field_name in hidden:
                continue
            if node_type == "field" and field_name in effective:
                if effective[field_name].get("visible"):
                    self._force_visible_node(node)
                label = str(effective[field_name].get("label") or "").strip()
                if label:
                    node["string"] = label
                    node["label"] = label
                    field_info = node.get("fieldInfo")
                    if isinstance(field_info, dict):
                        field_info["label"] = label
            for child_key in ("children", "pages", "tabs", "nodes", "items"):
                children = node.get(child_key)
                if isinstance(children, list):
                    node[child_key] = self._apply_layout_policy(children, effective)
            result.append(node)
        return result

    def _append_visible_policy_fields(self, layout: list, visible: set[str], effective: dict[str, dict[str, Any]]) -> None:
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
        missing = [name for name in visible if name not in existing]
        missing.sort(key=lambda name: (effective[name].get("sequence") or 100, name))
        if not missing:
            return
        target = self._find_sheet(layout)
        parent = target.setdefault("children", []) if target is not None else layout
        grouped: dict[str, list[str]] = {}
        for name in missing:
            group_title = str(effective[name].get("group_title") or "业务配置字段").strip() or "业务配置字段"
            grouped.setdefault(group_title, []).append(name)
        sorted_groups = sorted(
            grouped.items(),
            key=lambda item: (min(effective[name].get("sequence") or 100 for name in item[1]), item[0]),
        )
        for index, (group_title, field_names) in enumerate(sorted_groups, start=1):
            parent.append({
                "type": "group",
                "name": "business_config_field_policy_group_%s" % index,
                "string": group_title,
                "children": [
                    {
                        "type": "field",
                        "name": name,
                        "fieldInfo": effective[name].get("field_info") or {"name": name, "label": name, "type": "char"},
                        **({"string": effective[name]["label"], "label": effective[name]["label"]} if effective[name].get("label") else {}),
                    }
                    for name in field_names
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

    def _field_contract_info(self, meta: dict, label: str = "") -> dict:
        field_type = str(meta.get("type") or "char")
        return {
            "name": str(meta.get("name") or ""),
            "label": label or str(meta.get("string") or ""),
            "type": field_type,
            "required": bool(meta.get("required")),
            "readonly": bool(meta.get("readonly")),
            "invisible": False,
            "help": str(meta.get("help") or ""),
            "widget": field_type,
            "domain": meta.get("domain") or [],
            "context": meta.get("context") or {},
            "selection": meta.get("selection") or [],
            "colspan": 1,
        }

    def _force_visible_node(self, node: dict) -> None:
        node.pop("invisible", None)
        modifiers = node.get("modifiers")
        if isinstance(modifiers, dict):
            modifiers.pop("invisible", None)
        attributes = node.get("attributes")
        if isinstance(attributes, dict):
            attributes.pop("invisible", None)
            attr_modifiers = attributes.get("modifiers")
            if isinstance(attr_modifiers, dict):
                attr_modifiers.pop("invisible", None)
        field_info = node.get("fieldInfo")
        if isinstance(field_info, dict):
            field_info["invisible"] = False
            info_modifiers = field_info.get("modifiers")
            if isinstance(info_modifiers, dict):
                info_modifiers.pop("invisible", None)
