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


def _resolve_renderability_ok(scene_payload: dict[str, Any], declared_scene_count: int) -> tuple[bool, dict[str, Any]]:
    renderability = scene_payload.get("renderability", {}) if isinstance(scene_payload, dict) else {}
    if not isinstance(renderability, dict):
        return False, {"source": "missing"}

    if isinstance(renderability.get("fully_renderable"), bool):
        return bool(renderability.get("fully_renderable")), {"source": "fully_renderable"}

    # Backward-compatible fallback for older catalogs that only expose counts/ratios.
    renderable_count = renderability.get("renderable_scene_count")
    interaction_ready_count = renderability.get("interaction_ready_scene_count")
    renderable_ratio = renderability.get("renderable_ratio")
    interaction_ready_ratio = renderability.get("interaction_ready_ratio")

    if isinstance(interaction_ready_count, int) and declared_scene_count > 0:
        return interaction_ready_count >= declared_scene_count, {
            "source": "interaction_ready_scene_count",
            "interaction_ready_scene_count": interaction_ready_count,
        }
    if isinstance(renderable_count, int) and declared_scene_count > 0:
        return renderable_count >= declared_scene_count, {
            "source": "renderable_scene_count",
            "renderable_scene_count": renderable_count,
        }
    if isinstance(interaction_ready_ratio, (int, float)):
        return float(interaction_ready_ratio) >= 1.0, {
            "source": "interaction_ready_ratio",
            "interaction_ready_ratio": interaction_ready_ratio,
        }
    if isinstance(renderable_ratio, (int, float)):
        return float(renderable_ratio) >= 1.0, {
            "source": "renderable_ratio",
            "renderable_ratio": renderable_ratio,
        }
    return False, {"source": "unknown"}


def _normalize_string_list(value: object) -> list[str]:
    out: set[str] = set()
    if isinstance(value, list):
        for item in value:
            text = str(item or "").strip()
            if text:
                out.add(text)
    return sorted(out)


def _status(policy: dict[str, Any], profile: str) -> dict[str, Any]:
    result: dict[str, Any] = {"files": {}, "summary": {}}
    ok = True
    blockers: list[str] = []
    warnings: list[str] = []
    intent_count = 0
    scene_count = 0
    intent_keys: set[str] = set()
    scene_keys: set[str] = set()
    intent_test_refs: dict[str, int] = {}
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
                if isinstance(intents, list):
                    intent_keys = {
                        str(item.get("intent") or "").strip()
                        for item in intents
                        if isinstance(item, dict) and str(item.get("intent") or "").strip()
                    }
            elif key == "scene_catalog":
                entry["scene_count"] = int(payload.get("scene_count", 0)) if isinstance(payload, dict) else 0
                scene_count = int(entry["scene_count"])
                scenes = payload.get("scenes") if isinstance(payload, dict) else []
                if isinstance(scenes, list):
                    scene_keys = {
                        str(item.get("scene_key") or "").strip()
                        for item in scenes
                        if isinstance(item, dict) and str(item.get("scene_key") or "").strip()
                    }
                renderability_ok, renderability_meta = _resolve_renderability_ok(payload, scene_count)
                entry["fully_renderable"] = renderability_ok
                entry["renderability_resolved_by"] = renderability_meta
            elif key == "scene_contract_shape_guard":
                entry["shape_guard_ok"] = bool(payload.get("ok", True)) if isinstance(payload, dict) else True
            elif key == "intent_surface_json":
                rows = payload if isinstance(payload, list) else []
                if isinstance(rows, list):
                    for row in rows:
                        if not isinstance(row, dict):
                            continue
                        intent_name = str(row.get("intent") or "").strip()
                        if not intent_name:
                            continue
                        refs = row.get("test_refs", 0)
                        try:
                            intent_test_refs[intent_name] = int(refs)
                        except Exception:
                            intent_test_refs[intent_name] = 0
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
    required_intents = _normalize_string_list(policy.get("required_intents"))
    required_scene_keys = _normalize_string_list(policy.get("required_scene_keys"))
    required_test_ref_intents = _normalize_string_list(policy.get("required_test_ref_intents"))

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

    missing_intents = sorted(set(required_intents) - intent_keys)
    missing_scene_keys = sorted(set(required_scene_keys) - scene_keys)
    if missing_intents:
        ok = False
        blockers.append(f"missing_required_intents:{','.join(missing_intents)}")
    if missing_scene_keys:
        ok = False
        blockers.append(f"missing_required_scene_keys:{','.join(missing_scene_keys)}")

    missing_test_ref_intents = sorted(
        intent for intent in required_test_ref_intents if int(intent_test_refs.get(intent, 0)) <= 0
    )
    if missing_test_ref_intents:
        ok = False
        blockers.append(f"missing_required_test_refs:{','.join(missing_test_ref_intents)}")

    untested_intents = sorted(intent for intent in intent_keys if int(intent_test_refs.get(intent, 0)) <= 0)
    warning_untested_limit = int(policy.get("warning_untested_limit", 0))
    if warning_untested_limit > 0 and len(untested_intents) > warning_untested_limit:
        warnings.append(f"untested_intents_over_limit:{len(untested_intents)}/{warning_untested_limit}")

    result["summary"] = {
        "profile": profile,
        "ready": ok,
        "intent_count": intent_count,
        "scene_count": scene_count,
        "required_intent_count": len(required_intents),
        "required_scene_key_count": len(required_scene_keys),
        "missing_required_intents": missing_intents,
        "missing_required_scene_keys": missing_scene_keys,
        "required_test_ref_intent_count": len(required_test_ref_intents),
        "missing_required_test_ref_intents": missing_test_ref_intents,
        "untested_intent_count": len(untested_intents),
        "untested_intents_sample": untested_intents[:20],
        "renderability_fully_renderable": renderability_ok,
        "policy": {
            "min_intent_count": min_intent_count,
            "min_scene_count": min_scene_count,
            "require_renderability_fully_renderable": require_renderability,
            "require_scene_shape_guard_ok": require_shape_guard_ok,
            "required_intents": required_intents,
            "required_scene_keys": required_scene_keys,
            "required_test_ref_intents": required_test_ref_intents,
            "warning_untested_limit": warning_untested_limit,
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
        f"- required_intent_count: {result['summary']['required_intent_count']}",
        f"- required_scene_key_count: {result['summary']['required_scene_key_count']}",
        f"- required_test_ref_intent_count: {result['summary']['required_test_ref_intent_count']}",
        f"- renderability_fully_renderable: {result['summary']['renderability_fully_renderable']}",
        f"- missing_required_intents: {', '.join(result['summary'].get('missing_required_intents', [])) or '-'}",
        f"- missing_required_scene_keys: {', '.join(result['summary'].get('missing_required_scene_keys', [])) or '-'}",
        f"- missing_required_test_ref_intents: {', '.join(result['summary'].get('missing_required_test_ref_intents', [])) or '-'}",
        f"- untested_intent_count: {result['summary'].get('untested_intent_count', 0)}",
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
