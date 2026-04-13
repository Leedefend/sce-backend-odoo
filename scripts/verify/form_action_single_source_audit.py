#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "contract" / "form_action_single_source_v1.json"


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
    name = str(action.get("name") or "").strip()
    method = str(payload.get("method") or "").strip()
    action_id = payload.get("action_id")
    ref = str(payload.get("ref") or payload.get("xml_id") or "").strip()
    if name or method or ref or action_id not in (None, ""):
        return f"name:{name}|method:{method}|action_id:{action_id}|ref:{ref}"
    label = str(action.get("label") or action.get("string") or "").strip()
    return f"label:{label}" if label else "unknown"


def run_audit(input_path: str) -> dict[str, Any]:
    data = _load_payload(input_path)
    form = ((data.get("views") or {}).get("form") or {}) if isinstance(data, dict) else {}

    surfaces = {
        "buttons": [row for row in _as_list(data.get("buttons")) if isinstance(row, dict)],
        "header_buttons": [row for row in _as_list(form.get("header_buttons")) if isinstance(row, dict)],
        "button_box": [row for row in _as_list(form.get("button_box")) if isinstance(row, dict)],
        "stat_buttons": [row for row in _as_list(form.get("stat_buttons")) if isinstance(row, dict)],
    }

    group_actions: list[dict[str, Any]] = []
    for group in _as_list(data.get("action_groups")):
        if not isinstance(group, dict):
            continue
        for action in _as_list(group.get("actions")):
            if isinstance(action, dict):
                group_actions.append(action)
    surfaces["action_groups"] = group_actions

    issues: list[str] = []
    surface_duplicates: dict[str, int] = {}
    for key, rows in surfaces.items():
        identities = [_identity(row) for row in rows]
        duplicate_count = len(identities) - len(set(identities))
        surface_duplicates[key] = duplicate_count
        if duplicate_count > 0:
            issues.append(f"{key}:DUPLICATE_IDENTITIES")

    canonical_labels: dict[str, str] = {}
    label_conflicts: list[str] = []
    for rows in surfaces.values():
        for row in rows:
            identity = _identity(row)
            label = str(row.get("label") or row.get("string") or "").strip()
            if identity in canonical_labels and label and canonical_labels[identity] and canonical_labels[identity] != label:
                label_conflicts.append(identity)
            elif identity not in canonical_labels:
                canonical_labels[identity] = label
    if label_conflicts:
        issues.append("CROSS_SURFACE_LABEL_CONFLICT")

    payload = {
        "version": "v1",
        "audit": "form_action_single_source",
        "target": {"input": input_path},
        "summary": {
            "status": "PASS" if not issues else "BLOCKED",
            "issue_count": len(issues),
            "surface_counts": {k: len(v) for k, v in surfaces.items()},
        },
        "surface_duplicates": surface_duplicates,
        "label_conflicts": sorted(set(label_conflicts)),
        "issues": issues,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit form action single-source consistency.")
    parser.add_argument("--input", default="tmp/json/form.json")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    payload = run_audit(args.input)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            "status={status} issue_count={issue_count}".format(
                status=payload["summary"]["status"],
                issue_count=payload["summary"]["issue_count"],
            )
        )
    if args.strict and payload["summary"]["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
