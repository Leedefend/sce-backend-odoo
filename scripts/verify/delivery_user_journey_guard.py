#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCENE_MAP_JSON = ROOT / "artifacts" / "backend" / "scene_domain_mapping.json"
JOURNEYS = {
    "pm": ROOT / "docs" / "product" / "delivery" / "v1" / "user_journey_pm.md",
    "finance": ROOT / "docs" / "product" / "delivery" / "v1" / "user_journey_finance.md",
    "purchase": ROOT / "docs" / "product" / "delivery" / "v1" / "user_journey_purchase.md",
    "exec": ROOT / "docs" / "product" / "delivery" / "v1" / "user_journey_exec.md",
}
REPORT_JSON = ROOT / "artifacts" / "backend" / "delivery_user_journey_guard_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "delivery_user_journey_guard_report.md"

SCENE_RE = re.compile(r"`([a-zA-Z0-9_\.]+)`")
ALLOWED_INTENTS = {"ui.contract", "execute_button", "system.init", "api.data"}
SCENE_PREFIXES = ("projects.", "finance.", "cost.", "portal.", "data.", "default", "scene_smoke_default")


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    scene_map = _load(SCENE_MAP_JSON)
    rows = scene_map.get("scene_to_domain") if isinstance(scene_map.get("scene_to_domain"), list) else []
    valid_scene = {
        str(r.get("canonical_scene") or "").strip()
        for r in rows
        if isinstance(r, dict) and str(r.get("canonical_scene") or "").strip()
    }

    checked = []
    unknown_scenes = []
    unknown_intents = []

    for key, path in JOURNEYS.items():
        if not path.is_file():
            errors.append(f"missing_journey_doc={path.relative_to(ROOT).as_posix()}")
            continue
        text = path.read_text(encoding="utf-8")
        quoted = SCENE_RE.findall(text)
        scenes = sorted({x for x in quoted if x.startswith(SCENE_PREFIXES)})
        intents = sorted({x for x in quoted if x in ALLOWED_INTENTS})

        # minimal structural check: at least 3 journey rows
        step_rows = sum(1 for line in text.splitlines() if line.strip().startswith("| ") and "|" in line)
        has_table_steps = step_rows >= 5
        if not has_table_steps:
            errors.append(f"{key}: insufficient journey table rows")

        for s in scenes:
            if s not in valid_scene:
                unknown_scenes.append(f"{key}:{s}")
        if "execute_button" not in text and key in {"pm", "finance", "purchase"}:
            warnings.append(f"{key}: no execute_button step detected")
        if "## Demo Data Anchor" not in text:
            errors.append(f"{key}: missing Demo Data Anchor section")

        checked.append(
            {
                "journey": key,
                "path": path.relative_to(ROOT).as_posix(),
                "scene_count": len(scenes),
                "intent_count": len(intents),
                "has_execute_button": "execute_button" in text,
                "table_rows": step_rows,
            }
        )

    if unknown_scenes:
        errors.append(f"unknown_scene_ref_count={len(unknown_scenes)}")
    if unknown_intents:
        errors.append(f"unknown_intent_ref_count={len(unknown_intents)}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "journey_count": len(checked),
            "unknown_scene_ref_count": len(unknown_scenes),
            "unknown_intent_ref_count": len(unknown_intents),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "checked": checked,
        "unknown_scenes": unknown_scenes,
        "unknown_intents": unknown_intents,
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Delivery User Journey Guard Report",
        "",
        f"- journey_count: {payload['summary']['journey_count']}",
        f"- unknown_scene_ref_count: {payload['summary']['unknown_scene_ref_count']}",
        f"- unknown_intent_ref_count: {payload['summary']['unknown_intent_ref_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        f"- warning_count: {payload['summary']['warning_count']}",
    ]
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[delivery_user_journey_guard] FAIL")
        return 2
    print("[delivery_user_journey_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
