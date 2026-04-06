#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "addons/smart_core/core/platform_policy_defaults.py"
INDUSTRY_EXTENSION = ROOT / "addons/smart_construction_core/core_extension.py"


def main() -> int:
    text = POLICY.read_text(encoding="utf-8", errors="ignore") if POLICY.is_file() else ""
    required = [
        "SERVER_ACTION_WINDOW_MAP",
        "FILE_UPLOAD_ALLOWED_MODELS",
        "FILE_DOWNLOAD_ALLOWED_MODELS",
        "API_DATA_WRITE_ALLOWLIST",
        "API_DATA_UNLINK_ALLOWED_MODELS",
        "MODEL_CODE_MAPPING",
        "CREATE_FIELD_FALLBACKS",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        print("[verify.architecture.platform_policy_constant_owner_guard] FAIL")
        for item in missing:
            print(f"missing constant in platform policy defaults: {item}")
        return 1
    legacy_tokens = [
        "smart_core_server_action_window_map",
        "smart_core_file_upload_allowed_models",
        "smart_core_file_download_allowed_models",
        "smart_core_api_data_write_allowlist",
        "smart_core_api_data_unlink_allowed_models",
        "smart_core_model_code_mapping",
        "smart_core_create_field_fallbacks",
    ]
    hits = [item for item in legacy_tokens if item in text]
    if hits:
        print("[verify.architecture.platform_policy_constant_owner_guard] FAIL")
        for item in hits:
            print(f"legacy policy fallback remains: {item}")
        return 1

    industry_text = INDUSTRY_EXTENSION.read_text(encoding="utf-8", errors="ignore") if INDUSTRY_EXTENSION.is_file() else ""
    forbidden_industry_constants = [
        "SERVER_ACTION_WINDOW_MAP",
        "FILE_UPLOAD_ALLOWED_MODELS",
        "FILE_DOWNLOAD_ALLOWED_MODELS",
        "API_DATA_WRITE_ALLOWLIST",
        "API_DATA_UNLINK_ALLOWED_MODELS",
        "MODEL_CODE_MAPPING",
    ]
    industry_hits = [item for item in forbidden_industry_constants if f"{item} =" in industry_text]
    if industry_hits:
        print("[verify.architecture.platform_policy_constant_owner_guard] FAIL")
        for item in industry_hits:
            print(f"industry still owns platform policy constant: {item}")
        return 1

    print("[verify.architecture.platform_policy_constant_owner_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
