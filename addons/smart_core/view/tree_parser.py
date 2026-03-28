from __future__ import annotations

from .base import BaseViewParser
from .native_view_node_schema import build_field_node, build_view_semantics


class TreeViewParser(BaseViewParser):
    def parse(self):
        view_info = self.get_view_info(fallback_view_type="tree")
        arch = view_info["arch"]

        fields = []
        for node in arch.xpath(".//field[@name]"):
            fields.append(
                build_field_node(
                    name=node.get("name"),
                    string=node.get("string"),
                    widget=node.get("widget"),
                    optional=node.get("optional"),
                    semantic_role="tree_column",
                    source_view="tree",
                    semantic_meta={
                        "has_widget": bool(node.get("widget")),
                        "is_optional": node.get("optional") is not None,
                    },
                )
            )

        return {
            "columns": fields,
            "decorations": self._parse_decorations(arch),
            "editable": arch.get("editable"),
            "create": arch.get("create"),
            "delete": arch.get("delete"),
            "view_semantics": build_view_semantics(
                source_view="tree",
                capability_flags={
                    "can_create": arch.get("create") not in ("0", "false", "False"),
                    "can_delete": arch.get("delete") not in ("0", "false", "False"),
                    "is_editable": bool(arch.get("editable")),
                },
                semantic_meta={
                    "editable_mode": arch.get("editable"),
                    "decoration_keys": sorted(self._parse_decorations(arch).keys()),
                },
            ),
        }

    def _parse_decorations(self, arch):
        out = {}
        for key, value in arch.attrib.items():
            if key.startswith("decoration-") and value:
                out[key] = value
        return out
