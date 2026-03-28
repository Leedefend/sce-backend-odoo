from __future__ import annotations

from lxml import etree
from odoo.exceptions import UserError


class NativeViewSourceLoader:
    def __init__(self, env, *, model=None, view_type=None, view_id=None, context=None):
        self.env = env
        self.model = model
        self.view_type = view_type or "form"
        self.view_id = view_id
        self.context = context or {}

    def load(self) -> dict:
        if not self.model:
            raise UserError("模型名称未指定")

        model_cls = self.env[self.model]
        try:
            view_info = model_cls.get_view(
                view_id=self.view_id,
                view_type=self.view_type,
                context=self.context,
            )
        except Exception as exc:
            raise UserError(f"无法加载 {self.view_type} 视图: {str(exc)}") from exc

        arch = view_info.get("arch")
        if isinstance(arch, str):
            view_info["arch"] = etree.fromstring(arch)
        return view_info
