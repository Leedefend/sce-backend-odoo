from .base import BaseViewParser
from .native_view_node_schema import (
    build_action_node,
    build_chatter_node,
    build_field_node,
    build_group_node,
    build_notebook_node,
    build_page_node,
    build_ribbon_node,
    build_view_semantics,
)

import ast


class FormViewParser(BaseViewParser):
    def parse(self):
        view_info = self.get_view_info(fallback_view_type="form")
        arch = view_info["arch"]

        title_field = self._parse_title_field(arch)
        title_node = self._parse_title_node(arch)
        header_buttons = self._parse_header_buttons(arch)
        stat_buttons = self._parse_stat_buttons(arch)
        ribbon = self._parse_ribbon(arch)
        groups = self._parse_groups(arch.xpath(".//sheet"))  # 支持多层解析
        notebooks = self._parse_notebooks(arch)
        chatter = self._parse_chatter(arch)

        return {
            "titleField": title_field,
            "titleNode": title_node,
            "headerButtons": header_buttons,
            "statButtons": stat_buttons,
            "ribbon": ribbon,
            "groups": groups,
            "notebooks": notebooks,
            "chatter": chatter,
            "view_semantics": build_view_semantics(
                source_view="form",
                capability_flags={
                    "has_title": bool(title_node),
                    "has_header_buttons": bool(header_buttons),
                    "has_stat_buttons": bool(stat_buttons),
                    "has_ribbon": bool(ribbon),
                    "has_chatter": bool(chatter and (chatter.get("followers") or chatter.get("activities") or chatter.get("messages"))),
                    "has_notebooks": bool(notebooks),
                },
                semantic_meta={
                    "group_count": len(groups),
                    "notebook_count": len(notebooks),
                    "header_button_count": len(header_buttons),
                    "stat_button_count": len(stat_buttons),
                },
            ),
        }

    # ---------- 标题 ----------
    def _parse_title_field(self, arch):
        nodes = arch.xpath(".//div[contains(@class, 'oe_title')]//field")
        for node in nodes:
            if node.get("widget") != "boolean_favorite":
                return node.get("name")
        return nodes[0].get("name") if nodes else None

    def _parse_title_node(self, arch):
        nodes = arch.xpath(".//div[contains(@class, 'oe_title')]//field")
        target = None
        for node in nodes:
            if node.get("widget") != "boolean_favorite":
                target = node
                break
        if target is None and nodes:
            target = nodes[0]
        if target is None:
            return None
        return build_field_node(
            name=target.get("name"),
            string=target.get("string"),
            widget=target.get("widget"),
            semantic_role="form_title_field",
            source_view="form",
            semantic_meta={
                "is_title": True,
                "is_favorite_widget": target.get("widget") == "boolean_favorite",
            },
        )

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
            return build_ribbon_node(
                title=node.get("title"),
                bg_color=node.get("bg_color"),
                invisible=self._parse_condition(node.get("invisible")),
                semantic_role="form_ribbon",
                source_view="form",
                semantic_meta={
                    "has_bg_color": bool(node.get("bg_color")),
                    "has_visibility_rule": node.get("invisible") is not None,
                },
            )
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

        return build_group_node(
            fields=fields,
            sub_groups=sub_groups,
            attributes=self._parse_common_attrs(group_node),
            semantic_role="form_group",
            source_view="form",
            semantic_meta={
                "has_sub_groups": bool(sub_groups),
                "field_count": len(fields),
            },
        )

    def _parse_field_node(self, node):
        return build_field_node(
            name=node.get("name"),
            string=node.get("string"),
            widget=node.get("widget"),
            invisible=self._parse_condition(node.get("invisible")),
            required=self._parse_condition(node.get("required")),
            readonly=self._parse_condition(node.get("readonly")),
            placeholder=node.get("placeholder"),
            visible=True,
            editable=True,
            semantic_role="form_field",
            source_view="form",
            semantic_meta={
                "has_placeholder": bool(node.get("placeholder")),
                "has_widget": bool(node.get("widget")),
            },
        )

    # ---------- notebook ----------
    def _parse_notebooks(self, arch):
        notebooks = []
        for notebook in arch.xpath(".//notebook"):
            pages = []
            for page in notebook.xpath("./page"):
                pages.append(
                    build_page_node(
                        title=page.get("string"),
                        groups=self._parse_groups([page]),
                        visible=True,
                        semantic_role="form_page",
                        source_view="form",
                        semantic_meta={
                            "group_count": len(self._parse_groups([page])),
                        },
                    )
                )
            notebooks.append(
                build_notebook_node(
                    pages=pages,
                    semantic_role="form_notebook",
                    source_view="form",
                    semantic_meta={"page_count": len(pages)},
                )
            )
        return notebooks

    # ---------- chatter ----------
    def _parse_chatter(self, arch):
        chatter_fields = arch.xpath(".//div[contains(@class,'oe_chatter')]//field")
        followers = next((f.get("name") for f in chatter_fields if "follower" in f.get("name", "")), None)
        activities = next((f.get("name") for f in chatter_fields if "activity" in f.get("name", "")), None)
        messages = next((f.get("name") for f in chatter_fields if "message" in f.get("name", "")), None)
        return build_chatter_node(
            followers=followers,
            activities=activities,
            messages=messages,
            semantic_role="form_chatter",
            source_view="form",
            semantic_meta={
                "has_followers": bool(followers),
                "has_activities": bool(activities),
                "has_messages": bool(messages),
            },
        )

    # ---------- 按钮解析 ----------
    def _parse_button(self, node):
        button = build_action_node(
            name=node.get("name"),
            string=node.get("string"),
            action_type=node.get("type"),
            context=self._parse_context(node.get("context")),
            icon=node.get("icon"),
            groups=self._parse_groups_attr(node.get("groups")),
            hotkey=node.get("data-hotkey"),
            invisible=self._parse_condition(node.get("invisible")),
            visible=True,
            semantic_role="form_button",
            source_view="form",
            semantic_meta={
                "has_context": bool(node.get("context")),
                "has_hotkey": bool(node.get("data-hotkey")),
                "has_groups": bool(node.get("groups")),
            },
        )
        button["class"] = node.get("class")
        return button

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
