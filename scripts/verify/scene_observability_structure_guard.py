#!/usr/bin/env python3
"""Guard scene observability smoke scripts against structural drift."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFY_ROOT = ROOT / "scripts" / "verify"
BASELINE_PATH = VERIFY_ROOT / "baselines" / "scene_observability_structure.json"


def _load_targets() -> dict[str, dict[str, list[str]]]:
    if not BASELINE_PATH.exists():
        raise FileNotFoundError(f"missing baseline: {BASELINE_PATH.relative_to(ROOT)}")
    payload = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    targets = payload.get("targets") if isinstance(payload, dict) else None
    if not isinstance(targets, dict) or not targets:
        raise ValueError("invalid baseline: `targets` must be a non-empty object")
    out: dict[str, dict[str, list[str]]] = {}
    for rel, rules in targets.items():
        if not isinstance(rel, str) or not isinstance(rules, dict):
            continue
        out[rel] = {
            "must_contain": [str(x) for x in (rules.get("must_contain") or [])],
            "must_not_contain": [str(x) for x in (rules.get("must_not_contain") or [])],
        }
    if not out:
        raise ValueError("invalid baseline: no usable targets")
    return out


def _collect_default_targets() -> dict[str, dict[str, list[str]]]:
    tokens_contain = [
        "require('./scene_observability_utils')",
        "probeModels(",
        "assertRequiredModels(",
    ]
    tokens_forbid = ["function isModelMissing("]
    keys = [
        "fe_portal_scene_governance_action_smoke.js",
        "fe_scene_auto_degrade_smoke.js",
        "fe_scene_auto_degrade_notify_smoke.js",
        "fe_scene_package_import_smoke.js",
    ]
    return {
        key: {
            "must_contain": list(tokens_contain),
            "must_not_contain": list(tokens_forbid),
        }
        for key in keys
    }


def _write_default_baseline() -> None:
    payload = {"targets": _collect_default_targets()}
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    update_mode = str(sys.argv[1] if len(sys.argv) > 1 else "").strip().lower() in {"--update", "update"}
    if update_mode:
        _write_default_baseline()
        print("[OK] scene observability structure baseline updated")
        print(f"- file: {BASELINE_PATH.relative_to(ROOT)}")
        return 0
    try:
        targets = _load_targets()
    except Exception as exc:
        print("[FAIL] scene observability structure guard")
        print(f"- {exc}")
        return 1
    errors: list[str] = []
    for rel, rules in targets.items():
        path = VERIFY_ROOT / rel
        if not path.exists():
            errors.append(f"missing file: scripts/verify/{rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for token in rules.get("must_contain", []):
            if token not in text:
                errors.append(f"{rel}: missing token `{token}`")
        for token in rules.get("must_not_contain", []):
            if token in text:
                errors.append(f"{rel}: forbidden token present `{token}`")

    if errors:
        print("[FAIL] scene observability structure guard")
        for err in errors:
            print(f"- {err}")
        return 1

    print("[OK] scene observability structure guard")
    print(f"- files_checked: {len(targets)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
