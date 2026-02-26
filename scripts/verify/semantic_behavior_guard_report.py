#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "semantic_behavior_guard_baseline.json"
REPORT_JSON = ROOT / "artifacts" / "backend" / "semantic_behavior_guard_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "semantic_behavior_guard_report.md"

CASES = {
    "execute_button_dry_run": ROOT / "docs" / "contract" / "snapshots" / "execute_button_intent_dry_run_pm.json",
    "portal_execute_button_not_allowed": ROOT / "docs" / "contract" / "snapshots" / "portal_execute_button_not_allowed.json",
    "system_init_admin": ROOT / "docs" / "contract" / "snapshots" / "system_init_intent_admin.json",
}


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _hash_payload(payload: dict) -> str:
    canon = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]


def _extract_case(case_key: str, payload: dict) -> dict:
    raw = payload.get("ui_contract_raw") if isinstance(payload.get("ui_contract_raw"), dict) else {}
    if case_key == "execute_button_dry_run":
        result = ((raw.get("result") if isinstance(raw.get("result"), dict) else {}))
        return {
            "status": str(result.get("status") or ""),
            "success": bool(result.get("success")),
            "reason_code": str(result.get("reason_code") or ""),
            "type": str(result.get("type") or ""),
            "method": str(result.get("method") or ""),
            "button_type": str(result.get("button_type") or ""),
        }
    if case_key == "portal_execute_button_not_allowed":
        error = raw.get("error") if isinstance(raw.get("error"), dict) else {}
        target = raw.get("target") if isinstance(raw.get("target"), dict) else {}
        return {
            "allowed": bool(raw.get("allowed")),
            "error_code": str(error.get("code") or ""),
            "target_model": str(target.get("model") or ""),
            "target_method": str(target.get("method") or ""),
        }
    if case_key == "system_init_admin":
        caps = raw.get("capabilities") if isinstance(raw.get("capabilities"), list) else []
        intents = raw.get("intents") if isinstance(raw.get("intents"), list) else []
        feature_flags = raw.get("feature_flags") if isinstance(raw.get("feature_flags"), dict) else {}
        return {
            "capability_count": len(caps),
            "intent_count": len(intents),
            "feature_flag_keys": sorted(feature_flags.keys()),
            "default_route_keys": sorted((raw.get("default_route") if isinstance(raw.get("default_route"), dict) else {}).keys()),
        }
    return {}


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    observed: dict[str, dict] = {}
    for case_key, path in CASES.items():
        payload = _load_json(path)
        if not payload:
            errors.append(f"missing_case_payload={path.relative_to(ROOT).as_posix()}")
            continue
        semantic = _extract_case(case_key, payload)
        observed[case_key] = {
            "source": path.relative_to(ROOT).as_posix(),
            "semantic": semantic,
            "fingerprint": _hash_payload(semantic),
        }

    baseline = _load_json(BASELINE_JSON)
    baseline_cases = baseline.get("cases") if isinstance(baseline.get("cases"), dict) else {}

    if os.getenv("SEMANTIC_BEHAVIOR_BOOTSTRAP") == "1":
        BASELINE_JSON.parent.mkdir(parents=True, exist_ok=True)
        BASELINE_JSON.write_text(
            json.dumps({"version": "v1", "cases": observed}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        warnings.append("baseline bootstrapped from current observed semantics")
        baseline_cases = {k: v for k, v in observed.items()}

    if not baseline_cases:
        errors.append(f"missing baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")

    drift_items = []
    for key, row in observed.items():
        baseline_row = baseline_cases.get(key) if isinstance(baseline_cases.get(key), dict) else {}
        baseline_fp = str(baseline_row.get("fingerprint") or "")
        current_fp = str(row.get("fingerprint") or "")
        if not baseline_fp:
            drift_items.append({"case": key, "type": "baseline_missing", "current_fingerprint": current_fp})
            continue
        if baseline_fp != current_fp:
            drift_items.append(
                {
                    "case": key,
                    "type": "semantic_drift",
                    "baseline_fingerprint": baseline_fp,
                    "current_fingerprint": current_fp,
                    "baseline_semantic": baseline_row.get("semantic") if isinstance(baseline_row.get("semantic"), dict) else {},
                    "current_semantic": row.get("semantic"),
                }
            )

    if drift_items:
        errors.append(f"semantic_drift_count={len(drift_items)}")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "case_count": len(observed),
            "drift_count": len(drift_items),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "observed": observed,
        "drifts": drift_items,
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Semantic Behavior Guard Report",
        "",
        f"- case_count: {len(observed)}",
        f"- drift_count: {len(drift_items)}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## Cases",
        "",
    ]
    for key, row in observed.items():
        lines.append(f"- {key}: {row.get('fingerprint')} ({row.get('source')})")
    lines.extend(["", "## Drifts", ""])
    if drift_items:
        for item in drift_items:
            lines.append(f"- {item['case']}: {item['type']}")
    else:
        lines.append("- none")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[semantic_behavior_guard_report] FAIL")
        return 2
    print("[semantic_behavior_guard_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

