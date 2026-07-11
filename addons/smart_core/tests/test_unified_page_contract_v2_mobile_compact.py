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

    def test_ui_contract_v2_uses_head_title_as_page_name(self):
        source = {
            "model": "project.project",
            "view_type": "form",
            "head": {"title": "项目"},
            "fields": {
                "name": {"name": "name", "type": "char", "string": "项目名称"},
            },
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.form.head.title",
        )

        self.assertEqual(full["pageInfo"]["pageName"], "项目")

    def test_top_level_header_buttons_project_to_form_header(self):
        source = {
            "model": "project.project",
            "view_type": "form",
            "head": {"title": "项目"},
            "fields": {
                "name": {"name": "name", "type": "char", "string": "项目名称"},
            },
            "header_buttons": [
                {
                    "name": "action_submit",
                    "label": "提交",
                    "kind": "object",
                    "payload": {"method": "action_submit", "type": "object"},
                }
            ],
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.form.top.level.header.buttons",
        )

        header = full["layoutContract"]["containerTree"][0]
        self.assertEqual(header["type"], "header")
        self.assertEqual(header["children"][0]["type"], "button")
        self.assertEqual(header["children"][0]["name"], "action_submit")
        self.assertEqual(header["children"][0]["label"], "提交")

    def test_data_source_and_formal_metadata_projection_carry_source_authority(self):
        source = {
            "model": "project.project",
            "view_type": "form",
            "head": {"title": "项目"},
            "fields": {
                "name": {"name": "name", "type": "char", "string": "项目名称"},
            },
            "business_operation_profile": {
                "source": "test",
                "common_fields": ["name"],
            },
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.form.data.source.authority",
        )

        primary = full["dataContract"]["dataSource"]["primary"]
        self.assertEqual(primary["sourceAuthority"]["runtime_carrier"], "ui.contract.v2.dataContract.dataSource")
        self.assertTrue(primary["sourceAuthority"]["projection_only"])
        self.assertTrue(primary["sourceAuthority"]["no_business_fact_authority"])
        profile = full["dataContract"]["dataMeta"]["businessOperationProfile"]
        self.assertEqual(profile["sourceAuthority"]["runtime_carrier"], "ui.contract.v2.dataMeta.businessOperationProfile")
        self.assertTrue(profile["sourceAuthority"]["projection_only"])
        self.assertTrue(profile["sourceAuthority"]["no_business_fact_authority"])
        self.assertTrue(profile["sourceAuthority"]["formal_projection"])
        self.assertNotIn("legacyContractProjection", full["dataContract"]["dataMeta"])

    def test_form_data_source_keeps_deep_form_fields(self):
        fields = {
            f"field_{index}": {
                "name": f"field_{index}",
                "type": "char",
                "string": f"字段{index}",
            }
            for index in range(70)
        }
        source = {
            "model": "construction.contract.income",
            "view_type": "form",
            "fields": fields,
            "record_id": 991,
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.form.deep.fields",
        )

        requested_fields = full["dataContract"]["dataSource"]["primary"]["params"]["fields"]
        self.assertIn("field_69", requested_fields)
        self.assertGreater(len(requested_fields), 40)

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

    def _source_with_form_structure_summary(self, render_profile):
        return {
            "model": "tender.doc.purchase",
            "view_type": "form",
            "render_profile": render_profile,
            "head": {"render_profile": render_profile},
            "fields": {
                "invoice_no": {"name": "invoice_no", "type": "char", "string": "发票号/凭证号"},
                "amount": {"name": "amount", "type": "monetary", "string": "金额", "readonly": False},
                "bid_id": {"name": "bid_id", "type": "many2one", "string": "投标", "readonly": False},
                "receipt_partner_name": {"name": "receipt_partner_name", "type": "char", "string": "历史/快照收款单位", "readonly": True},
                "legacy_state": {"name": "legacy_state", "type": "char", "string": "历史状态", "readonly": True},
                "legacy_source_user": {"name": "legacy_source_user", "type": "char", "string": "历史录入人", "readonly": True},
            },
            "form_structure_contract": {
                "source": "ui.contract.v2.form_structure_contract",
                "viewType": "form",
                "slots": [
                    {
                        "slot": "overview",
                        "title": "办理总览",
                        "fieldRefs": ["invoice_no", "amount"],
                    },
                    {
                        "slot": "primary_facts",
                        "title": "主业务事实",
                        "groups": [
                            {"name": "identity", "title": "申请信息", "fieldRefs": ["bid_id", "receipt_partner_name"]},
                        ],
                    },
                    {
                        "slot": "amount_progress",
                        "title": "金额与进度",
                        "groups": [
                            {"name": "amounts", "title": "金额信息", "fieldRefs": ["amount"]},
                        ],
                    },
                    {
                        "slot": "details_source",
                        "title": "明细与来源",
                        "groups": [
                            {
                                "name": "history_check",
                                "title": "历史核对信息",
                                "role": "history_check",
                                "fieldRefs": ["legacy_state", "legacy_source_user"],
                            },
                        ],
                    },
                ],
            },
        }

    def test_form_structure_create_layout_starts_with_task_not_summary(self):
        full = assembler.assemble_unified_page_contract_v2(
            self._source_with_form_structure_summary("create"),
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.create.form.no.summary.first",
        )

        sheet = full["layoutContract"]["containerTree"][0]
        self.assertEqual([child["type"] for child in sheet["children"]], ["group", "group"])
        self.assertEqual([child["label"] for child in sheet["children"]], ["申请信息", "金额信息"])
        rendered_names = [
            node.get("name")
            for group in sheet["children"]
            for node in group.get("children", [])
        ]
        self.assertNotIn("receipt_partner_name", rendered_names)
        self.assertNotIn("legacy_state", rendered_names)
        self.assertNotIn("legacy_source_user", rendered_names)

    def test_form_structure_readonly_layout_keeps_summary_first(self):
        full = assembler.assemble_unified_page_contract_v2(
            self._source_with_form_structure_summary("readonly"),
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.readonly.form.summary.first",
        )

        sheet = full["layoutContract"]["containerTree"][0]
        self.assertEqual(sheet["children"][0]["type"], "group")
        self.assertEqual(sheet["children"][0]["label"], "办理总览")
        self.assertEqual(sheet["children"][1]["type"], "notebook")
        tabs = sheet["children"][1]["tabs"]
        history_tab = next(tab for tab in tabs if tab["label"] == "明细与来源")
        history_fields = [
            node.get("name")
            for group in history_tab.get("children", [])
            for node in group.get("children", [])
        ]
        primary_tab = next(tab for tab in tabs if tab["label"] == "主业务事实")
        primary_fields = [
            node.get("name")
            for group in primary_tab.get("children", [])
            for node in group.get("children", [])
        ]
        self.assertIn("receipt_partner_name", primary_fields)
        self.assertIn("legacy_state", history_fields)
        self.assertIn("legacy_source_user", history_fields)

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

    def test_ui_contract_v2_preserves_tree_selection_options(self):
        source = {
            "model": "project.project",
            "view_type": "tree",
            "fields": {
                "name": {"name": "name", "type": "char", "string": "名称"},
                "operation_strategy": {
                    "name": "operation_strategy",
                    "type": "selection",
                    "string": "经营方式",
                    "selection": [["direct", "公司直营"], ["joint", "联营项目"]],
                },
                "lifecycle_state": {
                    "name": "lifecycle_state",
                    "type": "selection",
                    "string": "项目状态",
                    "selection": [["draft", "草稿"], ["in_progress", "在建"]],
                },
            },
            "views": {
                "tree": {
                    "columns": ["name", "operation_strategy", "lifecycle_state"],
                    "columns_schema": [
                        {"name": "name", "string": "名称", "type": "char"},
                        {"name": "operation_strategy", "string": "经营方式", "type": "selection"},
                        {"name": "lifecycle_state", "string": "项目状态", "type": "selection"},
                    ],
                },
            },
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.tree.selection.options",
        )

        widgets = [
            widget
            for container in full["layoutContract"]["containerTree"]
            for widget in container["widgetList"]
        ]
        by_field = {widget["fieldCode"]: widget for widget in widgets}
        self.assertEqual(
            by_field["operation_strategy"]["componentConfig"]["selection"],
            [["direct", "公司直营"], ["joint", "联营项目"]],
        )
        self.assertEqual(
            by_field["lifecycle_state"]["componentConfig"]["selection"],
            [["draft", "草稿"], ["in_progress", "在建"]],
        )

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

    def test_form_structure_contract_rebuilds_business_task_layout(self):
        source = {
            "model": "construction.contract.income",
            "view_type": "form",
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "header",
                            "name": "contract_header",
                            "children": [{"type": "button", "name": "action_confirm", "label": "提交"}],
                        },
                        {
                            "type": "sheet",
                            "name": "native_sheet",
                            "children": [
                                {
                                    "type": "group",
                                    "name": "native_group",
                                    "children": [{"type": "field", "name": "name"}],
                                }
                            ],
                        },
                        {
                            "type": "group",
                            "name": "hidden_native_group",
                            "children": [
                                {
                                    "type": "field",
                                    "name": "hidden_internal_note",
                                    "invisible": True,
                                    "modifiers": {"invisible": True},
                                }
                            ],
                        },
                    ]
                }
            },
            "fields": {
                "name": {"name": "name", "type": "char", "string": "编号"},
                "subject": {"name": "subject", "type": "char", "string": "标题"},
                "project_id": {"name": "project_id", "type": "many2one", "string": "项目"},
                "visible_contract_amount": {"name": "visible_contract_amount", "type": "monetary", "string": "合同金额"},
                "line_ids": {"name": "line_ids", "type": "one2many", "string": "明细"},
                "hidden_internal_note": {"name": "hidden_internal_note", "type": "char", "string": "隐藏内部说明"},
            },
            "form_structure_contract": {
                "source": "ui.contract.v2.form_structure_contract",
                "mode": "business_task_form",
                "navigation": {"title": "业务办理"},
                "fieldRoles": {
                    "subject": {"role": "identity", "slot": "primary_facts", "group": "identity"},
                    "line_ids": {"role": "detail", "slot": "details_source", "group": "details"},
                },
                "slots": [
                    {
                        "slot": "overview",
                        "title": "办理总览",
                        "readonly": True,
                        "fieldRefs": ["subject", "project_id", "visible_contract_amount"],
                    },
                    {
                        "slot": "primary_facts",
                        "title": "主业务事实",
                        "groups": [
                            {"name": "identity", "title": "业务识别", "fieldRefs": ["name", "subject"]},
                            {"name": "other_facts", "title": "基础信息", "fieldRefs": ["hidden_internal_note"]},
                        ],
                    },
                    {
                        "slot": "details_source",
                        "title": "明细与来源",
                        "groups": [
                            {"name": "details", "title": "业务明细", "fieldRefs": ["line_ids"]},
                        ],
                    },
                ],
            },
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.form.structure",
        )

        self.assertEqual(full["formStructureContract"]["source"], "ui.contract.v2.form_structure_contract")
        tree = full["layoutContract"]["containerTree"]
        self.assertEqual([node["type"] for node in tree], ["header", "sheet"])
        sheet_children = tree[1]["children"]
        self.assertEqual([node["type"] for node in sheet_children], ["group", "group"])
        self.assertEqual([node["label"] for node in sheet_children], ["业务识别", "业务明细"])
        self.assertEqual(sheet_children[0]["formStructure"]["slot"], "primary_facts")
        self.assertEqual(sheet_children[0]["formStructure"]["role"], "identity")
        self.assertEqual(sheet_children[0]["children"][1]["formStructureRole"]["role"], "identity")
        rendered_names = [
            node.get("name")
            for group in sheet_children
            for node in group.get("children", [])
        ]
        self.assertNotIn("hidden_internal_note", rendered_names)
        self.assertEqual(sheet_children[1]["children"][0]["name"], "line_ids")

    def test_governed_form_layout_overlay_takes_precedence_over_form_structure(self):
        source = {
            "model": "res.partner",
            "view_type": "form",
            "governance": {
                "view_orchestration": {
                    "applied": True,
                    "form_layout_overlay": True,
                }
            },
            "source_trace": {
                "view_orchestration": {
                    "form_layout_overlay": True,
                    "business_config_contracts": [{"id": 261, "name": "partner customer preference"}],
                }
            },
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "sheet",
                            "name": "sc_custom_partner_form_sheet",
                            "children": [
                                {
                                    "type": "group",
                                    "name": "sc_custom_partner_flat_fields",
                                    "columns": 3,
                                    "children": [
                                        {"type": "field", "name": "name", "label": "客户名称"},
                                        {"type": "field", "name": "company_type", "label": "客户类型"},
                                        {"type": "field", "name": "vat", "label": "统一社会信用代码"},
                                    ],
                                }
                            ],
                        }
                    ]
                }
            },
            "fields": {
                "name": {"name": "name", "type": "char", "string": "名称"},
                "company_type": {"name": "company_type", "type": "selection", "string": "客户类型"},
                "vat": {"name": "vat", "type": "char", "string": "税号"},
                "category_id": {"name": "category_id", "type": "many2many", "string": "标签"},
            },
            "form_structure_contract": {
                "source": "ui.contract.v2.form_structure_contract",
                "mode": "business_task_form",
                "fieldRoles": {
                    "category_id": {"role": "identity", "slot": "primary_facts", "group": "identity"},
                    "name": {"role": "identity", "slot": "primary_facts", "group": "identity"},
                },
                "slots": [
                    {
                        "slot": "primary_facts",
                        "title": "主业务事实",
                        "groups": [
                            {"name": "identity", "title": "业务识别", "fieldRefs": ["category_id", "name"]},
                        ],
                    },
                ],
            },
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.form.layout.overlay.precedence",
        )

        self.assertNotIn("formStructureContract", full)
        group = full["layoutContract"]["containerTree"][0]["children"][0]
        self.assertEqual(group["name"], "sc_custom_partner_flat_fields")
        self.assertEqual(group["columns"], 3)
        self.assertEqual(
            [node["name"] for node in group["children"]],
            ["name", "company_type", "vat"],
        )

    def test_form_structure_contract_preserves_configured_group_columns(self):
        source = {
            "model": "res.partner",
            "view_type": "form",
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "sheet",
                            "children": [
                                {
                                    "type": "group",
                                    "name": "native_group",
                                    "cols": 2,
                                    "children": [
                                        {"type": "field", "name": "name"},
                                        {"type": "field", "name": "company_type"},
                                        {"type": "field", "name": "vat"},
                                    ],
                                }
                            ],
                        }
                    ]
                }
            },
            "fields": {
                "name": {"name": "name", "type": "char", "string": "名称"},
                "company_type": {"name": "company_type", "type": "selection", "string": "客户类型"},
                "vat": {"name": "vat", "type": "char", "string": "税号"},
            },
            "form_structure_contract": {
                "source": "ui.contract.v2.form_structure_contract",
                "mode": "business_task_form",
                "slots": [
                    {
                        "slot": "configured_form",
                        "title": "表单字段",
                        "groups": [
                            {
                                "name": "configured_group_1",
                                "title": "基础信息",
                                "cols": 3,
                                "fieldRefs": ["name", "company_type", "vat"],
                            },
                        ],
                    },
                ],
            },
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.form.structure.configured.columns",
        )

        group = full["layoutContract"]["containerTree"][0]["children"][0]
        self.assertEqual(group["label"], "基础信息")
        self.assertEqual(group["cols"], 3)
        self.assertEqual(group["attributes"]["col"], "3")

    def test_form_structure_columns_apply_to_governed_form_layout(self):
        source = {
            "model": "res.partner",
            "view_type": "form",
            "governance": {
                "view_orchestration": {
                    "applied": True,
                    "form_layout_overlay": True,
                }
            },
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "sheet",
                            "children": [
                                {
                                    "type": "group",
                                    "name": "configured_business_fields",
                                    "string": "业务配置字段",
                                    "columns": 3,
                                    "children": [
                                        {"type": "field", "name": "name"},
                                        {"type": "field", "name": "company_type"},
                                    ],
                                }
                            ],
                        }
                    ]
                }
            },
            "fields": {
                "name": {"name": "name", "type": "char", "string": "名称"},
                "company_type": {"name": "company_type", "type": "selection", "string": "客户类型"},
            },
            "form_structure_contract": {
                "source": "ui.contract.v2.form_structure_contract",
                "mode": "business_task_form",
                "columns": 2,
                "slots": [
                    {
                        "slot": "configured_form",
                        "title": "表单字段",
                        "groups": [
                            {
                                "name": "configured_group_1",
                                "title": "业务配置字段",
                                "fieldRefs": ["name", "company_type"],
                            },
                        ],
                    },
                ],
            },
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.form.structure.columns.overlay",
        )

        group = full["layoutContract"]["containerTree"][0]["children"][0]
        self.assertEqual(group["label"], "业务配置字段")
        self.assertEqual(group["cols"], 2)
        self.assertEqual(group["columns"], 2)
        self.assertEqual(group["attributes"]["col"], "2")

    def test_ui_contract_v2_preserves_relation_entry_search_dialog(self):
        search_dialog = {
            "columns": [
                {"name": "display_name", "label": "名称", "type": "char"},
                {"name": "phone", "label": "电话", "type": "char"},
            ],
            "read_fields": ["id", "display_name", "phone"],
            "order": "display_name asc",
            "limit": 120,
            "source": "relation_target_native_view",
        }
        source = {
            "model": "project.project",
            "view_type": "form",
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "sheet",
                            "name": "project_sheet",
                            "children": [
                                {
                                    "type": "group",
                                    "name": "project_core",
                                    "children": [{"type": "field", "name": "partner_id"}],
                                }
                            ],
                        }
                    ]
                }
            },
            "fields": {
                "partner_id": {
                    "name": "partner_id",
                    "type": "many2one",
                    "string": "客户",
                    "relation": "res.partner",
                    "relation_entry": {
                        "model": "res.partner",
                        "can_read": True,
                        "can_create": True,
                        "create_mode": "page",
                        "search_dialog": search_dialog,
                    },
                },
            },
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.relation.search.dialog",
        )

        field_node = full["layoutContract"]["containerTree"][0]["children"][0]["children"][0]
        self.assertEqual(
            field_node["fieldInfo"]["relation_entry"]["search_dialog"]["source"],
            "relation_target_native_view",
        )
        self.assertEqual(
            field_node["componentConfig"]["relationEntry"]["search_dialog"]["columns"][1]["name"],
            "phone",
        )
        widget = full["layoutContract"]["containerTree"][0]["children"][0]["widgetList"][0]
        self.assertEqual(
            widget["componentConfig"]["relationEntry"]["search_dialog"]["read_fields"],
            ["id", "display_name", "phone"],
        )

    def test_ui_contract_v2_uses_button_badge_display_label(self):
        source = {
            "model": "project.project",
            "view_type": "form",
            "record": {
                "tender_count": 0,
            },
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "sheet",
                            "name": "project_sheet",
                            "children": [
                                {
                                    "type": "button",
                                    "name": "564",
                                    "label": "投标管理",
                                    "buttonType": "action",
                                    "action": {
                                        "name": "564",
                                        "label": "投标管理",
                                        "kind": "open",
                                        "level": "smart",
                                        "selection": "none",
                                        "intent": "open",
                                        "payload": {
                                            "ref": "564",
                                            "type": "action",
                                        },
                                        "badge": {
                                            "kind": "statinfo",
                                            "field": "tender_count",
                                            "label": "投标",
                                        },
                                    },
                                },
                            ],
                        },
                    ]
                }
            },
            "fields": {
                "tender_count": {"name": "tender_count", "type": "integer", "string": "投标"},
            },
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.button.badge.label",
        )

        button = full["layoutContract"]["containerTree"][0]["children"][0]
        self.assertEqual(button["label"], "投标管理")
        self.assertEqual(button["displayLabel"], "0投标")
        self.assertEqual(button["action"]["displayLabel"], "0投标")

    def test_ui_contract_v2_preserves_search_filters_and_group_by(self):
        source = {
            "model": "project.project",
            "view_type": "tree",
            "views": {
                "tree": {
                    "fields": ["name", "manager_id", "lifecycle_state"],
                },
            },
            "fields": {
                "name": {"name": "name", "type": "char"},
                "manager_id": {"name": "manager_id", "type": "many2one", "relation": "res.users"},
                "lifecycle_state": {"name": "lifecycle_state", "type": "selection"},
            },
            "search": {
                "default_sort": "write_date desc",
                "filters": [
                    {"key": "filter_my_projects", "label": "我的项目", "domain_raw": "[('manager_id', '=', uid)]"},
                ],
                "saved_filters": [
                    {
                        "id": 7,
                        "name": "用户收藏",
                        "domain": [],
                        "context": {},
                        "owner": 16,
                        "is_shared": False,
                    },
                ],
                "group_by": [
                    {
                        "key": "group_manager",
                        "label": "按项目经理",
                        "field": "manager_id",
                        "context_raw": "{'group_by': 'manager_id'}",
                    },
                ],
                "fields": [{"field": "name", "label": "名称"}],
            },
        }

        full = assembler.assemble_unified_page_contract_v2(
            source,
            source_type="ui.contract",
            client_type="web_pc",
            request_id="test.web.search.contract",
        )

        self.assertEqual(full["searchContract"]["filters"][0]["key"], "filter_my_projects")
        self.assertEqual(full["searchContract"]["saved_filters"][0]["name"], "用户收藏")
        self.assertEqual(full["searchContract"]["group_by"][0]["field"], "manager_id")
        self.assertEqual(full["dataContract"]["search"]["default_sort"], "write_date desc")


if __name__ == "__main__":
    unittest.main()
