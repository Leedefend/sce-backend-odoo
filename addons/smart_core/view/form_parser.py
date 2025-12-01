from .base import BaseViewParser

import ast


class FormViewParser(BaseViewParser):
    def parse(self):
        view_info = self.get_view_info(fallback_view_type="form")
        arch = view_info["arch"]

        return {
            "titleField": self._parse_title_field(arch),
            "headerButtons": self._parse_header_buttons(arch),
            "statButtons": self._parse_stat_buttons(arch),
            "ribbon": self._parse_ribbon(arch),
            "groups": self._parse_groups(arch.xpath(".//sheet")),  # 支持多层解析
            "notebooks": self._parse_notebooks(arch),
            "chatter": self._parse_chatter(arch)
        }

    # ---------- 标题 ----------
    def _parse_title_field(self, arch):
        nodes = arch.xpath(".//div[contains(@class, 'oe_title')]//field")
        for node in nodes:
            if node.get("widget") != "boolean_favorite":
                return node.get("name")
        return nodes[0].get("name") if nodes else None

    # ---------- header 按钮 ----------
    def _parse_header_buttons(self, arch):
        return [self._parse_button(btn) for btn in arch.xpath(".//header/button")]

    # ---------- stat 按钮 ----------
    def _parse_stat_buttons(self, arch):
        buttons = []
        for btn in arch.xpath(".//div[contains(@class, 'oe_button_box')]/button"):
            field_node = btn.xpath(".//field")
            field_name = field_node[0].get("name") if field_node else None
            data = self._parse_button(btn)
            data["field"] = field_name
            buttons.append(data)
        return buttons

    # ---------- ribbon ----------
    def _parse_ribbon(self, arch):
        ribbon = arch.xpath(".//widget[@name='web_ribbon']")
        if ribbon:
            node = ribbon[0]
            return {
                "title": node.get("title"),
                "bg_color": node.get("bg_color"),
                "invisible": self._parse_condition(node.get("invisible"))
            }
        return None

    # ---------- group 递归解析 ----------
    def _parse_groups(self, parent_nodes):
        """
        parent_nodes: 可能是 sheet 或 page 节点
        """
        groups = []
        for group_node in parent_nodes[0].xpath("./group") if parent_nodes else []:
            groups.append(self._parse_group_recursive(group_node))
        return groups

    def _parse_group_recursive(self, group_node):
        """
        支持 group 嵌套 group
        """
        # 当前 group 内字段
        fields = [self._parse_field_node(node) for node in group_node.xpath("./field")]

        # 子 group
        sub_groups = []
        for sub_group in group_node.xpath("./group"):
            sub_groups.append(self._parse_group_recursive(sub_group))

        return {
            "fields": fields,
            "sub_groups": sub_groups,
            "attributes": self._parse_common_attrs(group_node)
        }

    def _parse_field_node(self, node):
        return {
            "name": node.get("name"),
            "string": node.get("string"),
            "widget": node.get("widget"),
            "invisible": self._parse_condition(node.get("invisible")),
            "required": self._parse_condition(node.get("required")),
            "readonly": self._parse_condition(node.get("readonly")),
            "placeholder": node.get("placeholder"),
            "visible": True,
            "editable": True
        }

    # ---------- notebook ----------
    def _parse_notebooks(self, arch):
        notebooks = []
        for notebook in arch.xpath(".//notebook"):
            pages = []
            for page in notebook.xpath("./page"):
                pages.append({
                    "title": page.get("string"),
                    "groups": self._parse_groups([page]),
                    "visible": True
                })
            notebooks.append({"pages": pages})
        return notebooks

    # ---------- chatter ----------
    def _parse_chatter(self, arch):
        chatter_fields = arch.xpath(".//div[contains(@class,'oe_chatter')]//field")
        return {
            "followers": next((f.get("name") for f in chatter_fields if "follower" in f.get("name", "")), None),
            "activities": next((f.get("name") for f in chatter_fields if "activity" in f.get("name", "")), None),
            "messages": next((f.get("name") for f in chatter_fields if "message" in f.get("name", "")), None)
        }

    # ---------- 按钮解析 ----------
    def _parse_button(self, node):
        return {
            "name": node.get("name"),
            "string": node.get("string"),
            "type": node.get("type"),
            "class": node.get("class"),
            "context": self._parse_context(node.get("context")),
            "invisible": self._parse_condition(node.get("invisible")),
            "icon": node.get("icon"),
            "groups": self._parse_groups_attr(node.get("groups")),
            "hotkey": node.get("data-hotkey"),
            "visible": True
        }

    # ---------- 工具方法 ----------
    def _parse_context(self, ctx):
        if not ctx:
            return {}
        try:
            return ast.literal_eval(ctx)
        except Exception:
            return {"raw": ctx}

    def _parse_groups_attr(self, groups):
        if not groups:
            return []
        return [g.strip() for g in groups.split(",") if g.strip()]

    def _parse_common_attrs(self, node):
        """
        提取通用属性：class / name 等
        """
        return {
            "class": node.get("class"),
            "name": node.get("name")
        }

    def _parse_condition(self, expr):
        import re
        """
        将 invisible/required/readonly 等条件解析为结构化 JSON
        支持格式：
        - "field != 'portal'"
        - "field == value"
        - "field and other_field"
        """
        if expr in ("1", "true", "True"):
            return {"type": "boolean", "value": True}
        if expr in ("0", "false", "False", None):
            return {"type": "boolean", "value": False}

        # 支持多条件 (and/or)
        if " and " in expr or " or " in expr:
            parts = re.split(r"\s+(and|or)\s+", expr)
            conditions = []
            operator = None
            for part in parts:
                if part.lower() in ("and", "or"):
                    operator = part.lower()
                    continue
                conditions.append(self._parse_condition(part.strip()))
            return {"type": "compound", "operator": operator, "conditions": conditions}

        # 匹配单条件: field != 'value'
        pattern = re.compile(r"(\w+)\s*(==|!=|>|<|>=|<=)\s*('?[\w\s]+'?)")
        match = pattern.match(expr)
        if match:
            field, op, value = match.groups()
            return {
                "type": "expression",
                "field": field,
                "operator": op,
                "value": value.strip("'\"")
            }

        # 未知格式，保留原始值
        return {"type": "raw", "value": expr}
