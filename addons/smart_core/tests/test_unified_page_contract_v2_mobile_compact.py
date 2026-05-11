# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "core"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


sys.modules.setdefault("odoo", types.ModuleType("odoo"))
sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
core_pkg.__path__ = [str(CORE_DIR)]
smart_core_pkg.core = core_pkg

assembler = _load_module(
    "odoo.addons.smart_core.core.unified_page_contract_v2_assembler",
    CORE_DIR / "unified_page_contract_v2_assembler.py",
)
client = _load_module(
    "odoo.addons.smart_core.core.unified_page_contract_v2_client",
    CORE_DIR / "unified_page_contract_v2_client.py",
)


class TestUnifiedPageContractV2MobileCompact(unittest.TestCase):
    def test_mobile_compact_preserves_create_business_context_outside_compat(self):
        source = {
            "model": "project.project",
            "view_type": "form",
            "head": {
                "render_profile": "create",
                "context": {
                    "default_manager_id": 43,
                    "default_user_id": 43,
                    "default_phase_key": "initiation",
                    "sc_return_to_overview": 1,
                },
            },
            "fields": {
                "name": {"name": "name", "type": "char"},
                "manager_id": {"name": "manager_id", "type": "many2one"},
                "user_id": {"name": "user_id", "type": "many2one"},
                "phase_key": {"name": "phase_key", "type": "selection"},
            },
            "context_raw": "{'default_manager_id': uid, 'default_phase_key': 'initiation'}",
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="harmony_h5",
            request_id="test.mobile.compact.create",
        )
        trimmed = client.trim_unified_page_contract_v2(
            full,
            client_type="harmony_h5",
            delivery_profile="mobile_compact",
        )

        data_contract = trimmed["dataContract"]
        source_context = data_contract["dataMeta"]["sourceContext"]
        self.assertEqual(source_context["renderProfile"], "create")
        self.assertEqual(source_context["context"]["default_phase_key"], "initiation")
        self.assertEqual(data_contract["mainData"]["manager_id"], 43)
        self.assertEqual(data_contract["mainData"]["user_id"], 43)
        self.assertEqual(data_contract["mainData"]["phase_key"], "initiation")
        self.assertEqual(trimmed["statusContract"]["globalStatus"]["pageAuth"], "edit")

    def test_ui_contract_v2_edit_form_page_auth_follows_write_permission(self):
        source = {
            "model": "project.project",
            "view_type": "form",
            "head": {
                "render_profile": "edit",
                "permissions": {
                    "read": True,
                    "write": True,
                    "create": True,
                    "unlink": False,
                },
            },
            "fields": {
                "name": {"name": "name", "type": "char", "readonly": False},
                "partner_id": {"name": "partner_id", "type": "many2one", "readonly": False},
            },
            "record_id": 771,
            "render_profile": "edit",
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.edit.auth",
        )

        self.assertEqual(full["statusContract"]["globalStatus"]["pageAuth"], "edit")

    def test_ui_contract_v2_readonly_form_page_auth_stays_read(self):
        source = {
            "model": "project.project",
            "view_type": "form",
            "head": {
                "render_profile": "readonly",
                "permissions": {
                    "read": True,
                    "write": True,
                    "create": True,
                    "unlink": False,
                },
            },
            "fields": {
                "name": {"name": "name", "type": "char", "readonly": False},
            },
            "record_id": 771,
            "render_profile": "readonly",
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.readonly.auth",
        )

        self.assertEqual(full["statusContract"]["globalStatus"]["pageAuth"], "read")

    def test_ui_contract_v2_preserves_tree_column_optional_hide(self):
        source = {
            "model": "hr.department",
            "view_type": "tree",
            "fields": {
                "name": {"name": "name", "type": "char", "string": "部门名称"},
                "create_uid": {"name": "create_uid", "type": "many2one", "string": "创建人"},
                "create_date": {"name": "create_date", "type": "datetime", "string": "创建日期"},
            },
            "views": {
                "tree": {
                    "columns": ["name", "create_uid", "create_date"],
                    "columns_schema": [
                        {"name": "name", "string": "部门名称", "type": "char"},
                        {
                            "name": "create_uid",
                            "string": "创建人",
                            "type": "many2one",
                            "optional": "hide",
                        },
                        {
                            "name": "create_date",
                            "string": "创建日期",
                            "type": "datetime",
                            "optional": "hide",
                        },
                    ],
                },
            },
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.tree.optional.hide",
        )

        widgets = [
            widget
            for container in full["layoutContract"]["containerTree"]
            for widget in container["widgetList"]
        ]
        by_field = {widget["fieldCode"]: widget for widget in widgets}
        self.assertEqual(by_field["create_uid"]["componentConfig"]["optional"], "hide")
        self.assertEqual(by_field["create_date"]["componentConfig"]["optional"], "hide")
        status = {row["widgetId"]: row for row in full["statusContract"]["widgetStatus"]}
        self.assertTrue(status[by_field["create_uid"]["widgetId"]]["visible"])
        self.assertTrue(status[by_field["create_date"]["widgetId"]]["visible"])

    def test_web_pc_drops_source_compat_when_not_requested(self):
        source = {
            "model": "project.project",
            "view_type": "form",
            "fields": {
                "name": {"name": "name", "type": "char", "string": "名称"},
            },
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.no.compat",
        )
        trimmed = client.trim_unified_page_contract_v2(
            full,
            client_type="web_pc",
            delivery_profile="full",
        )
        self.assertNotIn("compat", trimmed["meta"])

    def test_ui_contract_v2_preserves_native_form_layout_tree(self):
        source = {
            "model": "project.project",
            "view_type": "form",
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "header",
                            "name": "project_header",
                            "children": [
                                {
                                    "type": "button",
                                    "name": "action_submit",
                                    "label": "提交",
                                    "buttonType": "object",
                                }
                            ],
                        },
                        {
                            "type": "sheet",
                            "name": "project_sheet",
                            "children": [
                                {
                                    "type": "group",
                                    "name": "project_core",
                                    "string": "基础信息",
                                    "children": [
                                        {"type": "field", "name": "name"},
                                        {"type": "field", "name": "manager_id", "fieldInfo": {"label": "项目经理"}},
                                    ],
                                },
                                {
                                    "type": "notebook",
                                    "name": "project_tabs",
                                    "tabs": [
                                        {
                                            "type": "page",
                                            "name": "settings_page",
                                            "string": "设置",
                                            "children": [
                                                {
                                                    "type": "group",
                                                    "name": "settings_group",
                                                    "children": [
                                                        {"type": "field", "name": "company_id"},
                                                    ],
                                                }
                                            ],
                                        }
                                    ],
                                },
                            ],
                        },
                    ]
                }
            },
            "fields": {
                "name": {"name": "name", "type": "char", "string": "名称"},
                "manager_id": {"name": "manager_id", "type": "many2one", "string": "项目经理"},
                "company_id": {"name": "company_id", "type": "many2one", "string": "公司"},
            },
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.native.form.tree",
        )

        tree = full["layoutContract"]["containerTree"]
        self.assertEqual([node["type"] for node in tree], ["header", "sheet"])
        self.assertEqual(tree[1]["children"][0]["type"], "group")
        self.assertEqual(tree[1]["children"][1]["type"], "notebook")
        self.assertEqual(tree[1]["children"][1]["tabs"][0]["type"], "page")
        core_group = tree[1]["children"][0]
        self.assertEqual([node["name"] for node in core_group["children"]], ["name", "manager_id"])
        self.assertEqual([widget["fieldCode"] for widget in core_group["widgetList"]], ["name", "manager_id"])
        page_group = tree[1]["children"][1]["tabs"][0]["children"][0]
        self.assertEqual([node["name"] for node in page_group["children"]], ["company_id"])
        self.assertEqual(page_group["children"][0]["fieldInfo"]["label"], "公司")


if __name__ == "__main__":
    unittest.main()
