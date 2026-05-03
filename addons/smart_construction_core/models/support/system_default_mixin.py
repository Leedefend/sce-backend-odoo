# -*- coding: utf-8 -*-
from odoo import fields, models


class ScSystemDefaultMixin(models.AbstractModel):
    _name = "sc.system.default.mixin"
    _description = "系统默认兜底标记"

    sc_has_system_default = fields.Boolean(string="含系统默认值", readonly=True, copy=False, index=True)
    sc_system_default_fields = fields.Char(string="系统默认字段", readonly=True, copy=False)
    sc_system_default_note = fields.Text(
        string="系统默认说明",
        readonly=True,
        copy=False,
        default="系统默认值仅用于避免填单或级联创建被技术字段阻断，真实业务办理前需要补充完善。",
    )

    @classmethod
    def _sc_mark_system_defaults(cls, vals, field_names):
        names = [name for name in field_names if name]
        if not names:
            return
        existing = [name.strip() for name in (vals.get("sc_system_default_fields") or "").split(",") if name.strip()]
        merged = []
        for name in existing + names:
            if name not in merged:
                merged.append(name)
        vals["sc_has_system_default"] = True
        vals["sc_system_default_fields"] = ",".join(merged)
        vals.setdefault(
            "sc_system_default_note",
            "系统默认值仅用于避免填单或级联创建被技术字段阻断，真实业务办理前需要补充完善。",
        )
