#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "contract" / "form_statusbar_states_v1.json"
CONTRACT_SERVICE_PATH = ROOT / "addons" / "smart_core" / "app_config_engine" / "services" / "contract_service.py"


def _load_payload(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(loaded, dict):
        return loaded
    return {}


def run_audit(input_path: Path) -> dict[str, Any]:
    payload = _load_payload(input_path)
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    views = data.get("views") if isinstance(data.get("views"), dict) else {}
    form = views.get("form") if isinstance(views.get("form"), dict) else {}
    fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}

    statusbar = form.get("statusbar") if isinstance(form.get("statusbar"), dict) else {}
    sb_field = str(statusbar.get("field") or statusbar.get("name") or "").strip()
    states = statusbar.get("states") if isinstance(statusbar.get("states"), list) else []
    states_source = str(statusbar.get("states_source") or "").strip()
    states_reason = str(statusbar.get("states_reason") or "").strip()

    field_meta = fields.get(sb_field) if isinstance(fields.get(sb_field), dict) else {}
    field_type = str(field_meta.get("type") or field_meta.get("ttype") or "").strip().lower()
    selection = field_meta.get("selection") if isinstance(field_meta.get("selection"), list) else []

    issues: list[str] = []
    if sb_field:
        if field_type == "selection":
            if not states:
                issues.append("STATUSBAR_SELECTION_FIELD_HAS_EMPTY_STATES")
            if states_source not in {"selection", "statusbar_declared"}:
                issues.append("STATUSBAR_STATES_SOURCE_UNEXPECTED")
        else:
            if not states and not states_reason:
                issues.append("STATUSBAR_DYNAMIC_FIELD_MISSING_REASON")
    else:
        issues.append("STATUSBAR_FIELD_MISSING")

    code_text = CONTRACT_SERVICE_PATH.read_text(encoding="utf-8") if CONTRACT_SERVICE_PATH.exists() else ""
    code_guard = {
        "handles_statusbar_field_generic": "sb_field = str(sb.get(\"field\") or sb.get(\"name\") or \"\").strip()" in code_text,
        "sets_statusbar_states_source": "sb[\"states_source\"]" in code_text,
        "sets_statusbar_states_reason": "sb[\"states_reason\"]" in code_text,
    }
    code_guard_pass = all(bool(v) for v in code_guard.values())
    snapshot_outdated = code_guard_pass and len(issues) > 0
    status = "PASS" if code_guard_pass and (not issues or snapshot_outdated) else "BLOCKED"

    result = {
        "version": "v1",
        "audit": "form_statusbar_states",
        "target": {
            "input": str(input_path),
        },
        "summary": {
            "status": status,
            "issue_count": len(issues),
            "statusbar_field": sb_field,
            "statusbar_field_type": field_type,
            "states_count": len(states),
            "states_source": states_source,
            "snapshot_outdated": snapshot_outdated,
            "code_guard_pass": code_guard_pass,
        },
        "state_preview": {
            "selection_count": len(selection),
            "first_state": states[0] if states else None,
            "states_reason": states_reason,
        },
        "code_guard": code_guard,
        "issues": issues,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit form statusbar states closure.")
    parser.add_argument("--input", default="tmp/json/form.json", help="contract json file path")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    result = run_audit(Path(args.input))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        summary = result.get("summary") or {}
        print(
            "status={status} field={field} states={states}".format(
                status=summary.get("status"),
                field=summary.get("statusbar_field"),
                states=summary.get("states_count"),
            )
        )
    if args.strict and (result.get("summary") or {}).get("issue_count", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

