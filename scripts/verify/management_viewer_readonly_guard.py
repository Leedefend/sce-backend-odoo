#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROLE_FLOOR_JSON = ROOT / "artifacts" / "backend" / "role_capability_floor_prod_like.json"
OUT_JSON = ROOT / "artifacts" / "backend" / "management_viewer_readonly_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "management_viewer_readonly_guard.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    floor = _load_json(ROLE_FLOOR_JSON)
    errors: list[str] = []
    summary: dict = {
        "executive_found": False,
        "executive_login": "",
        "journey_intents": [],
        "read_probe_count": 0,
        "capability_count": 0,
    }

    if not floor:
        errors.append(f"missing role floor artifact: {ROLE_FLOOR_JSON.as_posix()}")
    roles = floor.get("roles") if isinstance(floor.get("roles"), list) else []
    executive = None
    for row in roles:
        if not isinstance(row, dict):
            continue
        if str(row.get("role") or "").strip() == "executive":
            executive = row
            break
    if not isinstance(executive, dict):
        errors.append("executive fixture not found in role floor artifact")
    else:
        summary["executive_found"] = True
        summary["executive_login"] = str(executive.get("login") or "").strip()
        summary["capability_count"] = int(executive.get("capability_count") or 0)
        read_probes = executive.get("read_probes") if isinstance(executive.get("read_probes"), list) else []
        summary["read_probe_count"] = len(read_probes)
        journey = executive.get("journey") if isinstance(executive.get("journey"), list) else []
        journey_intents = []
        for item in journey:
            if not isinstance(item, dict):
                continue
            intent = str(item.get("intent") or "").strip()
            ok = bool(item.get("ok"))
            if intent:
                journey_intents.append(intent)
            if not ok:
                errors.append(f"executive journey intent failed: {intent or '<empty>'}")
        summary["journey_intents"] = journey_intents
        allowed_readonly_journey = {"system.init", "ui.contract"}
        invalid = sorted({intent for intent in journey_intents if intent not in allowed_readonly_journey})
        if invalid:
            errors.append(f"executive journey includes non-readonly intents: {invalid}")
        if len(read_probes) < 1:
            errors.append("executive read probe missing")
        if int(summary["capability_count"]) < 1:
            errors.append("executive capability_count must be >= 1")

    report = {
        "ok": len(errors) == 0,
        "summary": summary,
        "errors": errors,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Management Viewer Readonly Guard",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- executive_found: {summary['executive_found']}",
        f"- executive_login: {summary['executive_login'] or '-'}",
        f"- journey_intents: {','.join(summary['journey_intents']) if summary['journey_intents'] else '-'}",
        f"- read_probe_count: {summary['read_probe_count']}",
        f"- capability_count: {summary['capability_count']}",
        f"- error_count: {len(errors)}",
    ]
    if errors:
        lines.extend(["", "## Errors", ""])
        for item in errors:
            lines.append(f"- {item}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON))
    print(str(OUT_MD))
    if errors:
        print("[management_viewer_readonly_guard] FAIL")
        return 1
    print("[management_viewer_readonly_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

