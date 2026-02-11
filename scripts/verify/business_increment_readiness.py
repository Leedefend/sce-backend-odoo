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
POLICY_PATH = ROOT / "scripts" / "verify" / "baselines" / "business_increment_readiness_policy.json"

REQUIRED_FILES = {
    "intent_catalog": ROOT / "docs" / "contract" / "exports" / "intent_catalog.json",
    "scene_catalog": ROOT / "docs" / "contract" / "exports" / "scene_catalog.json",
    "intent_surface_json": ROOT / "artifacts" / "intent_surface_report.json",
    "scene_contract_shape_guard": ROOT / "artifacts" / "scene_contract_shape_guard.json",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_policy(profile: str) -> dict[str, Any]:
    payload = _load_json(POLICY_PATH)
    profiles = payload.get("profiles") if isinstance(payload, dict) else {}
    policy = profiles.get(profile) if isinstance(profiles, dict) else None
    if not isinstance(policy, dict):
        raise ValueError(f"unknown profile: {profile}")
    return policy


def _status(policy: dict[str, Any], profile: str) -> dict[str, Any]:
    result: dict[str, Any] = {"files": {}, "summary": {}}
    ok = True
    blockers: list[str] = []
    warnings: list[str] = []
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
            blockers.append(f"missing_file:{key}")
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
            blockers.append(f"invalid_json:{key}")
        result["files"][key] = entry

    min_intent_count = int(policy.get("min_intent_count", 1))
    min_scene_count = int(policy.get("min_scene_count", 1))
    require_renderability = bool(policy.get("require_renderability_fully_renderable", False))
    require_shape_guard_ok = bool(policy.get("require_scene_shape_guard_ok", True))

    shape_guard_ok = bool(
        ((result.get("files", {}).get("scene_contract_shape_guard", {}) or {}).get("shape_guard_ok", True))
    )
    if intent_count < min_intent_count or scene_count < min_scene_count:
        ok = False
        blockers.append(
            f"catalog_count_below_min:intents={intent_count}/{min_intent_count},scenes={scene_count}/{min_scene_count}"
        )
    if require_renderability and not renderability_ok:
        ok = False
        blockers.append("renderability_not_fully_renderable")
    elif not renderability_ok:
        warnings.append("renderability_not_fully_renderable")
    if require_shape_guard_ok and not shape_guard_ok:
        ok = False
        blockers.append("scene_contract_shape_guard_not_ok")

    result["summary"] = {
        "profile": profile,
        "ready": ok,
        "intent_count": intent_count,
        "scene_count": scene_count,
        "renderability_fully_renderable": renderability_ok,
        "policy": {
            "min_intent_count": min_intent_count,
            "min_scene_count": min_scene_count,
            "require_renderability_fully_renderable": require_renderability,
            "require_scene_shape_guard_ok": require_shape_guard_ok,
        },
        "blockers": blockers,
        "warnings": warnings,
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
        f"- blockers: {', '.join(result['summary'].get('blockers', [])) or '-'}",
        f"- warnings: {', '.join(result['summary'].get('warnings', [])) or '-'}",
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
    parser.add_argument("--profile", default="base")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    profile = "strict" if args.strict else str(args.profile or "base")
    policy = _load_policy(profile)
    result = _status(policy, profile)
    _write(result)
    print("[OK] business increment readiness report")
    print(f"- profile: {profile}")
    print(f"- ready: {result['summary']['ready']}")
    print(f"- out_json: {OUT_JSON.relative_to(ROOT)}")
    print(f"- out_md: {OUT_MD.relative_to(ROOT)}")
    if args.strict and not result["summary"]["ready"]:
        print("[FAIL] readiness required but unmet")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
