#!/usr/bin/env python3
"""Guard Lite semantic parity across supported terminal clients."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SUPPORTED_CLIENTS = ("web_pc", "wx_mini", "harmony_h5")
CONTRACT_VERSION = "2.0.0"
ALLOWED_PATCH_OPERATIONS = {"replace", "merge"}
FORBIDDEN_ID_SUFFIXES = (
    ".web_pc",
    ".wx_mini",
    ".harmony_h5",
    ".mobile",
    ".mini",
    ".h5",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def repo_label(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def iter_containers(containers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for container in containers:
        found.append(container)
        found.extend(iter_containers(container.get("children") or []))
    return found


def collect_widgets(contract: dict[str, Any]) -> list[dict[str, Any]]:
    widgets: list[dict[str, Any]] = []
    for container in iter_containers(contract["layoutContract"].get("containerList") or []):
        widgets.extend(container.get("widgetList") or [])
    return widgets


def semantic_signature(contract: dict[str, Any]) -> dict[str, Any]:
    page = contract["pageInfo"]
    containers = iter_containers(contract["layoutContract"].get("containerList") or [])
    widgets = collect_widgets(contract)
    widget_status = contract["statusContract"].get("widgetStatus") or []
    button_status = contract["statusContract"].get("buttonStatus") or []
    actions = contract["actionContract"].get("actionRuleList") or []
    data = contract["dataContract"]
    return {
        "page": {
            "pageId": page["pageId"],
            "sceneKey": page["sceneKey"],
            "model": page["model"],
            "viewType": page["viewType"],
            "contractVersion": page["contractVersion"],
        },
        "layout": {
            "layoutType": contract["layoutContract"]["layoutType"],
            "containers": sorted(
                (
                    container["containerId"],
                    container["containerType"],
                    tuple(widget["widgetId"] for widget in container.get("widgetList") or []),
                )
                for container in containers
            ),
            "widgets": sorted(
                (
                    widget["widgetId"],
                    widget["fieldCode"],
                    widget["widgetType"],
                    widget["component"],
                )
                for widget in widgets
            ),
        },
        "status": {
            "widgets": sorted(
                (
                    item["widgetId"],
                    item["visible"],
                    item["readonly"],
                    item["required"],
                    item["disabled"],
                )
                for item in widget_status
            ),
            "buttons": sorted(
                (
                    item["btnId"],
                    item["visible"],
                    item["disabled"],
                )
                for item in button_status
            ),
        },
        "actions": sorted(
            (
                item["actionId"],
                item["triggerType"],
                item["sourceWidgetId"],
                item["dispatchMode"],
                item["refreshMode"],
            )
            for item in actions
        ),
        "dataKeys": {
            "mainData": sorted(data.get("mainData", {}).keys()),
            "relationData": sorted(data.get("relationData", {}).keys()),
            "dictData": sorted(data.get("dictData", {}).keys()),
        },
    }


def terminal_variant(contract: dict[str, Any], client_type: str) -> dict[str, Any]:
    variant = copy.deepcopy(contract)
    variant["pageInfo"]["clientType"] = client_type
    return variant


def id_values(contract: dict[str, Any]) -> list[str]:
    page = contract["pageInfo"]
    values = [page["pageId"], page["sceneKey"]]
    for container in iter_containers(contract["layoutContract"].get("containerList") or []):
        values.append(container["containerId"])
    for widget in collect_widgets(contract):
        values.extend([widget["widgetId"], widget["fieldCode"]])
    for item in contract["statusContract"].get("widgetStatus") or []:
        values.append(item["widgetId"])
    for item in contract["statusContract"].get("buttonStatus") or []:
        values.append(item["btnId"])
    for item in contract["actionContract"].get("actionRuleList") or []:
        values.extend([item["actionId"], item["sourceWidgetId"]])
    return values


def validate_contract(label: str, contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    page = contract.get("pageInfo") or {}
    if page.get("contractVersion") != CONTRACT_VERSION:
        errors.append(f"{label}: contractVersion must be {CONTRACT_VERSION}")
    if page.get("clientType") not in SUPPORTED_CLIENTS:
        errors.append(f"{label}: unsupported clientType {page.get('clientType')!r}")
    if set(contract.keys()) != {
        "pageInfo",
        "layoutContract",
        "statusContract",
        "actionContract",
        "dataContract",
        "meta",
    }:
        errors.append(f"{label}: unexpected top-level keys {sorted(contract.keys())}")
    for value in id_values(contract):
        if any(value.endswith(suffix) for suffix in FORBIDDEN_ID_SUFFIXES):
            errors.append(f"{label}: terminal-specific id is forbidden: {value}")
    for action in contract["actionContract"].get("actionRuleList") or []:
        if action.get("dispatchMode") != "server":
            errors.append(f"{label}: action {action.get('actionId')} is not server-dispatched")
    return errors


def validate_patch(label: str, patch: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    operation = patch.get("operation")
    if operation not in ALLOWED_PATCH_OPERATIONS:
        errors.append(f"{label}: patch operation must be replace or merge, got {operation!r}")
    if patch.get("updateType") != "partial":
        errors.append(f"{label}: updateType must be partial")
    for key in ("statusPatch", "dataPatch", "layoutPatch"):
        if key not in patch:
            errors.append(f"{label}: missing {key}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", action="append", required=True, type=Path)
    parser.add_argument("--patch", action="append", default=[], type=Path)
    parser.add_argument("--plan-doc", required=True, type=Path)
    parser.add_argument("--makefile", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    contract_reports: list[dict[str, Any]] = []
    for contract_path in args.contract:
        contract = read_json(contract_path)
        label = repo_label(contract_path)
        errors.extend(validate_contract(label, contract))
        signatures: dict[str, str] = {}
        for client_type in SUPPORTED_CLIENTS:
            variant = terminal_variant(contract, client_type)
            variant_errors = validate_contract(f"{label}:{client_type}", variant)
            errors.extend(variant_errors)
            signatures[client_type] = stable_hash(semantic_signature(variant))
        unique_signatures = sorted(set(signatures.values()))
        if len(unique_signatures) != 1:
            errors.append(f"{label}: semantic signature diverges across terminals")
        contract_reports.append(
            {
                "contract": label,
                "clients": list(SUPPORTED_CLIENTS),
                "semanticSignature": unique_signatures[0] if unique_signatures else None,
                "signatureByClient": signatures,
            }
        )

    patch_reports: list[dict[str, Any]] = []
    for patch_path in args.patch:
        patch = read_json(patch_path)
        label = repo_label(patch_path)
        errors.extend(validate_patch(label, patch))
        patch_reports.append(
            {
                "patch": label,
                "operation": patch.get("operation"),
                "updateType": patch.get("updateType"),
            }
        )

    plan_text = args.plan_doc.read_text(encoding="utf-8") if args.plan_doc.exists() else ""
    makefile_text = args.makefile.read_text(encoding="utf-8") if args.makefile.exists() else ""
    required_plan_tokens = (
        "All-Terminal Coverage Plan",
        "`web_pc`, `wx_mini`, and `harmony_h5`",
        "terminal_client_parity",
        "terminal_coverage_matrix",
        "same Lite semantic contract",
        "no page-level semantic inference",
    )
    for token in required_plan_tokens:
        if token not in plan_text:
            errors.append(f"plan doc missing token: {token}")
    required_makefile_tokens = (
        "verify.unified_page_contract.lite.terminal_client_parity",
        "unified_page_contract_lite_terminal_client_parity_guard.py",
    )
    for token in required_makefile_tokens:
        if token not in makefile_text:
            errors.append(f"Makefile missing token: {token}")

    report = {
        "ok": not errors,
        "clients": list(SUPPORTED_CLIENTS),
        "contractVersion": CONTRACT_VERSION,
        "contractReports": contract_reports,
        "patchReports": patch_reports,
        "allowedPatchOperations": sorted(ALLOWED_PATCH_OPERATIONS),
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite terminal client parity guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite terminal client parity guard passed")
    print(f"- clients: {', '.join(SUPPORTED_CLIENTS)}")
    print(f"- contracts: {len(contract_reports)}")
    print(f"- patches: {len(patch_reports)}")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
