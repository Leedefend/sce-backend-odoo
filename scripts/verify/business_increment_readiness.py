#!/usr/bin/env python3
"""Check contract/scene evidence readiness before business-feature iteration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "business_increment_readiness.latest.json"
OUT_MD = ROOT / "artifacts" / "business_increment_readiness.latest.md"

REQUIRED_FILES = {
    "intent_catalog": ROOT / "docs" / "contract" / "exports" / "intent_catalog.json",
    "scene_catalog": ROOT / "docs" / "contract" / "exports" / "scene_catalog.json",
    "intent_surface_json": ROOT / "artifacts" / "intent_surface_report.json",
    "scene_contract_shape_guard": ROOT / "artifacts" / "scene_contract_shape_guard.json",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _status() -> dict[str, Any]:
    result: dict[str, Any] = {"files": {}, "summary": {}}
    ok = True
    intent_count = 0
    scene_count = 0
    renderability_ok = False

    for key, path in REQUIRED_FILES.items():
        entry = {
            "path": str(path.relative_to(ROOT)),
            "exists": path.exists(),
            "size": path.stat().st_size if path.exists() else 0,
        }
        if not path.exists():
            ok = False
            result["files"][key] = entry
            continue
        try:
            payload = _load_json(path)
            entry["json_ok"] = True
            if key == "intent_catalog":
                intents = payload.get("intents") if isinstance(payload, dict) else []
                entry["intent_count"] = len(intents) if isinstance(intents, list) else 0
                intent_count = int(entry["intent_count"])
            elif key == "scene_catalog":
                entry["scene_count"] = int(payload.get("scene_count", 0)) if isinstance(payload, dict) else 0
                scene_count = int(entry["scene_count"])
                renderability = payload.get("renderability", {}) if isinstance(payload, dict) else {}
                renderability_ok = bool(renderability.get("fully_renderable") is True)
                entry["fully_renderable"] = renderability_ok
            elif key == "scene_contract_shape_guard":
                entry["shape_guard_ok"] = bool(payload.get("ok", True)) if isinstance(payload, dict) else True
        except Exception as exc:
            entry["json_ok"] = False
            entry["error"] = str(exc)
            ok = False
        result["files"][key] = entry

    if intent_count < 1 or scene_count < 1:
        ok = False
    if not renderability_ok:
        ok = False

    result["summary"] = {
        "ready": ok,
        "intent_count": intent_count,
        "scene_count": scene_count,
        "renderability_fully_renderable": renderability_ok,
    }
    return result


def _write(result: dict[str, Any]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    md_lines = [
        "# Business Increment Readiness",
        "",
        f"- ready: {result['summary']['ready']}",
        f"- intent_count: {result['summary']['intent_count']}",
        f"- scene_count: {result['summary']['scene_count']}",
        f"- renderability_fully_renderable: {result['summary']['renderability_fully_renderable']}",
        "",
        "## Files",
    ]
    for key, entry in result["files"].items():
        md_lines.append(
            f"- {key}: exists={entry.get('exists')} json_ok={entry.get('json_ok', '-')}"
            f" path=`{entry.get('path')}`"
        )
    OUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    result = _status()
    _write(result)
    print("[OK] business increment readiness report")
    print(f"- ready: {result['summary']['ready']}")
    print(f"- out_json: {OUT_JSON.relative_to(ROOT)}")
    print(f"- out_md: {OUT_MD.relative_to(ROOT)}")
    if args.strict and not result["summary"]["ready"]:
        print("[FAIL] readiness required but unmet")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
