#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def require(path: str, token: str, errors: list[str]) -> None:
    target = ROOT / path
    if not target.exists():
        errors.append(f"missing {path}")
        return
    if token and token not in target.read_text(encoding="utf-8"):
        errors.append(f"{path} missing {token}")


def main() -> int:
    errors: list[str] = []
    require("schemas/tenant_delivery/customer_module_manifest.schema.json", "sce.customer_module_manifest.v1", errors)
    require("schemas/tenant_delivery/customer_payload_manifest.schema.json", "sce.customer_payload_manifest.v1", errors)
    require("addons/smart_core/utils/tenant_delivery_manifest.py", "verify_manifest_hmac", errors)
    require("addons/smart_core/models/tenant_payload_import_batch.py", "rolled_back", errors)
    require("customer_addons/sce_customer_sample/customer_module_manifest.json", "fail_closed", errors)
    require("customer_addons/sce_customer_sample/hooks.py", "allow_audited_tenant_destroy", errors)

    for schema_path in (
        "schemas/tenant_delivery/customer_module_manifest.schema.json",
        "schemas/tenant_delivery/customer_payload_manifest.schema.json",
        "customer_addons/sce_customer_sample/customer_module_manifest.json",
    ):
        try:
            json.loads((ROOT / schema_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON {schema_path}: {exc}")
    try:
        sample_manifest = ast.literal_eval(
            (ROOT / "customer_addons/sce_customer_sample/__manifest__.py").read_text(encoding="utf-8")
        )
        if sample_manifest.get("depends") != ["smart_construction_bundle"]:
            errors.append("sample customer module must depend only on smart_construction_bundle")
        if sample_manifest.get("uninstall_hook") != "uninstall_hook":
            errors.append("sample customer module must register uninstall_hook")
    except (OSError, SyntaxError, ValueError) as exc:
        errors.append(f"invalid sample customer manifest: {exc}")
    if errors:
        print("[tenant_delivery_protocol_guard] FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("[tenant_delivery_protocol_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
