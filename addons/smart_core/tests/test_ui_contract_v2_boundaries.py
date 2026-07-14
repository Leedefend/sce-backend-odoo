# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, su_env=None, request=None, params=None, context=None, payload=None):
        self.env = env
        self.su_env = su_env
        self.request = request
        self.params = params or {}
        self.context = context or {}
        self.payload = payload or {}


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


class _ElementWrapper:
    def __init__(self, element):
        self._element = element
        self.tag = element.tag
        self.attrib = element.attrib

    def get(self, key, default=None):
        return self._element.get(key, default)

    def xpath(self, expr):
        if not expr.startswith(".//"):
            return []
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


def _install_lxml_shim():
    if "lxml" in sys.modules:
        return
    try:
        import lxml  # noqa: F401
        return
    except Exception:
        pass

    etree = types.SimpleNamespace()
    etree._Element = _ElementWrapper
    etree.fromstring = lambda raw: _ElementWrapper(ET.fromstring(raw.decode("utf-8") if isinstance(raw, bytes) else raw))
    etree.tostring = lambda node, encoding="unicode": ET.tostring(node._element, encoding=encoding)
    lxml_mod = types.ModuleType("lxml")
    lxml_mod.etree = etree
    sys.modules["lxml"] = lxml_mod
    sys.modules["lxml.etree"] = etree


