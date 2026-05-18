# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


class _ElementWrapper:
    def __init__(self, element):
        self._element = element
        self.tag = element.tag
        self.attrib = element.attrib

    def get(self, key, default=None):
        return self._element.get(key, default)

    def xpath(self, expr):
        if expr.startswith(".//"):
            tag = expr[3:]
            attr = None
            if "[@" in tag and tag.endswith("]"):
                tag, attr = tag[:-1].split("[@", 1)
            rows = []
            for item in self._element.iter(tag):
                if attr and item.get(attr) is None:
                    continue
                rows.append(_ElementWrapper(item))
            return rows
        return []


def _install_lxml_shim():
    if "lxml" in sys.modules:
        return
    try:
        import lxml  # noqa: F401
        return
    except Exception:
        pass

    etree = types.SimpleNamespace()
    etree.fromstring = lambda raw: _ElementWrapper(ET.fromstring(raw.decode("utf-8") if isinstance(raw, bytes) else raw))
    etree.tostring = lambda node, encoding="unicode": ET.tostring(node._element, encoding=encoding)
    lxml_mod = types.ModuleType("lxml")
    lxml_mod.etree = etree
    sys.modules["lxml"] = lxml_mod
    sys.modules["lxml.etree"] = etree


def _load_calendar_mixin():
    _install_lxml_shim()
    root = Path(__file__).resolve().parents[1]
    module_path = root / "app_config_engine" / "services" / "view_Parser" / "parsers_Calendar_Gantt Activity.py"
    spec = importlib.util.spec_from_file_location("calendar_gantt_activity_parser_probe", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._CalendarGanttActivitySearchParserMixin


class _ParserProbe(_load_calendar_mixin()):
    def _safe_eval_expr(self, expr):
        try:
            return eval(expr, {"__builtins__": {}}, {})
        except Exception:
            return None


class TestNativeViewParserSurfaces(unittest.TestCase):
    def setUp(self):
        self.parser = _ParserProbe()

    def test_calendar_parser_preserves_native_slots_and_fields(self):
        result = self.parser._parse_calendar_view(
            """
            <calendar date_start="planned_start" date_stop="planned_stop" color="user_id" default_scale="week">
                <field name="name" string="Title"/>
                <field name="user_id" string="Owner"/>
            </calendar>
            """
        )

        self.assertEqual(result["date_slots"]["start"], "planned_start")
        self.assertEqual(result["date_slots"]["stop"], "planned_stop")
        self.assertEqual(result["color_slots"]["color"], "user_id")
        self.assertEqual([row["name"] for row in result["fields"]], ["name", "user_id"])
        self.assertEqual(result["native_attrs"]["default_scale"], "week")

    def test_gantt_parser_preserves_dependency_and_resource_slots(self):
        result = self.parser._parse_gantt_view(
            """
            <gantt date_start="start_date" date_stop="end_date" default_group_by="employee_id" dependency_field="depends_on_ids">
                <field name="name"/>
                <field name="employee_id"/>
            </gantt>
            """
        )

        self.assertEqual(result["date_slots"]["start"], "start_date")
        self.assertEqual(result["resource_slots"]["group_by"], "employee_id")
        self.assertEqual(result["dependency_slots"]["dependency_field"], "depends_on_ids")
        self.assertEqual([row["name"] for row in result["fields"]], ["name", "employee_id"])

    def test_search_parser_preserves_search_fields_and_group_by_metadata(self):
        result = self.parser._parse_search_from_arch(
            """
            <search>
                <field name="partner_id" string="Customer" operator="ilike"/>
                <filter name="mine" string="Mine" domain="[('user_id', '=', uid)]"/>
                <filter name="by_user" string="By User" context="{'group_by': 'user_id'}"/>
            </search>
            """
        )

        self.assertEqual(result["search_fields"][0]["name"], "partner_id")
        self.assertEqual(result["filters"][0]["name"], "mine")
        self.assertEqual(result["group_by"], ["user_id"])
        self.assertEqual(result["group_by_fields"][0]["field"], "user_id")


if __name__ == "__main__":
    unittest.main()
