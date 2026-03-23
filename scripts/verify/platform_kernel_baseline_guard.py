#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "platform_kernel_baseline.json"
INTENT_ENRICHED_JSON = ROOT / "docs" / "contract" / "exports" / "intent_catalog_enriched.json"
CAPABILITY_REGISTRY = ROOT / "addons" / "smart_construction_core" / "services" / "capability_registry.py"
SCENE_REGISTRY = ROOT / "addons" / "smart_construction_scene" / "scene_registry.py"
OUT_JSON = ROOT / "artifacts" / "backend" / "platform_kernel_baseline.json"


def _safe_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _extract_scene_count() -> int:
    if not SCENE_REGISTRY.is_file():
        return 0
    try:
        spec = spec_from_file_location("platform_kernel_scene_registry_probe", SCENE_REGISTRY)
        if spec is None or spec.loader is None:
            raise RuntimeError("spec unavailable")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        loader = getattr(module, "load_scene_configs", None)
        if not callable(loader):
            raise RuntimeError("load_scene_configs missing")
        rows = loader(None)
        if not isinstance(rows, list):
            return 0
        scene_codes = {
            str(row.get("code") or "").strip()
            for row in rows
            if isinstance(row, dict) and str(row.get("code") or "").strip()
        }
        return len(scene_codes)
    except Exception:
        return 0


def _extract_capability_count() -> int:
    if not CAPABILITY_REGISTRY.is_file():
        return 0
    try:
        tree = ast.parse(CAPABILITY_REGISTRY.read_text(encoding="utf-8"), filename=str(CAPABILITY_REGISTRY))
    except Exception:
        return 0
    keys: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "_cap":
            continue
        if not node.args:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            text = arg.value.strip()
            if text:
                keys.add(text)
    return len(keys)


def _extract_intent_counts() -> tuple[int, int, dict[str, int]]:
    payload = _safe_json(INTENT_ENRICHED_JSON)
    rows = payload.get("intents") if isinstance(payload.get("intents"), list) else []
    intents = [row for row in rows if isinstance(row, dict) and str(row.get("intent_type") or "").strip()]
    write_count = sum(1 for row in intents if bool(row.get("is_write") or row.get("is_write_operation")))
    layer_distribution = {"core": 0, "domain": 0, "governance": 0}
    for row in intents:
        layer = str(row.get("layer") or "domain").strip().lower()
        if layer not in layer_distribution:
            layer = "domain"
        layer_distribution[layer] += 1
    return len(intents), write_count, layer_distribution


def _load_baseline() -> dict:
    payload = _safe_json(BASELINE_JSON)
    return payload if payload else {
        "intent_count": 0,
        "write_intent_count": 0,
        "capability_count": 0,
        "scene_count": 0,
        "layer_distribution": {"core": 0, "domain": 0, "governance": 0},
    }


def main() -> int:
    intent_count, write_intent_count, layer_distribution = _extract_intent_counts()
    observed = {
        "intent_count": intent_count,
        "write_intent_count": write_intent_count,
        "capability_count": _extract_capability_count(),
        "scene_count": _extract_scene_count(),
        "layer_distribution": layer_distribution,
    }
    baseline = _load_baseline()

    errors: list[str] = []
    for key in ("intent_count", "write_intent_count", "capability_count", "scene_count"):
        observed_value = int(observed.get(key) or 0)
        baseline_value = int(baseline.get(key) or 0)
        if observed_value < baseline_value:
            errors.append(f"{key} regressed: {observed_value} < {baseline_value}")
    for layer in ("core", "domain", "governance"):
        observed_value = int((observed.get("layer_distribution") or {}).get(layer) or 0)
        baseline_value = int((baseline.get("layer_distribution") or {}).get(layer) or 0)
        if observed_value < baseline_value:
            errors.append(f"layer_distribution.{layer} regressed: {observed_value} < {baseline_value}")

    report = {
        "ok": len(errors) == 0,
        "baseline": baseline,
        "observed": observed,
        "errors": errors,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(OUT_JSON))
    if errors:
        for item in errors:
            print(f"- {item}")
        print("[platform_kernel_baseline_guard] FAIL")
        return 2
    print("[platform_kernel_baseline_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