def _load_handler():
    _install_lxml_shim()
    root = Path(__file__).resolve().parents[1]
    _install_module("odoo")
    _install_module("odoo.addons")
    smart_core_mod = _install_module("odoo.addons.smart_core")
    handlers_mod = _install_module("odoo.addons.smart_core.handlers")
    core_mod = _install_module("odoo.addons.smart_core.core")
    utils_mod = _install_module("odoo.addons.smart_core.utils")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]
    utils_mod.__path__ = [str(root / "utils")]

    _install_module("odoo.addons.smart_core.core.base_handler", BaseIntentHandler=_BaseIntentHandler)
    _install_module("odoo.addons.smart_core.utils.extension_hooks", call_extension_hook_first=lambda *args, **kwargs: None)
    _install_module(
        "odoo.addons.smart_core.core.scene_provider",
        load_scenes_from_db_or_fallback=lambda *args, **kwargs: {
            "scenes": [{"key": "workspace.home", "title": "Home"}]
        },
    )
    captured = {}

    def _assemble_unified_page_contract_v2(source, *args, **kwargs):
        captured["assembler_source"] = dict(source or {})
        return {"pageInfo": {}, "meta": {}}

    _install_module(
        "odoo.addons.smart_core.core.unified_page_contract_v2_assembler",
        CONTRACT_VERSION="2.0",
        assemble_unified_page_contract_v2=_assemble_unified_page_contract_v2,
    )

    def _trim_unified_page_contract_v2(contract, **kwargs):
        captured["trim_kwargs"] = kwargs
        return {"contract": contract, "trim_kwargs": kwargs}

    _install_module(
        "odoo.addons.smart_core.core.unified_page_contract_v2_client",
        MOBILE_CLIENT_TYPES={"wx_mini", "harmony_h5"},
        resolve_client_type=lambda headers, params: "wx_mini",
        resolve_delivery_profile=lambda client_type, params=None: "mobile_compact",
        trim_unified_page_contract_v2=_trim_unified_page_contract_v2,
    )

    for module_name, rel_path in (
        ("odoo.addons.smart_core.core.intent_execution_result", "core/intent_execution_result.py"),
        ("odoo.addons.smart_core.core.request_params", "core/request_params.py"),
    ):
        sys.modules.pop(module_name, None)
        spec = importlib.util.spec_from_file_location(module_name, root / rel_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

    class _UiContractHandler(_BaseIntentHandler):
        def handle(self, payload=None, ctx=None):
            captured.setdefault("ui_payloads", []).append(dict(payload or {}))
            return {
                "ok": True,
                "data": {
                    "model": "res.partner",
                    "view_type": "form",
                    "data": {"record": {"id": 42, "name": "ACME"}},
                },
                "meta": {},
            }

    _install_module("odoo.addons.smart_core.handlers.ui_contract", UiContractHandler=_UiContractHandler)

    module_name = "odoo.addons.smart_core.handlers.ui_contract_v2"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "ui_contract_v2.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    module._captured = captured
    return module


class TestUiContractV2Boundaries(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler()

    def test_rejects_invalid_max_widgets(self):
        handler = self.module.UiContractV2Handler(env=object())

        result = handler.handle(payload={"params": {"model": "res.partner", "max_widgets": "bad"}})

        self.assertFalse(result.ok)
        self.assertEqual(result.code, 400)
        self.assertEqual(result.error["message"], "max_widgets 无效")

    def test_rejects_zero_max_actions(self):
        handler = self.module.UiContractV2Handler(env=object())

        result = handler.handle(payload={"params": {"model": "res.partner", "maxActions": 0}})

        self.assertFalse(result.ok)
        self.assertEqual(result.code, 400)
        self.assertEqual(result.error["message"], "max_actions 无效")

    def test_passes_parsed_trim_limits(self):
        handler = self.module.UiContractV2Handler(env=object())

        result = handler.handle(
            payload={
                "params": {
                    "model": "res.partner",
                    "maxWidgets": "8",
                    "max_actions": "3",
                    "maxContainers": "2",
                }
            }
        )

        self.assertTrue(result.ok)
        trim_kwargs = self.module._captured["trim_kwargs"]
        self.assertEqual(trim_kwargs["max_widgets"], 8)
        self.assertEqual(trim_kwargs["max_actions"], 3)
        self.assertEqual(trim_kwargs["max_containers"], 2)

    def test_request_adapter_merges_nested_params_over_top_level_payload(self):
        handler = self.module.UiContractV2Handler(
            env=object(),
            params={"model": "fallback.model"},
        )

        params = handler._params({
            "model": "outer.model",
            "params": {
                "model": "inner.model",
                "viewType": "list",
            },
        })
        ui_params = handler._ui_contract_params(params)

        self.assertEqual(params["model"], "inner.model")
        self.assertEqual(ui_params["view_type"], "tree")
        self.assertEqual(ui_params["viewType"], "tree")
        self.assertEqual(ui_params["op"], "model")

    def test_projection_applies_field_policies_to_widget_status(self):
        handler = self.module.UiContractV2Handler(env=object())
        contract = {
            "statusContract": {
                "widgetStatus": [
                    {
                        "widgetId": "field.name",
                        "visible": True,
                        "readonly": False,
                        "required": False,
                        "disabled": False,
                        "auth": "edit",
                    }
                ]
            }
        }
        source = {
            "render_profile": "readonly",
            "field_policies": {
                "name": {"readonly_profiles": ["readonly"]},
                "amount": {"visible": False},
            },
        }

        handler._apply_field_policies_to_v2_status(contract, source)

        rows = {
            row["widgetId"]: row
            for row in contract["statusContract"]["widgetStatus"]
        }
        self.assertTrue(rows["field.name"]["readonly"])
        self.assertEqual(rows["field.name"]["auth"], "read")
        self.assertFalse(rows["field.amount"]["visible"])
        self.assertEqual(rows["field.amount"]["auth"], "none")

    def test_projection_marks_native_visible_layout_fields_editable(self):
        handler = self.module.UiContractV2Handler(env=object())
        contract = {
            "layoutContract": {
                "containerTree": [
                    {
                        "type": "group",
                        "children": [
                            {"type": "field", "name": "name"},
                            {"type": "field", "name": "hidden", "attributes": {"invisible": "1"}},
                        ],
                    }
                ]
            },
            "statusContract": {
                "widgetStatus": [
                    {
                        "widgetId": "field.name",
                        "visible": False,
                        "readonly": False,
                        "required": False,
                        "disabled": False,
                        "auth": "none",
                    },
                    {
                        "widgetId": "field.hidden",
                        "visible": False,
                        "readonly": False,
                        "required": False,
                        "disabled": False,
                        "auth": "none",
                    },
                ]
            },
        }

        handler._ensure_native_layout_widget_status_visible(contract)

        rows = {
            row["widgetId"]: row
            for row in contract["statusContract"]["widgetStatus"]
        }
        self.assertTrue(rows["field.name"]["visible"])
        self.assertEqual(rows["field.name"]["auth"], "edit")
        self.assertFalse(rows["field.hidden"]["visible"])

    def test_layout_governance_applies_group_columns_and_visibility(self):
        handler = self.module.UiContractV2Handler(env=object())
        source_contract = {
            "business_operation_profile": {
                "form_structure_governance": {
                    "form_columns": 3,
                    "group_columns": {"基础信息": 2},
                    "group_visibility": {"隐藏区": False},
                }
            }
        }
        node = {"type": "group", "string": "基础信息"}

        handler._apply_form_layout_governance_to_group(
            node,
            "基础信息",
            source_contract=source_contract,
        )

        self.assertEqual(handler._form_layout_governance_columns(source_contract), 3)
        self.assertEqual(handler._form_layout_governance_columns(source_contract, "基础信息"), 2)
        self.assertFalse(
            handler._form_layout_group_visible_from_governance(
                handler._form_layout_governance(source_contract),
                "隐藏区",
            )
        )
        self.assertEqual(node["cols"], 2)
        self.assertEqual(node["columns"], 2)
        self.assertEqual(node["attributes"]["col"], "2")

    def test_form_orchestration_reorders_legacy_visible_widget_list(self):
        class _Config:
            contract_json = {
                "view_orchestration": {
                    "views": {
                        "form": {
                            "fields": [
                                {"name": "legacy_visible_02", "sequence": 10},
                                {"name": "legacy_visible_01", "sequence": 20},
                            ]
                        }
                    }
                }
            }

        class _ContractModel:
            def _effective_view_orchestration_contracts(self, *args, **kwargs):
                return [_Config()]

        class _Env:
            def __contains__(self, key):
                return key == "ui.business.config.contract"

            def __getitem__(self, key):
                if key == "ui.business.config.contract":
                    return _ContractModel()
                raise KeyError(key)

        handler = self.module.UiContractV2Handler(env=_Env())
        contract = {
            "layoutContract": {
                "containerTree": [
                    {
                        "type": "header",
                        "widgetList": [],
                        "children": [],
                    }
                ]
            }
        }
        source = {
            "model": "project.material.plan",
            "action_id": 525,
            "list_profile": {
                "columns": ["legacy_visible_01", "legacy_visible_02", "legacy_visible_03"],
                "column_labels": {
                    "legacy_visible_01": "单据状态",
                    "legacy_visible_02": "单据编号",
                    "legacy_visible_03": "单据日期",
                },
            },
            "fields": {
                "legacy_visible_01": {"type": "char"},
                "legacy_visible_02": {"type": "char"},
                "legacy_visible_03": {"type": "char"},
            },
        }

        handler._apply_legacy_visible_list_layout(contract, source)

        widgets = contract["layoutContract"]["containerTree"][0]["widgetList"]
        self.assertEqual(
            [widget["fieldCode"] for widget in widgets],
            ["legacy_visible_02", "legacy_visible_01", "legacy_visible_03"],
        )

    def test_scene_contract_rejects_invalid_trim_limit(self):
        handler = self.module.UiContractV2Handler(env=object())

        result = handler.handle(
            payload={
                "params": {
                    "source_type": "scene_contract_v1",
                    "scene_key": "workspace.home",
                    "max_containers": "bad",
                }
            }
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.code, 400)
        self.assertEqual(result.error["message"], "max_containers 无效")

    def test_form_record_contract_requests_record_data(self):
        handler = self.module.UiContractV2Handler(env=object())

        result = handler.handle(
            payload={
                "params": {
                    "model": "res.partner",
                    "view_type": "form",
                    "record_id": 42,
                    "render_profile": "edit",
                }
            }
        )

        self.assertTrue(result.ok)
        payloads = self.module._captured["ui_payloads"]
        self.assertTrue(payloads)
        model_payloads = [row for row in payloads if row.get("op") == "model" or row.get("subject") == "model"]
        self.assertTrue(model_payloads)
        self.assertTrue(model_payloads[-1]["with_data"])

    def test_list_contract_does_not_request_record_data(self):
        handler = self.module.UiContractV2Handler(env=object())

        result = handler.handle(
            payload={
                "params": {
                    "model": "res.partner",
                    "view_type": "tree",
                    "record_id": 42,
                }
            }
        )

        self.assertTrue(result.ok)
        payloads = self.module._captured["ui_payloads"]
        self.assertTrue(payloads)
        model_payloads = [row for row in payloads if row.get("op") == "model" or row.get("subject") == "model"]
        self.assertTrue(model_payloads)
        self.assertFalse(model_payloads[-1].get("with_data"))

    def test_nested_source_record_is_promoted_to_v2_main_source(self):
        handler = self.module.UiContractV2Handler(env=object())

        result = handler.handle(
            payload={
                "params": {
                    "model": "res.partner",
                    "view_type": "form",
                    "record_id": 42,
                }
            }
        )

        self.assertTrue(result.ok)
        self.assertEqual(
            self.module._captured["assembler_source"]["record"],
            {"id": 42, "name": "ACME"},
        )

    def test_action_open_injects_action_window_domain_context_and_title(self):
        class _Action:
            id = 949
            name = "工程进度款收入登记"
            res_model = "sc.receipt.income"
            domain = "[('source_kind', '=', 'receipt_income'), ('receipt_type', '=', '工程进度收款')]"
            context = "{'default_source_kind': 'receipt_income', 'default_receipt_type': '工程进度收款'}"

            def exists(self):
                return True

        class _ActionModel:
            def sudo(self):
                return self

            def browse(self, action_id):
                self.action_id = action_id
                return _Action()

        class _Env:
            def __getitem__(self, model):
                if model != "ir.actions.act_window":
                    raise KeyError(model)
                return _ActionModel()

        handler = self.module.UiContractV2Handler(env=_Env())

        result = handler.handle(payload={"params": {"op": "action_open", "action_id": 949}})

        self.assertTrue(result.ok)
        source = self.module._captured["assembler_source"]
        self.assertEqual(source["action_id"], 949)
        self.assertEqual(source["model"], "sc.receipt.income")
        self.assertEqual(source["title"], "工程进度款收入登记")
        self.assertEqual(source["head"]["title"], "工程进度款收入登记")
        self.assertEqual(
            source["domain"],
            [("source_kind", "=", "receipt_income"), ("receipt_type", "=", "工程进度收款")],
        )
        self.assertEqual(source["context"]["default_receipt_type"], "工程进度收款")
        self.assertEqual(source["domain_raw"], _Action.domain)

    def test_business_list_profile_keeps_contract_ledger_fields_visible(self):
        handler = self.module.UiContractV2Handler(env=object())
        columns = [{"name": f"field_{index}"} for index in range(24)]
        columns.extend([
            {"name": "operation_strategy"},
            {"name": "entry_user_text"},
            {"name": "entry_time"},
            {"name": "contract_duration_text"},
            {"name": "contract_payment_method_text"},
            {"name": "attachment_text"},
            {"name": "visible_contract_amount"},
        ])
        source_contract = {
            "views": {"tree": {"columns": columns}},
            "list_profile": {},
        }

        handler._merge_business_list_profile(
            source_contract,
            common_fields=[],
            amount_fields=["visible_contract_amount"],
            note_field="",
            status_field="",
            label_for=lambda name: name,
            type_for=lambda name: "char",
        )

        profile_columns = source_contract["list_profile"]["columns"]
        self.assertEqual(len(profile_columns), 31)
        self.assertIn("operation_strategy", profile_columns)
        self.assertIn("entry_user_text", profile_columns)
        self.assertIn("entry_time", profile_columns)
        self.assertIn("contract_duration_text", profile_columns)
        self.assertIn("contract_payment_method_text", profile_columns)
        self.assertIn("attachment_text", profile_columns)
        self.assertIn("visible_contract_amount", profile_columns)
        self.assertEqual(
            source_contract["list_profile"]["preference_policy"]["must_request_columns"],
            profile_columns,
        )

    def test_business_list_profile_preserves_business_config_column_order(self):
        class _Config:
            contract_json = {
                "view_orchestration": {
                    "views": {
                        "tree": {
                            "columns": [
                                {"name": "state", "sequence": 10},
                                {"name": "name", "sequence": 10},
                                {"name": "project_id", "sequence": 10},
                            ]
                        }
                    }
                }
            }

        class _ConfigModel:
            def _effective_view_orchestration_contracts(self, model_name, view_type, action_id=0):
                self.request = (model_name, view_type, action_id)
                return [_Config()]

        class _Env(dict):
            def __contains__(self, key):
                return dict.__contains__(self, key)

        config_model = _ConfigModel()
        handler = self.module.UiContractV2Handler(env=_Env({
            "ui.business.config.contract": config_model,
        }))
        source_contract = {
            "action_id": 949,
            "model": "sc.demo",
            "views": {"tree": {"columns": [{"name": "id"}, {"name": "name"}]}},
            "list_profile": {},
        }

        handler._merge_business_list_profile(
            source_contract,
            common_fields=["fallback_field"],
            amount_fields=[],
            note_field="",
            status_field="",
            label_for=lambda name: name,
            type_for=lambda name: "char",
        )

        self.assertEqual(config_model.request, ("sc.demo", "tree", 949))
        self.assertEqual(
            source_contract["list_profile"]["columns"][:3],
            ["state", "name", "project_id"],
        )
        self.assertEqual(
            source_contract["views"]["tree"]["columns"][:3],
            ["state", "name", "project_id"],
        )

    def test_business_list_profile_keeps_configured_columns_with_duplicate_schema_labels(self):
        class _Config:
            contract_json = {
                "view_orchestration": {
                    "views": {
                        "tree": {
                            "columns": [
                                {"name": "entry_user_text", "sequence": 10},
                                {"name": "source_created_by", "sequence": 20},
                                {"name": "entry_time", "sequence": 30},
                                {"name": "source_created_at", "sequence": 40},
                            ]
                        }
                    }
                }
            }

        class _ConfigModel:
            def _effective_view_orchestration_contracts(self, model_name, view_type, action_id=0):
                return [_Config()]

        class _Env(dict):
            def __contains__(self, key):
                return dict.__contains__(self, key)

        labels = {
            "entry_user_text": "录入人",
            "source_created_by": "来源录入人",
            "entry_time": "录入时间",
            "source_created_at": "来源录入时间",
        }
        handler = self.module.UiContractV2Handler(env=_Env({
            "ui.business.config.contract": _ConfigModel(),
        }))
        source_contract = {
            "action_id": 949,
            "model": "sc.demo",
            "views": {
                "tree": {
                    "columns": [
                        "entry_user_text",
                        "source_created_by",
                        "entry_time",
                        "source_created_at",
                    ],
                    "columns_schema": [
                        {"name": "entry_user_text", "label": "录入人"},
                        {"name": "source_created_by", "label": "录入人"},
                        {"name": "entry_time", "label": "录入时间"},
                        {"name": "source_created_at", "label": "录入时间"},
                    ],
                }
            },
            "list_profile": {},
        }

        handler._merge_business_list_profile(
            source_contract,
            common_fields=[],
            amount_fields=[],
            note_field="",
            status_field="",
            label_for=lambda name: labels.get(name, name),
            type_for=lambda name: "char",
        )

        self.assertEqual(
            source_contract["list_profile"]["columns"],
            ["entry_user_text", "source_created_by", "entry_time", "source_created_at"],
        )

    def test_business_list_profile_prefers_config_over_legacy_visible_override(self):
        class _Config:
            contract_json = {
                "view_orchestration": {
                    "views": {
                        "tree": {
                            "columns": [
                                {"name": "p1_visible_a", "sequence": 10},
                                {"name": "p1_visible_b", "sequence": 20},
                                {"name": "source_created_by", "sequence": 30},
                                {"name": "source_created_at", "sequence": 40},
                            ]
                        }
                    }
                }
            }

        class _ConfigModel:
            def _effective_view_orchestration_contracts(self, model_name, view_type, action_id=0):
                return [_Config()]

        class _Env(dict):
            def __contains__(self, key):
                return dict.__contains__(self, key)

        handler = self.module.UiContractV2Handler(env=_Env({
            "ui.business.config.contract": _ConfigModel(),
        }))
        handler._scbs55_legacy_visible_list_override = lambda source_contract: {
            "columns": ["p1_visible_a", "p1_visible_b"],
            "column_labels": {"p1_visible_a": "单据状态", "p1_visible_b": "项目名称"},
        }
        source_contract = {
            "action_id": 856,
            "model": "sc.demo",
            "views": {
                "tree": {
                    "columns": ["p1_visible_a", "p1_visible_b", "source_created_by", "source_created_at"],
                }
            },
            "list_profile": {},
        }

        handler._merge_business_list_profile(
            source_contract,
            common_fields=[],
            amount_fields=[],
            note_field="",
            status_field="",
            label_for=lambda name: name,
            type_for=lambda name: "char",
        )

        self.assertEqual(
            source_contract["list_profile"]["columns"],
            ["p1_visible_a", "p1_visible_b", "source_created_by", "source_created_at"],
        )
        self.assertEqual(
            source_contract["list_profile"]["column_policy"]["reason"],
            "business_list_config_contract_authoritative",
        )

    def test_business_list_profile_does_not_append_native_tail_to_direct_config(self):
        class _Config:
            contract_json = {
                "view_orchestration": {
                    "views": {
                        "tree": {
                            "columns": [
                                {"name": "contract_name", "sequence": 10},
                                {"name": "contract_no", "sequence": 20},
                                {"name": "amount_total", "sequence": 30},
                            ]
                        }
                    }
                }
            }

        class _ConfigModel:
            def _effective_view_orchestration_contracts(self, model_name, view_type, action_id=0):
                return [_Config()]

        class _Env(dict):
            def __contains__(self, key):
                return dict.__contains__(self, key)

        handler = self.module.UiContractV2Handler(env=_Env({
            "ui.business.config.contract": _ConfigModel(),
        }))
        source_contract = {
            "action_id": 669,
            "model": "sc.general.contract",
            "views": {
                "tree": {
                    "columns": [
                        "contract_name",
                        "contract_no",
                        "amount_total",
                        "state",
                        "project_id",
                    ],
                }
            },
            "list_profile": {},
        }

        handler._merge_business_list_profile(
            source_contract,
            common_fields=[],
            amount_fields=[],
            note_field="",
            status_field="",
            label_for=lambda name: name,
            type_for=lambda name: "char",
        )

        self.assertEqual(
            source_contract["list_profile"]["columns"],
            ["contract_name", "contract_no", "amount_total"],
        )

    def test_business_list_profile_does_not_extend_direct_config_with_existing_profile(self):
        class _Config:
            contract_json = {
                "view_orchestration": {
                    "views": {
                        "tree": {
                            "columns": [
                                {"name": "legacy_visible_status", "sequence": 10},
                                {"name": "legacy_visible_project", "sequence": 20},
                                {"name": "source_created_by", "sequence": 30},
                            ]
                        }
                    }
                }
            }

        class _ConfigModel:
            def _effective_view_orchestration_contracts(self, model_name, view_type, action_id=0):
                return [_Config()]

        class _Env(dict):
            def __contains__(self, key):
                return dict.__contains__(self, key)

        handler = self.module.UiContractV2Handler(env=_Env({
            "ui.business.config.contract": _ConfigModel(),
        }))
        source_contract = {
            "action_id": 525,
            "model": "sc.material.plan",
            "views": {"tree": {"columns": []}},
            "list_profile": {
                "columns": ["name", "project_id", "state"],
                "column_labels": {"name": "名称", "project_id": "项目", "state": "状态"},
            },
        }

        handler._merge_business_list_profile(
            source_contract,
            common_fields=["name", "project_id", "state"],
            amount_fields=[],
            note_field="remark",
            status_field="state",
            label_for=lambda name: name,
            type_for=lambda name: "char",
        )

        self.assertEqual(
            source_contract["list_profile"]["columns"],
            ["legacy_visible_status", "legacy_visible_project", "source_created_by"],
        )
        self.assertEqual(
            source_contract["list_profile"]["column_policy"]["reason"],
            "business_list_config_contract_authoritative",
        )

    def test_business_list_config_projection_enforces_exact_final_columns(self):
        handler = self.module.UiContractV2Handler(env=object())
        source_contract = {
            "list_profile": {
                "columns": ["name", "source_created_by"],
                "fact_columns": ["name", "source_created_by"],
                "column_labels": {"name": "名称", "source_created_by": "来源录入人"},
                "column_policy": {
                    "mode": "strict",
                    "reason": "business_list_config_contract_authoritative",
                },
            }
        }
        contract = {
            "layoutContract": {
                "listProfile": {
                    "columns": ["name", "source_created_by", "governance_extra"],
                    "fact_columns": ["name", "source_created_by", "governance_extra"],
                }
            }
        }

        handler._enforce_business_list_config_projection(contract, source_contract)

        profile = contract["layoutContract"]["listProfile"]
        self.assertEqual(profile["columns"], ["name", "source_created_by"])
        self.assertEqual(profile["preference_policy"]["locked_columns"], [])
        self.assertTrue(profile["preference_policy"]["allow_visibility"])
        self.assertTrue(profile["preference_policy"]["allow_order"])
        self.assertEqual(profile["preference_policy"]["must_request_columns"], ["name", "source_created_by"])
        self.assertEqual(profile["sourceAuthority"]["source_key"], "list_profile.business_config_contract_authoritative")

    def test_business_list_config_projection_repairs_columns_from_fact_columns(self):
        handler = self.module.UiContractV2Handler(env=object())
        source_contract = {
            "list_profile": {
                "columns": ["legacy_visible_01", "legacy_visible_02"],
                "fact_columns": [
                    "legacy_visible_01",
                    "legacy_visible_02",
                    "source_created_by",
                    "source_created_at",
                ],
                "column_policy": {
                    "mode": "strict",
                    "reason": "business_list_config_contract_authoritative",
                },
            }
        }
        contract = {"layoutContract": {"listProfile": {"columns": ["legacy_visible_01", "legacy_visible_02"]}}}

        handler._enforce_business_list_config_projection(contract, source_contract)

        profile = contract["layoutContract"]["listProfile"]
        self.assertEqual(
            profile["columns"],
            ["legacy_visible_01", "legacy_visible_02", "source_created_by", "source_created_at"],
        )
        self.assertEqual(profile["preference_policy"]["locked_columns"], [])
        self.assertEqual(profile["preference_policy"]["must_request_columns"], profile["columns"])

    def test_material_plan_business_config_projection_labels_legacy_visible_columns(self):
        handler = self.module.UiContractV2Handler(env=object())
        source_contract = {
            "model": "project.material.plan",
            "list_profile": {
                "columns": ["legacy_visible_01", "legacy_visible_05", "source_created_by"],
                "column_labels": {
                    "legacy_visible_01": "历史验收可见字段01",
                    "legacy_visible_05": "历史验收可见字段05",
                    "source_created_by": "来源录入人",
                },
                "column_policy": {
                    "mode": "strict",
                    "reason": "business_list_config_contract_authoritative",
                },
            },
        }
        contract = {"layoutContract": {"listProfile": {}}}

        handler._enforce_business_list_config_projection(contract, source_contract)

        labels = contract["layoutContract"]["listProfile"]["column_labels"]
        self.assertEqual(labels["legacy_visible_01"], "单据状态")
        self.assertEqual(labels["legacy_visible_05"], "采购材料名称")
        self.assertEqual(labels["source_created_by"], "来源录入人")

    def test_material_plan_legacy_visible_widget_layout_uses_business_labels(self):
        handler = self.module.UiContractV2Handler(env={})
        contract = {
            "layoutContract": {
                "containerTree": [
                    {
                        "type": "table",
                        "widgetList": [],
                        "children": [],
                    }
                ]
            }
        }
        source = {
            "model": "project.material.plan",
            "list_profile": {
                "columns": ["legacy_visible_01", "legacy_visible_05"],
                "column_labels": {
                    "legacy_visible_01": "历史验收可见字段01",
                    "legacy_visible_05": "历史验收可见字段05",
                },
            },
            "fields": {
                "legacy_visible_01": {"type": "char", "string": "历史验收可见字段01"},
                "legacy_visible_05": {"type": "char", "string": "历史验收可见字段05"},
            },
        }

        handler._apply_legacy_visible_list_layout(contract, source)

        widgets = contract["layoutContract"]["containerTree"][0]["widgetList"]
        self.assertEqual([item["label"] for item in widgets], ["单据状态", "采购材料名称"])

    def test_material_inbound_business_config_projection_labels_legacy_visible_columns(self):
        handler = self.module.UiContractV2Handler(env=object())
        source_contract = {
            "model": "sc.material.inbound",
            "list_profile": {
                "columns": ["legacy_visible_01", "legacy_visible_02", "legacy_visible_05", "source_created_by"],
                "column_labels": {
                    "legacy_visible_01": "历史验收可见字段01",
                    "legacy_visible_02": "历史验收可见字段02",
                    "legacy_visible_05": "历史验收可见字段05",
                    "source_created_by": "来源录入人",
                },
                "column_policy": {
                    "mode": "strict",
                    "reason": "business_list_config_contract_authoritative",
                },
            },
        }
        contract = {"layoutContract": {"listProfile": {}}}

        handler._enforce_business_list_config_projection(contract, source_contract)

        labels = contract["layoutContract"]["listProfile"]["column_labels"]
        self.assertEqual(labels["legacy_visible_01"], "单据状态")
        self.assertEqual(labels["legacy_visible_02"], "入库单号")
        self.assertEqual(labels["legacy_visible_05"], "材料名称")
        self.assertEqual(labels["source_created_by"], "来源录入人")

    def test_material_inbound_legacy_visible_widget_layout_uses_business_labels(self):
        handler = self.module.UiContractV2Handler(env={})
        contract = {
            "layoutContract": {
                "containerTree": [
                    {
                        "type": "table",
                        "widgetList": [],
                        "children": [],
                    }
                ]
            }
        }
        source = {
            "model": "sc.material.inbound",
            "list_profile": {
                "columns": ["legacy_visible_02", "legacy_visible_05"],
                "column_labels": {
                    "legacy_visible_02": "历史验收可见字段02",
                    "legacy_visible_05": "历史验收可见字段05",
                },
            },
            "fields": {
                "legacy_visible_02": {"type": "char", "string": "历史验收可见字段02"},
                "legacy_visible_05": {"type": "char", "string": "历史验收可见字段05"},
            },
        }

        handler._apply_legacy_visible_list_layout(contract, source)

        widgets = contract["layoutContract"]["containerTree"][0]["widgetList"]
        self.assertEqual([item["label"] for item in widgets], ["入库单号", "材料名称"])

    def test_ui_contract_params_normalizes_list_view_to_tree_source(self):
        handler = self.module.UiContractV2Handler(env=object())

        params = handler._ui_contract_params({
            "op": "model",
            "model": "sc.material.inbound",
            "view_type": "list",
            "viewType": "list",
        })

        self.assertEqual(params["view_type"], "tree")
        self.assertEqual(params["viewType"], "tree")

    def test_form_structure_contract_uses_generic_slots_not_contract_template(self):
        handler = self.module.UiContractV2Handler(env=object())
        field_types = {
            "name": "char",
            "subject": "char",
            "project_id": "many2one",
            "partner_id": "many2one",
            "date_contract": "date",
            "engineering_address": "char",
            "visible_contract_amount": "monetary",
            "received_amount": "monetary",
            "document_status": "selection",
            "approval_info": "char",
            "entry_user_text": "char",
            "entry_time": "datetime",
            "line_ids": "one2many",
        }

        def unique(items):
            out = []
            seen = set()
            for item in items:
                value = str(item or "").strip()
                if value and value in field_types and value not in seen:
                    seen.add(value)
                    out.append(value)
            return out

        structure = handler._build_form_structure_contract(
            model="construction.contract.income",
            profile={
                "common_fields": list(field_types.keys())[:-1],
                "amount_fields": ["visible_contract_amount", "received_amount"],
                "date_fields": ["date_contract", "entry_time"],
                "status_field": "document_status",
                "note_field": "",
                "attachment_field": "",
                "detail_fields": ["line_ids"],
                "source_section_titles": ["Source Section"],
            },
            field_type=lambda name: field_types.get(name, "char"),
            unique=unique,
        )

        slot_titles = [slot["title"] for slot in structure["slots"]]
        self.assertEqual(slot_titles, ["办理总览", "主业务事实", "金额与进度", "办理协作", "明细与来源"])
        self.assertNotIn("合同事实", slot_titles)
        self.assertNotIn("工程与合同约定", slot_titles)
        self.assertEqual(structure["layoutPolicy"], "overview_then_task_slots")
        self.assertEqual(structure["source"], "ui.contract.v2.form_structure_contract")
        self.assertNotIn("businessSectionAliases", structure)
        self.assertEqual(structure["sourceSectionTitles"], ["Source Section"])
        self.assertEqual(structure["fieldRoles"]["engineering_address"]["role"], "term")
        self.assertEqual(structure["fieldRoles"]["visible_contract_amount"]["slot"], "amount_progress")
        self.assertEqual(structure["fieldRoles"]["line_ids"]["group"], "details")
        self.assertIn("engineering_address", structure["slots"][1]["groups"][2]["fieldRefs"])
        self.assertEqual(structure["slots"][2]["groups"][0]["title"], "金额信息")
        self.assertIn("line_ids", structure["slots"][4]["groups"][0]["fieldRefs"])

    def test_platform_contract_has_no_model_specific_business_section_registry(self):
        self.assertFalse(hasattr(self.module, "BUSINESS_FORM_SECTION_ALIASES_BY_MODEL"))
        self.assertFalse(hasattr(self.module, "BUSINESS_FORM_STRUCTURE_P1_VISIBLE_FIELD_MODELS"))

    def test_form_structure_contract_places_history_fields_in_check_group(self):
        handler = self.module.UiContractV2Handler(env=object())
        field_types = {
            "project_id": "many2one",
            "amount": "monetary",
            "p1_visible_8fa8662ad38f": "char",
            "p1_visible_3e7255522b33": "char",
            "legacy_status": "char",
        }

        def unique(items):
            out = []
            seen = set()
            for item in items:
                value = str(item or "").strip()
                if value and value in field_types and value not in seen:
                    seen.add(value)
                    out.append(value)
            return out

        structure = handler._build_form_structure_contract(
            model="payment.request",
            profile={
                "common_fields": list(field_types.keys()),
                "amount_fields": ["amount"],
                "date_fields": [],
                "status_field": "legacy_status",
                "note_field": "",
                "attachment_field": "",
                "detail_fields": [],
                "field_labels": {
                    "p1_visible_8fa8662ad38f": "单据编号",
                    "p1_visible_3e7255522b33": "项目名称",
                    "legacy_status": "历史状态",
                },
            },
            field_type=lambda name: field_types.get(name, "char"),
            unique=unique,
        )

        history_group = None
        primary_refs = []
        for slot in structure["slots"]:
            if slot["slot"] == "primary_facts":
                for group in slot.get("groups") or []:
                    primary_refs.extend(group.get("fieldRefs") or [])
            if slot["slot"] == "details_source":
                history_group = next(
                    (group for group in slot.get("groups") or [] if group.get("name") == "history_check"),
                    None,
                )

        self.assertIsNotNone(history_group)
        self.assertEqual(
            history_group["fieldRefs"],
            ["p1_visible_8fa8662ad38f", "p1_visible_3e7255522b33", "legacy_status"],
        )
        self.assertNotIn("p1_visible_8fa8662ad38f", primary_refs)
        self.assertNotIn("legacy_status", primary_refs)

    def test_form_structure_contract_promotes_formalized_migration_business_fields(self):
        handler = self.module.UiContractV2Handler(env=object())
        field_types = {
            "name": "char",
            "legacy_owner_unit": "char",
            "legacy_source_created_at": "char",
            "legacy_attachment_ref": "char",
        }

        def unique(items):
            out = []
            seen = set()
            for item in items:
                value = str(item or "").strip()
                if value and value in field_types and value not in seen:
                    seen.add(value)
                    out.append(value)
            return out

        structure = handler._build_form_structure_contract(
            model="project.project",
            profile={
                "common_fields": list(field_types.keys()),
                "amount_fields": [],
                "date_fields": [],
                "status_field": "",
                "note_field": "",
                "attachment_field": "",
                "detail_fields": [],
                "field_labels": {
                    "name": "项目名称",
                    "legacy_owner_unit": "业主单位",
                    "legacy_source_created_at": "历史录入时间",
                    "legacy_attachment_ref": "历史附件引用",
                },
            },
            field_type=lambda name: field_types.get(name, "char"),
            unique=unique,
        )

        roles = structure["fieldRoles"]
        self.assertEqual(roles["legacy_owner_unit"]["slot"], "primary_facts")
        self.assertEqual(roles["legacy_owner_unit"]["group"], "other_facts")
        self.assertEqual(roles["legacy_source_created_at"]["slot"], "details_source")
        self.assertEqual(roles["legacy_source_created_at"]["group"], "history_check")
        self.assertEqual(roles["legacy_attachment_ref"]["slot"], "details_source")
        self.assertEqual(roles["legacy_attachment_ref"]["group"], "history_check")

    def test_form_structure_governance_hidden_rows_override_duplicate_migration_fields(self):
        class _Field:
            def __init__(self, field_type, string="", relation=""):
                self.type = field_type
                self.string = string
                self.comodel_name = relation

        class _Model:
            _fields = {
                "owner_id": _Field("many2one", "业主单位", "res.partner"),
                "legacy_owner_unit": _Field("char", "业主单位名称"),
                "owner_contact": _Field("char", "业主联系人"),
                "legacy_owner_contact": _Field("char", "业主联系人姓名"),
            }

            def fields_get(self, names):
                return {
                    name: {
                        "type": field.type,
                        "string": field.string,
                        "relation": field.comodel_name,
                    }
                    for name, field in self._fields.items()
                    if name in names
                }

        class _Env:
            def __contains__(self, model):
                return model == "project.project"

            def __getitem__(self, model):
                if model != "project.project":
                    raise KeyError(model)
                return _Model()

        handler = self.module.UiContractV2Handler(env=_Env())
        source_contract = {
            "fields": {
                "owner_id": {"name": "owner_id", "type": "many2one", "string": "业主单位"},
                "legacy_owner_unit": {"name": "legacy_owner_unit", "type": "char", "string": "业主单位名称"},
                "owner_contact": {"name": "owner_contact", "type": "char", "string": "业主联系人"},
                "legacy_owner_contact": {"name": "legacy_owner_contact", "type": "char", "string": "业主联系人姓名"},
            },
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "group",
                            "children": [
                                {"type": "field", "name": "owner_id"},
                                {"type": "field", "name": "legacy_owner_unit"},
                                {"type": "field", "name": "owner_contact"},
                                {"type": "field", "name": "legacy_owner_contact"},
                            ],
                        }
                    ]
                }
            },
            "governance": {
                "view_orchestration": {
                    "applied": True,
                    "business_config_contracts": [{"id": 7, "name": "project-form", "version_no": 1}],
                    "fields": [
                        {"name": "owner_id", "sequence": 10},
                        {"name": "legacy_owner_unit", "sequence": 20},
                        {"name": "owner_contact", "sequence": 30},
                        {"name": "legacy_owner_contact", "sequence": 40},
                        {"name": "legacy_owner_unit", "sequence": 900, "visible": False},
                        {"name": "legacy_owner_contact", "sequence": 910, "visible": False},
                    ],
                }
            },
        }

        handler._inject_business_operation_contract(
            source_contract,
            model="project.project",
            view_type="form",
        )

        roles = source_contract["form_structure_contract"]["fieldRoles"]
        self.assertIn("owner_id", roles)
        self.assertIn("owner_contact", roles)
        self.assertNotIn("legacy_owner_unit", roles)
        self.assertNotIn("legacy_owner_contact", roles)
        visible_fields = source_contract["business_operation_profile"]["form_structure_common_fields"]
        self.assertEqual(visible_fields, ["owner_id", "owner_contact"])

    def test_form_structure_contract_does_not_fallback_to_wide_profile_fields(self):
        handler = self.module.UiContractV2Handler(env=object())
        field_types = {
            "subject": "char",
            "project_id": "many2one",
            "company_id": "many2one",
            "line_ids": "one2many",
            "review_ids": "one2many",
        }

        def unique(items):
            out = []
            seen = set()
            for item in items:
                value = str(item or "").strip()
                if value and value in field_types and value not in seen:
                    seen.add(value)
                    out.append(value)
            return out

        structure = handler._build_form_structure_contract(
            model="demo.business",
            profile={
                "common_fields": ["subject", "project_id", "company_id"],
                "detail_fields": ["line_ids", "review_ids"],
                "form_structure_common_fields": ["subject", "project_id"],
                "form_structure_detail_fields": ["line_ids"],
                "amount_fields": [],
                "date_fields": [],
                "status_field": "",
                "note_field": "",
                "attachment_field": "",
            },
            field_type=lambda name: field_types.get(name, "char"),
            unique=unique,
        )

        refs = []
        for slot in structure["slots"]:
            refs.extend(slot.get("fieldRefs") or [])
            for group in slot.get("groups") or []:
                refs.extend(group.get("fieldRefs") or [])
        self.assertIn("subject", refs)
        self.assertIn("project_id", refs)
        self.assertIn("line_ids", refs)
        self.assertNotIn("company_id", refs)
        self.assertNotIn("review_ids", refs)

    def test_business_operation_projection_uses_source_form_fields_for_generic_object(self):
        class _Field:
            def __init__(self, field_type, string="", relation=""):
                self.type = field_type
                self.string = string
                self.comodel_name = relation

        class _Model:
            _fields = {
                "expense_title": _Field("char", "事项"),
                "employee_id": _Field("many2one", "经办人", "hr.employee"),
                "business_purpose": _Field("char", "事由"),
                "total_amount": _Field("monetary", "金额"),
                "state": _Field("selection", "状态"),
                "line_ids": _Field("one2many", "明细"),
                "access_token": _Field("char", "访问令牌"),
                "alias_id": _Field("many2one", "别名", "mail.alias"),
                "dashboard_graph_data": _Field("char", "看板图表"),
                "is_favorite": _Field("boolean", "收藏"),
                "source_origin": _Field("char", "来源"),
                "document_no": _Field("char", "隐藏单据号"),
                "hidden_internal_note": _Field("char", "隐藏内部说明"),
                "validation_status": _Field("char", "校验状态"),
                "legacy_amount_source": _Field("char", "金额来源"),
                "legacy_counterparty_text": _Field("char", "历史往来单位"),
                "name_short": _Field("char", "简称"),
                "my_activity_date_deadline": _Field("date", "活动截止"),
                "review_ids": _Field("one2many", "审批记录"),
                "create_uid": _Field("many2one", "创建人", "res.users"),
            }

            def fields_get(self, names):
                return {
                    name: {
                        "type": field.type,
                        "string": field.string,
                        "relation": field.comodel_name,
                    }
                    for name, field in self._fields.items()
                    if name in names
                }

        class _Env:
            def __contains__(self, model):
                return model == "sc.expense.claim"

            def __getitem__(self, model):
                if model != "sc.expense.claim":
                    raise KeyError(model)
                return _Model()

        handler = self.module.UiContractV2Handler(env=_Env())
        source_contract = {
            "fields": {
                "expense_title": {"name": "expense_title", "type": "char", "string": "事项"},
                "employee_id": {"name": "employee_id", "type": "many2one", "string": "经办人"},
                "business_purpose": {"name": "business_purpose", "type": "char", "string": "事由"},
                "total_amount": {"name": "total_amount", "type": "monetary", "string": "金额"},
                "state": {"name": "state", "type": "selection", "string": "状态"},
                "line_ids": {"name": "line_ids", "type": "one2many", "string": "明细"},
                "access_token": {"name": "access_token", "type": "char", "string": "访问令牌"},
                "alias_id": {"name": "alias_id", "type": "many2one", "string": "别名"},
                "dashboard_graph_data": {"name": "dashboard_graph_data", "type": "char", "string": "看板图表"},
                "is_favorite": {"name": "is_favorite", "type": "boolean", "string": "收藏"},
                "source_origin": {"name": "source_origin", "type": "char", "string": "来源"},
                "document_no": {"name": "document_no", "type": "char", "string": "隐藏单据号"},
                "hidden_internal_note": {"name": "hidden_internal_note", "type": "char", "string": "隐藏内部说明"},
                "validation_status": {"name": "validation_status", "type": "char", "string": "校验状态"},
                "legacy_amount_source": {"name": "legacy_amount_source", "type": "char", "string": "金额来源"},
                "legacy_counterparty_text": {"name": "legacy_counterparty_text", "type": "char", "string": "历史往来单位"},
                "name_short": {"name": "name_short", "type": "char", "string": "简称"},
                "my_activity_date_deadline": {
                    "name": "my_activity_date_deadline",
                    "type": "date",
                    "string": "活动截止",
                },
                "review_ids": {"name": "review_ids", "type": "one2many", "string": "审批记录"},
            },
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "sheet",
                            "children": [
                                {
                                    "type": "group",
                                    "children": [
                                        {"type": "field", "name": "expense_title"},
                                        {"type": "field", "name": "employee_id"},
                                        {"type": "field", "name": "business_purpose"},
                                        {"type": "field", "name": "total_amount"},
                                        {"type": "field", "name": "state"},
                                        {"type": "field", "name": "line_ids"},
                                        {"type": "field", "name": "access_token"},
                                        {"type": "field", "name": "alias_id"},
                                        {"type": "field", "name": "dashboard_graph_data"},
                                        {"type": "field", "name": "is_favorite"},
                                        {"type": "field", "name": "source_origin"},
                                        {"type": "field", "name": "validation_status"},
                                        {"type": "field", "name": "legacy_amount_source"},
                                        {"type": "field", "name": "legacy_counterparty_text"},
                                        {"type": "field", "name": "name_short"},
                                        {"type": "field", "name": "my_activity_date_deadline"},
                                        {"type": "field", "name": "review_ids"},
                                    ],
                                }
                            ],
                        }
                    ]
                }
            },
            "visible_fields": ["expense_title", "document_no", "hidden_internal_note"],
            "governance": {
                "view_orchestration": {
                    "applied": True,
                    "owner_layer": "business_view_orchestration",
                    "business_config_contracts": [{"id": 1, "name": "expense-form", "version_no": 1}],
                }
            },
            "source_trace": {
                "view_orchestration": {
                    "owner_layer": "business_view_orchestration",
                    "business_config_contracts": [{"id": 1, "name": "expense-form", "version_no": 1}],
                    "legacy_field_policy_overlay": False,
                }
            },
        }

        handler._inject_business_operation_contract(
            source_contract,
            model="sc.expense.claim",
            view_type="form",
        )

        profile = source_contract["business_operation_profile"]
        self.assertIn("expense_title", profile["common_fields"])
        self.assertIn("business_purpose", profile["common_fields"])
        self.assertIn("total_amount", profile["amount_fields"])
        self.assertIn("line_ids", profile["detail_fields"])
        self.assertNotIn("create_uid", profile["common_fields"])
        roles = source_contract["form_structure_contract"]["fieldRoles"]
        self.assertEqual(roles["employee_id"]["group"], "relations")
        self.assertEqual(roles["business_purpose"]["group"], "other_facts")
        self.assertEqual(roles["total_amount"]["slot"], "amount_progress")
        self.assertEqual(roles["line_ids"]["group"], "details")
        self.assertNotIn("access_token", roles)
        self.assertNotIn("alias_id", roles)
        self.assertNotIn("dashboard_graph_data", roles)
        self.assertNotIn("is_favorite", roles)
        self.assertNotIn("source_origin", roles)
        self.assertNotIn("document_no", roles)
        self.assertNotIn("hidden_internal_note", roles)
        self.assertNotIn("validation_status", roles)
        self.assertNotIn("legacy_amount_source", roles)
        self.assertNotIn("legacy_counterparty_text", roles)
        self.assertNotIn("name_short", roles)
        self.assertNotIn("my_activity_date_deadline", roles)
        self.assertNotIn("review_ids", roles)
        self.assertEqual(source_contract["visible_fields"], ["expense_title", "document_no", "hidden_internal_note"])
        self.assertIn("form_structure_governance", profile)
        self.assertTrue(
            source_contract["form_structure_contract"]["sourceAuthority"]["governed_form_structure"]
        )

    def test_form_structure_contract_requires_view_governance(self):
        class _Field:
            def __init__(self, field_type, string="", relation=""):
                self.type = field_type
                self.string = string
                self.comodel_name = relation

        class _Model:
            _fields = {
                "name": _Field("char", "名称"),
                "business_purpose": _Field("char", "事由"),
                "amount": _Field("monetary", "金额"),
                "line_ids": _Field("one2many", "明细"),
            }

            def fields_get(self, names):
                return {
                    name: {
                        "type": field.type,
                        "string": field.string,
                        "relation": field.comodel_name,
                    }
                    for name, field in self._fields.items()
                    if name in names
                }

        class _Env:
            def __contains__(self, model):
                return model == "demo.business"

            def __getitem__(self, model):
                if model != "demo.business":
                    raise KeyError(model)
                return _Model()

        handler = self.module.UiContractV2Handler(env=_Env())
        source_contract = {
            "fields": {
                "name": {"name": "name", "type": "char", "string": "名称"},
                "business_purpose": {"name": "business_purpose", "type": "char", "string": "事由"},
                "amount": {"name": "amount", "type": "monetary", "string": "金额"},
                "line_ids": {"name": "line_ids", "type": "one2many", "string": "明细"},
            },
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "sheet",
                            "children": [
                                {"type": "field", "name": "name"},
                                {"type": "field", "name": "business_purpose"},
                                {"type": "field", "name": "amount"},
                                {"type": "field", "name": "line_ids"},
                            ],
                        }
                    ]
                }
            },
            "visible_fields": ["name"],
        }

        handler._inject_business_operation_contract(
            source_contract,
            model="demo.business",
            view_type="form",
        )

        self.assertNotIn("form_structure_contract", source_contract)
        self.assertNotIn("list_profile", source_contract)
        self.assertEqual(source_contract["visible_fields"], ["name"])

    def test_form_structure_governance_ignores_hidden_config_fields(self):
        class _Field:
            def __init__(self, field_type, string="", relation=""):
                self.type = field_type
                self.string = string
                self.comodel_name = relation

        class _Model:
            _fields = {
                "name": _Field("char", "名称"),
                "amount": _Field("monetary", "金额"),
                "line_ids": _Field("one2many", "明细"),
            }

            def fields_get(self, names):
                return {
                    name: {
                        "type": field.type,
                        "string": field.string,
                        "relation": field.comodel_name,
                    }
                    for name, field in self._fields.items()
                    if name in names
                }

        class _GeneratedConfig:
            id = 7
            name = "demo_form_generated"
            priority = 70
            view_type = "form"
            version_no = 1
            contract_json = {
                "view_orchestration": {
                    "views": {
                        "form": {
                            "fields": [
                                {"name": "name", "sequence": 10},
                                {"name": "amount", "sequence": 20},
                                {"name": "line_ids", "sequence": 30},
                            ]
                        }
                    }
                }
            }

        class _OverrideConfig:
            id = 8
            name = "demo_form_override"
            priority = 90
            view_type = "form"
            version_no = 1
            contract_json = {
                "view_orchestration": {
                    "views": {
                        "form": {
                            "fields": [
                                {"name": "line_ids", "sequence": 30, "visible": False},
                            ]
                        }
                    }
                }
            }

        class _ConfigModel:
            def _effective_view_orchestration_contracts(self, *args, **kwargs):
                return [_GeneratedConfig(), _OverrideConfig()]

        class _Env:
            def __contains__(self, model):
                return model in {"demo.business", "ui.business.config.contract"}

            def __getitem__(self, model):
                if model == "demo.business":
                    return _Model()
                if model == "ui.business.config.contract":
                    return _ConfigModel()
                raise KeyError(model)

        handler = self.module.UiContractV2Handler(env=_Env())
        source_contract = {
            "fields": {
                "name": {"name": "name", "type": "char", "string": "名称"},
                "amount": {"name": "amount", "type": "monetary", "string": "金额"},
                "line_ids": {"name": "line_ids", "type": "one2many", "string": "明细"},
            },
            "views": {"form": {"layout": []}},
            "governance": {"view_orchestration": {"applied": True}},
        }

        handler._inject_business_operation_contract(
            source_contract,
            model="demo.business",
            view_type="form",
        )

        structure = source_contract["form_structure_contract"]
        self.assertIn("name", structure["fieldRoles"])
        self.assertIn("amount", structure["fieldRoles"])
        self.assertNotIn("line_ids", structure["fieldRoles"])

    def test_form_structure_governance_hides_configured_groups(self):
        class _Field:
            def __init__(self, field_type, string="", relation=""):
                self.type = field_type
                self.string = string
                self.comodel_name = relation

        class _Model:
            _fields = {
                "name": _Field("char", "名称"),
                "amount": _Field("monetary", "金额"),
                "tax_note": _Field("char", "税务说明"),
            }

            def fields_get(self, names):
                return {
                    name: {
                        "type": field.type,
                        "string": field.string,
                        "relation": field.comodel_name,
                    }
                    for name, field in self._fields.items()
                    if name in names
                }

        class _Config:
            id = 9
            name = "demo_form_sections"
            priority = 80
            view_type = "form"
            contract_json = {
                "view_orchestration": {
                    "views": {
                        "form": {
                            "columns": 3,
                            "fields": [
                                {"name": "name", "sequence": 10},
                                {"name": "amount", "sequence": 20},
                                {"name": "tax_note", "sequence": 30},
                            ],
                            "sections": [
                                {
                                    "title": "基础信息",
                                    "visible": True,
                                    "columns": 2,
                                    "fields": ["name", "amount"],
                                },
                                {
                                    "title": "税务信息",
                                    "visible": False,
                                    "columns": 1,
                                    "fields": ["tax_note"],
                                },
                            ],
                        }
                    }
                }
            }

        class _ConfigModel:
            def _effective_view_orchestration_contracts(self, *args, **kwargs):
                return [_Config()]

        class _Env:
            def __contains__(self, model):
                return model in {"demo.business", "ui.business.config.contract"}

            def __getitem__(self, model):
                if model == "demo.business":
                    return _Model()
                if model == "ui.business.config.contract":
                    return _ConfigModel()
                raise KeyError(model)

        handler = self.module.UiContractV2Handler(env=_Env())
        source_contract = {
            "fields": {
                "name": {"name": "name", "type": "char", "string": "名称"},
                "amount": {"name": "amount", "type": "monetary", "string": "金额"},
                "tax_note": {"name": "tax_note", "type": "char", "string": "税务说明"},
            },
            "views": {"form": {"layout": []}},
            "governance": {"view_orchestration": {"applied": True}},
        }

        handler._inject_business_operation_contract(
            source_contract,
            model="demo.business",
            view_type="form",
        )

        governance = source_contract["business_operation_profile"]["form_structure_governance"]
        self.assertEqual(governance["form_columns"], 3)
        self.assertEqual(governance["group_columns"], {"基础信息": 2, "税务信息": 1})
        self.assertEqual(governance["group_visibility"], {"基础信息": True, "税务信息": False})
        self.assertEqual(governance["hidden_field_names"], ["tax_note"])

        structure = source_contract["form_structure_contract"]
        self.assertEqual(structure["columns"], 3)
        groups = structure["slots"][0]["groups"]
        self.assertEqual([group["title"] for group in groups], ["基础信息"])
        self.assertEqual(groups[0]["columns"], 2)
        self.assertIn("name", structure["fieldRoles"])
        self.assertIn("amount", structure["fieldRoles"])
        self.assertNotIn("tax_note", structure["fieldRoles"])

    def test_tree_projection_does_not_import_form_structure_fields_into_list_profile(self):
        class _Field:
            def __init__(self, field_type, string="", relation=""):
                self.type = field_type
                self.string = string
                self.comodel_name = relation

        class _Model:
            _fields = {
                "name": _Field("char", "名称"),
                "project_id": _Field("many2one", "项目", "project.project"),
                "visible_contract_amount": _Field("monetary", "合同金额"),
                "engineering_address": _Field("char", "工程地址"),
                "contract_payment_method_text": _Field("char", "合同约定付款方式"),
                "entry_time": _Field("datetime", "录入时间"),
                "state": _Field("selection", "状态"),
            }

            def fields_get(self, names):
                return {
                    name: {
                        "type": field.type,
                        "string": field.string,
                        "relation": field.comodel_name,
                    }
                    for name, field in self._fields.items()
                    if name in names
                }

        class _Env:
            def __contains__(self, model):
                return model == "construction.contract.income"

            def __getitem__(self, model):
                if model != "construction.contract.income":
                    raise KeyError(model)
                return _Model()

        handler = self.module.UiContractV2Handler(env=_Env())
        source_contract = {
            "fields": {
                "name": {"name": "name", "type": "char", "string": "名称"},
                "project_id": {"name": "project_id", "type": "many2one", "string": "项目"},
                "visible_contract_amount": {"name": "visible_contract_amount", "type": "monetary", "string": "合同金额"},
                "engineering_address": {"name": "engineering_address", "type": "char", "string": "工程地址"},
                "contract_payment_method_text": {
                    "name": "contract_payment_method_text",
                    "type": "char",
                    "string": "合同约定付款方式",
                },
                "entry_time": {"name": "entry_time", "type": "datetime", "string": "录入时间"},
                "state": {"name": "state", "type": "selection", "string": "状态"},
            },
            "views": {
                "tree": {
                    "columns_schema": [
                        {"name": "name", "string": "名称", "type": "char"},
                        {"name": "project_id", "string": "项目", "type": "many2one"},
                        {"name": "visible_contract_amount", "string": "合同金额", "type": "monetary"},
                    ]
                }
            },
        }

        handler._inject_business_operation_contract(
            source_contract,
            model="construction.contract.income",
            view_type="tree",
        )

        columns = source_contract["list_profile"]["columns"]
        self.assertEqual(columns, ["name", "project_id", "visible_contract_amount", "state"])
        self.assertNotIn("engineering_address", columns)
        self.assertNotIn("contract_payment_method_text", columns)
        self.assertNotIn("entry_time", columns)
        self.assertNotIn("form_structure_contract", source_contract)


if __name__ == "__main__":
    unittest.main()
