from __future__ import annotations

from .base import BaseViewParser
from .base import parse_safe_context


class SearchViewParser(BaseViewParser):
    def parse(self):
        view_info = self.get_view_info(fallback_view_type="search")
        arch = view_info["arch"]

        return {
            "fields": self._parse_fields(arch),
            "filters": self._parse_filters(arch),
            "group_bys": self._parse_group_bys(arch),
            "searchpanel": self._parse_searchpanel(arch),
        }

    def _parse_fields(self, arch):
        fields = []
        for node in arch.xpath(".//field[@name]"):
            fields.append(
                {
                    "name": node.get("name"),
                    "string": node.get("string"),
                    "operator": node.get("operator"),
                    "filter_domain": node.get("filter_domain"),
                }
            )
        return fields

    def _parse_filters(self, arch):
        filters = []
        for node in arch.xpath(".//filter[@name]"):
            filters.append(
                {
                    "name": node.get("name"),
                    "string": node.get("string"),
                    "domain": node.get("domain"),
                    "context": parse_safe_context(node.get("context", "{}")),
                }
            )
        return filters

    def _parse_group_bys(self, arch):
        group_bys = []
        for node in arch.xpath(".//filter[@context]"):
            context = parse_safe_context(node.get("context", "{}"))
            if isinstance(context, dict) and context.get("group_by"):
                group_bys.append(
                    {
                        "name": node.get("name"),
                        "string": node.get("string"),
                        "group_by": context.get("group_by"),
                    }
                )
        return group_bys

    def _parse_searchpanel(self, arch):
        sections = []
        for node in arch.xpath(".//searchpanel/field[@name]"):
            sections.append(
                {
                    "name": node.get("name"),
                    "string": node.get("string"),
                    "select": node.get("select"),
                    "icon": node.get("icon"),
                }
            )
        return sections
