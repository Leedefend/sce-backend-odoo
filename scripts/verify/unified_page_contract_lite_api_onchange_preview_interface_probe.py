# -*- coding: utf-8 -*-
"""Probe api.onchange Lite preview through the Odoo handler boundary.

Run through Odoo shell:
    DB_NAME=sc_demo make verify.unified_page_contract.lite.api_onchange_interface
"""

import json
import os
from pathlib import Path

from odoo import api, SUPERUSER_ID  # noqa: F401

from odoo.addons.smart_core.handlers.api_onchange import ApiOnchangeHandler


def _artifact_root():
    candidates = [
        Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or ""),
        Path("/tmp/unified_page_contract_lite"),
    ]
    for path in candidates:
        if not str(path):
            continue
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return path
        except Exception:
            continue
    raise RuntimeError("no writable artifact root")


def _run_handler(params):
    handler = ApiOnchangeHandler(env, payload={"params": params})  # noqa: F821
    return handler.handle({"params": params})


def _base_params():
    return {
        "model": "project.project",
        "values": {"name": "Lite Interface Probe"},
        "changed_fields": [],
        "context": {"lang": "zh_CN"},
    }


def _valid_opt_in():
    params = _base_params()
    params.update(
        {
            "contractMode": "lite_preview",
            "contractVersion": "2.0.0",
            "entryPoint": "api_onchange",
            "clientType": "web_pc",
            "fallbackMode": "legacy_default",
            "traceId": "lite-interface-probe-001",
        }
    )
    return params


def _incomplete_opt_in():
    params = _base_params()
    params.update(
        {
            "contractMode": "lite_preview",
            "entryPoint": "api_onchange",
            "clientType": "web_pc",
            "fallbackMode": "legacy_default",
        }
    )
    return params


def _assert(condition, errors, message):
    if not condition:
        errors.append(message)


errors = []
default_response = _run_handler(_base_params())
incomplete_response = _run_handler(_incomplete_opt_in())
valid_response = _run_handler(_valid_opt_in())

_assert(default_response.get("ok") is True, errors, "default response must be ok")
_assert("lite_preview" not in default_response, errors, "default response must not include lite_preview")
_assert(incomplete_response.get("ok") is True, errors, "incomplete opt-in response must be ok")
_assert("lite_preview" not in incomplete_response, errors, "incomplete opt-in must not include lite_preview")
_assert(valid_response.get("ok") is True, errors, "valid opt-in response must be ok")
_assert(valid_response.get("data") == default_response.get("data"), errors, "valid opt-in must keep legacy data unchanged")

preview = valid_response.get("lite_preview") if isinstance(valid_response, dict) else None
_assert(isinstance(preview, dict), errors, "valid opt-in must include lite_preview envelope")
if isinstance(preview, dict):
    _assert(preview.get("contractMode") == "lite_preview", errors, "preview contractMode mismatch")
    _assert(preview.get("contractVersion") == "2.0.0", errors, "preview contractVersion mismatch")
    _assert(preview.get("entryPoint") == "api_onchange", errors, "preview entryPoint mismatch")
    _assert(preview.get("payloadType") == "lite_patch", errors, "preview payloadType mismatch")
    _assert(preview.get("fallbackMode") == "legacy_default", errors, "preview fallbackMode mismatch")
    meta = preview.get("meta") if isinstance(preview.get("meta"), dict) else {}
    _assert(meta.get("previewOnly") is True, errors, "preview meta.previewOnly must be true")
    _assert(meta.get("defaultUnchanged") is True, errors, "preview meta.defaultUnchanged must be true")
    _assert(meta.get("traceId") == "lite-interface-probe-001", errors, "preview traceId must be preserved")
    payload = preview.get("payload") if isinstance(preview.get("payload"), dict) else {}
    _assert(payload.get("updateType") == "partial", errors, "preview payload must be partial")
    for key in ("statusPatch", "dataPatch", "layoutPatch"):
        _assert(isinstance(payload.get(key), dict), errors, "preview payload missing %s" % key)

report = {
    "ok": not errors,
    "db": env.cr.dbname,  # noqa: F821
    "model": "project.project",
    "default_ok": default_response.get("ok") is True,
    "default_has_lite_preview": "lite_preview" in default_response,
    "incomplete_has_lite_preview": "lite_preview" in incomplete_response,
    "valid_has_lite_preview": isinstance(preview, dict),
    "valid_legacy_data_unchanged": valid_response.get("data") == default_response.get("data"),
    "preview_payload_type": preview.get("payloadType") if isinstance(preview, dict) else None,
    "errors": errors,
}

out = _artifact_root() / "unified_page_contract_lite_api_onchange_preview_interface.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
print("UNIFIED_PAGE_CONTRACT_LITE_API_ONCHANGE_INTERFACE_REPORT=%s" % out)
if errors:
    raise SystemExit(1)
print("UNIFIED_PAGE_CONTRACT_LITE_API_ONCHANGE_INTERFACE=PASS")
