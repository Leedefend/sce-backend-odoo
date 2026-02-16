#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
INTENT_CATALOG = ROOT / "docs" / "contract" / "exports" / "intent_catalog.json"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "business_core_journey_guard.json"
ARTIFACT_JSON = ROOT / "artifacts" / "business_core_journey_guard.json"
ARTIFACT_MD = ROOT / "artifacts" / "business_core_journey_guard.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    if not baseline:
        print("[business_core_journey_guard] FAIL")
        print(f"invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    catalog = _load_json(INTENT_CATALOG)
    intents = catalog.get("intents") if isinstance(catalog.get("intents"), list) else []
    by_intent = {}
    for item in intents:
        if not isinstance(item, dict):
            continue
        key = str(item.get("intent") or "").strip()
        if key:
            by_intent[key] = item

    required = baseline.get("required_intents") if isinstance(baseline.get("required_intents"), dict) else {}
    checks = []
    errors = []
    for intent, policy in sorted(required.items()):
        policy = policy if isinstance(policy, dict) else {}
        min_test_refs = int(policy.get("min_test_refs") or 0)
        item = by_intent.get(intent)
        if not isinstance(item, dict):
            checks.append({"intent": intent, "ok": False, "reason": "missing", "test_refs": 0, "min_test_refs": min_test_refs})
            errors.append(f"missing required intent: {intent}")
            continue
        test_refs = int(item.get("test_refs") or 0)
        ok = test_refs >= min_test_refs
        checks.append(
            {
                "intent": intent,
                "ok": ok,
                "reason": "ok" if ok else "insufficient_test_refs",
                "test_refs": test_refs,
                "min_test_refs": min_test_refs,
            }
        )
        if not ok:
            errors.append(f"{intent}: test_refs {test_refs} < min_test_refs {min_test_refs}")

    report = {
        "ok": len(errors) <= int(baseline.get("max_errors", 0)),
        "baseline": baseline,
        "summary": {
            "catalog_intent_count": len(by_intent),
            "required_intent_count": len(required),
            "error_count": len(errors),
        },
        "checks": checks,
        "errors": errors,
    }
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Business Core Journey Guard",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- catalog_intent_count: {report['summary']['catalog_intent_count']}",
        f"- required_intent_count: {report['summary']['required_intent_count']}",
        f"- error_count: {report['summary']['error_count']}",
        "",
        "## Checks",
        "",
    ]
    for item in checks:
        lines.append(
            f"- {item['intent']}: {'PASS' if item['ok'] else 'FAIL'} "
            f"(test_refs={item['test_refs']}, min={item['min_test_refs']})"
        )
    if errors:
        lines.extend(["", "## Errors", ""])
        for item in errors:
            lines.append(f"- {item}")
    ARTIFACT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(ARTIFACT_JSON))
    print(str(ARTIFACT_MD))
    if not report["ok"]:
        print("[business_core_journey_guard] FAIL")
        return 1
    print("[business_core_journey_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
