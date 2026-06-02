# -*- coding: utf-8 -*-
import importlib.util
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, params=None, context=None):
        self.env = env or {}
        self.params = params or {}
        self.context = context or {}


class _Env(dict):
    def __init__(self):
        super().__init__()
        self.attachment_lookup_count = 0

    def __getitem__(self, key):
        if key == "ir.attachment":
            self.attachment_lookup_count += 1
        return super().__getitem__(key)


def _load_handler():
    root = Path(__file__).resolve().parents[1]
    odoo_mod = types.ModuleType("odoo")
    exc_mod = types.ModuleType("odoo.exceptions")
    exc_mod.AccessError = type("AccessError", (Exception,), {})
    odoo_mod.exceptions = exc_mod

    addons_mod = types.ModuleType("odoo.addons")
    smart_core_mod = types.ModuleType("odoo.addons.smart_core")
    handlers_mod = types.ModuleType("odoo.addons.smart_core.handlers")
    core_mod = types.ModuleType("odoo.addons.smart_core.core")
    utils_mod = types.ModuleType("odoo.addons.smart_core.utils")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]
    utils_mod.__path__ = [str(root / "utils")]

    base_mod = types.ModuleType("odoo.addons.smart_core.core.base_handler")
    base_mod.BaseIntentHandler = _BaseIntentHandler
    project_mod = types.ModuleType("odoo.addons.smart_core.core.project_context")
    project_mod.project_scope_denied_response = lambda meta: {"ok": False, "meta": meta}
    project_mod.record_in_project_scope = lambda model, record_id, project_id: (True, {"applied": False})
    project_mod.selected_project_id_from_context = lambda params, context: None
    hooks_mod = types.ModuleType("odoo.addons.smart_core.utils.extension_hooks")
    hooks_mod.call_extension_hook_first = lambda *args, **kwargs: None

    sys.modules.update(
        {
            "odoo": odoo_mod,
            "odoo.exceptions": exc_mod,
            "odoo.addons": addons_mod,
            "odoo.addons.smart_core": smart_core_mod,
            "odoo.addons.smart_core.handlers": handlers_mod,
            "odoo.addons.smart_core.core": core_mod,
            "odoo.addons.smart_core.utils": utils_mod,
            "odoo.addons.smart_core.core.base_handler": base_mod,
            "odoo.addons.smart_core.core.project_context": project_mod,
            "odoo.addons.smart_core.utils.extension_hooks": hooks_mod,
        }
    )

    module_name = "odoo.addons.smart_core.handlers.file_download"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "file_download.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestFileDownloadLocatorPolicy(unittest.TestCase):
    def test_extension_allowed_models_are_union_with_base_policy(self):
        module = _load_handler()
        old_hook = module.call_extension_hook_first
        module.call_extension_hook_first = lambda *args, **kwargs: ["payment.request"]
        try:
            handler = module.FileDownloadHandler(env=_Env())

            self.assertIn("res.partner", handler._allowed_models())
            self.assertIn("payment.request", handler._allowed_models())
        finally:
            module.call_extension_hook_first = old_hook

    def test_fallback_locator_rejects_disallowed_model_before_attachment_lookup(self):
        module = _load_handler()
        env = _Env()
        handler = module.FileDownloadHandler(
            env=env,
            params={"model": "project.task", "res_id": 7, "name": "secret.pdf"},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 403)
        self.assertEqual(env.attachment_lookup_count, 0)

    def test_non_positive_attachment_id_returns_bad_request(self):
        module = _load_handler()
        handler = module.FileDownloadHandler(env=_Env(), params={"id": 0})

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "id 无效")

    def test_fallback_locator_rejects_non_positive_res_id(self):
        module = _load_handler()
        env = _Env()
        env["res.partner"] = object()
        handler = module.FileDownloadHandler(env=env, params={"model": "res.partner", "res_id": 0})

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "res_id 无效")

    def test_resolves_legacy_uploadfile_path_from_configured_root(self):
        module = _load_handler()
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "UploadFile" / "OldSystem" / "File_New" / "a.pdf"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"x")
            old_value = os.environ.get("SC_LEGACY_FILE_ROOTS")
            os.environ["SC_LEGACY_FILE_ROOTS"] = tmpdir
            try:
                self.assertEqual(
                    module._resolve_legacy_file_path("UploadFile/OldSystem/File_New/a.pdf"),
                    target.resolve(),
                )
            finally:
                if old_value is None:
                    os.environ.pop("SC_LEGACY_FILE_ROOTS", None)
                else:
                    os.environ["SC_LEGACY_FILE_ROOTS"] = old_value

    def test_splits_legacy_file_id_links_from_display_text(self):
        module = _load_handler()

        refs = module._split_legacy_refs("历史附件 | legacy-file-id://abc123 other; legacy-file://ignored/path")

        self.assertIn("abc123", refs)
        self.assertIn("other", refs)
        self.assertNotIn("legacy-file://ignored/path", refs)

    def test_extracts_inline_legacy_attachment_ref_from_raw_payload(self):
        module = _load_handler()

        refs = module._legacy_inline_attachment_refs(
            '{"f_FDWB":"228e3e4f51e8713919fecb4f08b4a485","f_FDWB_FJ":"附件(1)","other_FJ":"not-an-attachment"}'
        )

        self.assertEqual(refs, ["228e3e4f51e8713919fecb4f08b4a485"])

    def test_uses_legacy_carrier_fields_as_attachment_refs(self):
        module = _load_handler()

        class _Record:
            _fields = {
                "legacy_pid": object(),
                "legacy_contract_id": object(),
                "contract_no": object(),
                "document_no": object(),
                "raw_payload": object(),
            }
            legacy_pid = "17799398042030000"
            legacy_contract_id = "7508903432694e2897fe74484e2236e6"
            contract_no = "GYSHT-20210926-003"
            document_no = "202109170844-1"
            raw_payload = ""

        handler = module.FileDownloadHandler(env=_Env())

        refs = handler._legacy_attachment_refs(_Record())

        self.assertIn("17799398042030000", refs)
        self.assertIn("7508903432694e2897fe74484e2236e6", refs)
        self.assertIn("GYSHT-20210926-003", refs)
        self.assertIn("202109170844-1", refs)

    def test_resolves_legacy_userfile_path_when_url_keeps_uploadfile_prefix(self):
        module = _load_handler()
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "UserFile" / "2023" / "a.png"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"x")
            old_value = os.environ.get("SC_LEGACY_FILE_ROOTS")
            os.environ["SC_LEGACY_FILE_ROOTS"] = tmpdir
            try:
                self.assertEqual(
                    module._resolve_legacy_file_path("UploadFile/UserFile/2023/a.png"),
                    target.resolve(),
                )
            finally:
                if old_value is None:
                    os.environ.pop("SC_LEGACY_FILE_ROOTS", None)
                else:
                    os.environ["SC_LEGACY_FILE_ROOTS"] = old_value

    def test_resolves_legacy_home_file_new_path_to_oldsystem_uploadfile(self):
        module = _load_handler()
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "UploadFile" / "OldSystem" / "File_New" / "PaymentApply" / "a.png"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"x")
            old_value = os.environ.get("SC_LEGACY_FILE_ROOTS")
            os.environ["SC_LEGACY_FILE_ROOTS"] = tmpdir
            try:
                self.assertEqual(
                    module._resolve_legacy_file_path("~/File_New/PaymentApply/a.png"),
                    target.resolve(),
                )
            finally:
                if old_value is None:
                    os.environ.pop("SC_LEGACY_FILE_ROOTS", None)
                else:
                    os.environ["SC_LEGACY_FILE_ROOTS"] = old_value

    def test_rejects_legacy_path_traversal(self):
        module = _load_handler()

        self.assertIsNone(module._resolve_legacy_file_path("../secret.pdf"))

    def test_reads_remote_legacy_file_when_configured(self):
        module = _load_handler()

        class _Response:
            headers = None

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b"remote"

        seen = {}
        old_base = os.environ.get("SC_LEGACY_FILE_HTTP_BASE")
        old_urlopen = module.urlopen
        os.environ["SC_LEGACY_FILE_HTTP_BASE"] = "https://files.example/legacy/"
        module.urlopen = lambda request, timeout=0: seen.setdefault("url", request.full_url) and _Response()
        try:
            result = module._read_remote_legacy_file_path("UploadFile/UserFile/2026/a b.pdf")
        finally:
            module.urlopen = old_urlopen
            if old_base is None:
                os.environ.pop("SC_LEGACY_FILE_HTTP_BASE", None)
            else:
                os.environ["SC_LEGACY_FILE_HTTP_BASE"] = old_base

        self.assertEqual(seen["url"], "https://files.example/legacy/UserFile/2026/a%20b.pdf")
        self.assertEqual(result["datas"], "cmVtb3Rl")


if __name__ == "__main__":
    unittest.main()
