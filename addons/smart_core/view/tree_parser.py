from __future__ import annotations

from .base import BaseViewParser


class TreeViewParser(BaseViewParser):
    def parse(self):
        view_info = self.get_view_info(fallback_view_type="tree")
        arch = view_info["arch"]

        fields = []
        for node in arch.xpath(".//field[@name]"):
            fields.append(
                {
                    "name": node.get("name"),
                    "string": node.get("string"),
                    "widget": node.get("widget"),
                    "optional": node.get("optional"),
                }
            )

        return {
            "columns": fields,
            "decorations": self._parse_decorations(arch),
            "editable": arch.get("editable"),
            "create": arch.get("create"),
            "delete": arch.get("delete"),
        }

    def _parse_decorations(self, arch):
        out = {}
        for key, value in arch.attrib.items():
            if key.startswith("decoration-") and value:
                out[key] = value
        return out
