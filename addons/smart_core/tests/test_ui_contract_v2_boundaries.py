# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
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


def _load_handler():
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

    def test_business_list_profile_keeps_contract_payment_terms_visible(self):
        handler = self.module.UiContractV2Handler(env=object())
        columns = [{"name": f"field_{index}"} for index in range(18)]
        columns.extend([
            {"name": "contract_duration_text"},
            {"name": "contract_payment_method_text"},
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
        self.assertEqual(len(profile_columns), 18)
        self.assertIn("contract_duration_text", profile_columns)
        self.assertIn("contract_payment_method_text", profile_columns)
        self.assertIn("visible_contract_amount", profile_columns)
        self.assertEqual(
            source_contract["list_profile"]["preference_policy"]["must_request_columns"],
            profile_columns,
        )


if __name__ == "__main__":
    unittest.main()
