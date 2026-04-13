#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "contract" / "form_stat_buttons_v1.json"


def _load_payload(input_path: str) -> dict[str, Any]:
    raw = json.loads(Path(input_path).read_text(encoding="utf-8"))
    if isinstance(raw.get("data"), dict):
        return raw.get("data")
    result = raw.get("result") if isinstance(raw.get("result"), dict) else {}
    if isinstance(result.get("data"), dict):
        return result.get("data")
    return raw if isinstance(raw, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _identity(action: dict[str, Any]) -> str:
    payload = action.get("payload") if isinstance(action.get("payload"), dict) else {}
    for key in ("name", "xml_id", "id"):
        value = action.get(key)
        if value not in (None, ""):
            return f"{key}:{value}"
    for key in ("method", "action_id", "xml_id"):
        value = payload.get(key)
        if value not in (None, ""):
            return f"payload.{key}:{value}"
    return f"label:{str(action.get('label') or '').strip()}"


def run_audit(input_path: str) -> dict[str, Any]:
    data = _load_payload(input_path)
    form = ((data.get("views") or {}).get("form") or {}) if isinstance(data, dict) else {}
    button_box = [row for row in _as_list(form.get("button_box")) if isinstance(row, dict)]
    stat_buttons = [row for row in _as_list(form.get("stat_buttons")) if isinstance(row, dict)]

    issues: list[str] = []
    overlap = sorted({_identity(row) for row in button_box} & {_identity(row) for row in stat_buttons})
    if overlap:
        issues.append("STAT_BUTTON_OVERLAP_WITH_BUTTON_BOX")
    if not stat_buttons:
        issues.append("STAT_BUTTONS_EMPTY")

    missing_semantics: list[str] = []
    for row in stat_buttons:
        label = str(row.get("label") or "").strip()
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        widget = str(row.get("widget") or "").strip()
        if not label or not payload or not widget:
            missing_semantics.append(_identity(row))
    if missing_semantics:
        issues.append("STAT_BUTTON_SEMANTICS_INCOMPLETE")

    payload = {
        "version": "v1",
        "audit": "form_stat_buttons",
        "target": {
            "input": input_path,
        },
        "summary": {
            "status": "PASS" if not issues else "BLOCKED",
            "issue_count": len(issues),
            "button_box_count": len(button_box),
            "stat_buttons_count": len(stat_buttons),
            "overlap_count": len(overlap),
        },
        "issues": issues,
        "overlap": overlap,
        "missing_semantics": missing_semantics,
        "stat_button_preview": stat_buttons[:5],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit form stat button separation in runtime contract.")
    parser.add_argument("--input", default="tmp/json/form.json")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    payload = run_audit(args.input)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            "status={status} stat_buttons={stat_count} button_box={box_count}".format(
                status=payload["summary"]["status"],
                stat_count=payload["summary"]["stat_buttons_count"],
                box_count=payload["summary"]["button_box_count"],
            )
        )
    if args.strict and payload["summary"]["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
