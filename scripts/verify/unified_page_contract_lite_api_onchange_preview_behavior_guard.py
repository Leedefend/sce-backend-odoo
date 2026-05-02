#!/usr/bin/env python3
"""Verify api.onchange Lite preview opt-in behavior without importing Odoo."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from addons.smart_core.core.unified_page_contract_lite_preview import with_lite_preview_if_requested  # noqa: E402


VALID_OPT_IN = {
    "contractMode": "lite_preview",
    "contractVersion": "2.0.0",
    "entryPoint": "api_onchange",
    "clientType": "web_pc",
    "fallbackMode": "legacy_default",
    "traceId": "trace-lite-preview-001",
}
DEFAULT_PARAMS = {
    "model": "project.project",
    "values": {"budget_total": 3000},
    "changed_fields": ["budget_total"],
}
MISSING_VERSION_OPT_IN = {
    "contractMode": "lite_preview",
    "entryPoint": "api_onchange",
    "clientType": "web_pc",
    "fallbackMode": "legacy_default",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_true(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-response", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    legacy_response = load_json(args.legacy_response)

    default_response = copy.deepcopy(legacy_response)
    default_out = with_lite_preview_if_requested(default_response, DEFAULT_PARAMS, "api_onchange")
    assert_true(errors, default_out is default_response, "default api.onchange must return the original response object")
    assert_true(errors, default_out == legacy_response, "default api.onchange response content must remain unchanged")
    assert_true(errors, "lite_preview" not in default_out, "default api.onchange must not include lite_preview")

    incomplete_response = copy.deepcopy(legacy_response)
    incomplete_out = with_lite_preview_if_requested(incomplete_response, MISSING_VERSION_OPT_IN, "api_onchange")
    assert_true(errors, incomplete_out is incomplete_response, "incomplete opt-in must return the original response object")
    assert_true(errors, "lite_preview" not in incomplete_out, "incomplete opt-in must not include lite_preview")

    opt_in_response = copy.deepcopy(legacy_response)
    opt_in_out = with_lite_preview_if_requested(opt_in_response, VALID_OPT_IN, "api_onchange")
    assert_true(errors, opt_in_out is not opt_in_response, "valid opt-in must return a shallow copied response")
    assert_true(errors, opt_in_out.get("data") == legacy_response.get("data"), "valid opt-in must keep legacy data unchanged")
    assert_true(errors, opt_in_response == legacy_response, "valid opt-in must not mutate the original response")

    preview = opt_in_out.get("lite_preview") if isinstance(opt_in_out, dict) else None
    assert_true(errors, isinstance(preview, dict), "valid opt-in must include lite_preview envelope")
    if isinstance(preview, dict):
        assert_true(errors, preview.get("contractMode") == "lite_preview", "preview contractMode must be lite_preview")
        assert_true(errors, preview.get("contractVersion") == "2.0.0", "preview contractVersion must be 2.0.0")
        assert_true(errors, preview.get("entryPoint") == "api_onchange", "preview entryPoint must be api_onchange")
        assert_true(errors, preview.get("payloadType") == "lite_patch", "preview payloadType must be lite_patch")
        assert_true(errors, preview.get("fallbackMode") == "legacy_default", "preview fallbackMode must be legacy_default")
        meta = preview.get("meta") if isinstance(preview.get("meta"), dict) else {}
        assert_true(errors, meta.get("previewOnly") is True, "preview meta.previewOnly must be true")
        assert_true(errors, meta.get("defaultUnchanged") is True, "preview meta.defaultUnchanged must be true")
        assert_true(errors, meta.get("traceId") == VALID_OPT_IN["traceId"], "preview traceId must be preserved")
        payload = preview.get("payload") if isinstance(preview.get("payload"), dict) else {}
        assert_true(errors, payload.get("updateType") == "partial", "Lite preview payload must be a partial patch")
        for key in ("statusPatch", "dataPatch", "layoutPatch"):
            assert_true(errors, isinstance(payload.get(key), dict), f"Lite preview payload missing {key}")
        status_patch = payload.get("statusPatch") if isinstance(payload.get("statusPatch"), dict) else {}
        data_patch = payload.get("dataPatch") if isinstance(payload.get("dataPatch"), dict) else {}
        assert_true(errors, "widgetStatus" in status_patch, "Lite preview statusPatch must include widgetStatus")
        assert_true(errors, "buttonStatus" in status_patch, "Lite preview statusPatch must include buttonStatus")
        assert_true(errors, "relationData" in data_patch, "Lite preview dataPatch must include relationData")

    report = {
        "ok": not errors,
        "default_unchanged": default_out == legacy_response and "lite_preview" not in default_out,
        "incomplete_opt_in_unchanged": "lite_preview" not in incomplete_out,
        "valid_opt_in_has_preview": isinstance(preview, dict),
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite api.onchange preview behavior guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite api.onchange preview behavior guard passed")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
