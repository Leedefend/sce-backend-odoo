# -*- coding: utf-8 -*-
from __future__ import annotations


class NavTreeCleaner:
    @staticmethod
    def is_menu_node(node: dict) -> bool:
        return bool(node.get("menu_id") or node.get("children"))

    def clean(self, nodes: list) -> list:
        cleaned = []
        for node in nodes or []:
            if not self.is_menu_node(node):
                continue
            item = dict(node)
            item["children"] = self.clean(node.get("children") or [])
            cleaned.append(item)
        return cleaned
