from .base import BaseViewParser
from .base import parse_safe_context
from .native_view_node_schema import build_action_node, build_field_node


class KanbanViewParser(BaseViewParser):
    def parse(self):
        view_info = self.get_view_info(fallback_view_type="kanban")
        arch = view_info["arch"]
        kanban_node = arch if getattr(arch, "tag", None) == "kanban" else arch.find("kanban")

        if kanban_node is None:
            raise ValueError("Invalid kanban view: missing <kanban> root")

        return {
            "cards": self._parse_card_fields(arch),
            "actions": self._parse_actions(arch),
            "menu": self._parse_menu(arch),
            "group_by": kanban_node.get("default_group_by") or kanban_node.get("group_by"),
            "on_create": kanban_node.get("on_create"),
            "quick_create_view": kanban_node.get("quick_create_view"),
            "color_field": self._parse_color_field(arch),
            "create": kanban_node.get("create"),
            "delete": kanban_node.get("delete"),
            "raw_fields": sorted(self.extract_fields(arch)),
        }

    def _parse_card_fields(self, arch):
        cards = []
        for template in arch.xpath(".//t[@t-name='kanban-box']"):
            for field_node in template.xpath(".//field[@name]"):
                cards.append(
                    build_field_node(
                        name=field_node.get("name"),
                        widget=field_node.get("widget"),
                        options=parse_safe_context(field_node.get("options", "{}")),
                        semantic_role="kanban_card_field",
                        source_view="kanban",
                        semantic_meta={
                            "has_widget": bool(field_node.get("widget")),
                            "has_options": bool(field_node.get("options")),
                        },
                    )
                )
        return cards

    def _parse_actions(self, arch):
        actions = []
        for action_node in arch.xpath(".//a[@name]"):
            actions.append(
                build_action_node(
                    name=action_node.get("name"),
                    action_type=action_node.get("type"),
                    context=parse_safe_context(action_node.get("t-attf-context", "{}")),
                    semantic_role="kanban_card_action",
                    source_view="kanban",
                    semantic_meta={
                        "has_context": bool(action_node.get("t-attf-context")),
                        "target_scope": "card",
                    },
                )
            )
        return actions

    def _parse_menu(self, arch):
        menu_template = arch.xpath(".//t[@t-name='kanban-menu']")
        if not menu_template:
            return {"items": []}

        items = []
        for item in menu_template[0].xpath(".//a[@name]"):
            items.append(
                build_action_node(
                    name=item.get("name"),
                    action_type=item.get("type"),
                    context=parse_safe_context(item.get("t-attf-context", "{}")),
                    semantic_role="kanban_menu_action",
                    source_view="kanban",
                    semantic_meta={
                        "has_context": bool(item.get("t-attf-context")),
                        "target_scope": "menu",
                    },
                )
            )
        return {"items": items}

    def _parse_color_field(self, arch):
        color_nodes = arch.xpath(".//field[@name='color']")
        if color_nodes:
            return "color"
        return None
