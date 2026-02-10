#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ALLOWED_OPS = {
    "nav",
    "menu",
    "action_open",
    "model",
    "ui.contract",
    "meta.describe_project_capabilities",
    "contract.capability_matrix",
    "contract.portal_dashboard",
    "contract.portal_execute_button",
    "intent.invoke",
}
ALLOWED_VIEW_TYPES = {"form", "list", "kanban"}
ALLOWED_CASE_KEYS = {
    "action_xmlid",
    "allow_error_response",
    "case",
    "execute_method",
    "id",
    "include_meta",
    "intent",
    "intent_params",
    "menu_id",
    "model",
    "op",
    "outdir",
    "project_id",
    "route",
    "trace_id",
    "user",
    "view_type",
}


def _as_str(value) -> str:
    return str(value or "").strip()


def _validate_positive_int(raw, field_name: str, case_name: str, invalid: list[str]) -> None:
    if raw is None:
        return
    if not isinstance(raw, int) or isinstance(raw, bool) or raw <= 0:
        invalid.append(f"{case_name}: {field_name} must be positive integer")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate docs/contract/cases.yml integrity for contract snapshot export."
    )
    parser.add_argument("--cases-file", default="docs/contract/cases.yml")
    args = parser.parse_args()

    path = Path(args.cases_file)
    if not path.exists():
        raise SystemExit(f"❌ missing cases file: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"❌ invalid cases JSON: {exc}")

    if not isinstance(payload, list):
        raise SystemExit("❌ cases file must be a JSON array")

    seen: set[str] = set()
    duplicated: set[str] = set()
    invalid: list[str] = []

    for idx, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            invalid.append(f"#{idx}: case item must be object")
            continue

        case_name = _as_str(item.get("case"))
        user = _as_str(item.get("user"))
        op = _as_str(item.get("op"))

        unknown_keys = sorted(set(item.keys()) - ALLOWED_CASE_KEYS)
        if unknown_keys:
            invalid.append(f"{case_name or f'#{idx}'}: unknown keys: {', '.join(unknown_keys)}")

        if not case_name:
            invalid.append(f"#{idx}: missing case")
            continue
        if case_name in seen:
            duplicated.add(case_name)
        seen.add(case_name)

        if not user:
            invalid.append(f"{case_name}: missing user")
        if not op:
            invalid.append(f"{case_name}: missing op")
            continue

        if op not in ALLOWED_OPS:
            invalid.append(
                f"{case_name}: unsupported op={op} (allowed: {', '.join(sorted(ALLOWED_OPS))})"
            )

        view_type = _as_str(item.get("view_type"))
        if view_type and view_type not in ALLOWED_VIEW_TYPES:
            invalid.append(
                f"{case_name}: unsupported view_type={view_type} (allowed: form,list,kanban)"
            )

        if "include_meta" in item and not isinstance(item.get("include_meta"), bool):
            invalid.append(f"{case_name}: include_meta must be boolean")
        if "allow_error_response" in item and not isinstance(item.get("allow_error_response"), bool):
            invalid.append(f"{case_name}: allow_error_response must be boolean")

        _validate_positive_int(item.get("id"), "id", case_name, invalid)
        _validate_positive_int(item.get("menu_id"), "menu_id", case_name, invalid)
        _validate_positive_int(item.get("project_id"), "project_id", case_name, invalid)

        if op == "model" and not _as_str(item.get("model")):
            invalid.append(f"{case_name}: missing model for op=model")
        if op == "menu" and item.get("menu_id") is None:
            invalid.append(f"{case_name}: missing menu_id for op=menu")
        if op == "action_open" and not _as_str(item.get("action_xmlid")):
            invalid.append(f"{case_name}: missing action_xmlid for op=action_open")
        if op == "ui.contract" and not _as_str(item.get("route")):
            invalid.append(f"{case_name}: missing route for op=ui.contract")
        if op == "meta.describe_project_capabilities" and item.get("project_id") is None:
            invalid.append(
                f"{case_name}: missing project_id for op=meta.describe_project_capabilities"
            )

        if op == "intent.invoke":
            intent = _as_str(item.get("intent"))
            if not intent:
                invalid.append(f"{case_name}: missing intent for op=intent.invoke")
            if "intent_params" in item and not isinstance(item.get("intent_params"), dict):
                invalid.append(f"{case_name}: intent_params must be object")

    if duplicated:
        invalid.append("duplicate case names: " + ", ".join(sorted(duplicated)))

    if invalid:
        raise SystemExit("❌ invalid cases integrity:\n- " + "\n- ".join(invalid))

    print("[verify.intent_cases.integrity_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
