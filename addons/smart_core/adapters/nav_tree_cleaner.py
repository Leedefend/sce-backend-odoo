# -*- coding: utf-8 -*-
from __future__ import annotations


class NavTreeCleaner:
    SOURCE_KIND = "nav_tree_shape_cleaner"
    SOURCE_AUTHORITIES = ("navigation_tree_payload",)
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": "nav_tree_cleaner",
        }

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
