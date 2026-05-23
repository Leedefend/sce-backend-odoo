#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import hashlib
import json
import os
from datetime import datetime, timezone
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


def _extract_repr_data(raw_text: str) -> dict:
    marker = "data="
    start = raw_text.find(marker)
    if start < 0:
        return {}
    start += len(marker)
    if start >= len(raw_text) or raw_text[start] != "{":
        return {}
    depth = 0
    end = None
    for idx, ch in enumerate(raw_text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = idx + 1
                break
    if end is None:
        return {}
    try:
        parsed = ast.literal_eval(raw_text[start:end])
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _extract_ui_contract_data(payload: dict) -> dict:
    raw = payload.get("ui_contract_raw") if isinstance(payload.get("ui_contract_raw"), dict) else {}
    raw_payload = raw.get("raw")
    if isinstance(raw_payload, dict):
        raw = raw_payload or raw
    elif isinstance(raw_payload, str):
        parsed = _extract_repr_data(raw_payload)
        if parsed:
            raw = parsed
    if isinstance(raw.get("data"), dict):
        raw = raw.get("data") or raw
        if isinstance(raw.get("data"), dict):
            raw = raw.get("data") or raw
    return raw if isinstance(raw, dict) else {}


def _extract_case(case_key: str, payload: dict) -> dict:
    raw = _extract_ui_contract_data(payload)
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
        if not caps:
            delivery_engine = raw.get("delivery_engine_v1") if isinstance(raw.get("delivery_engine_v1"), dict) else {}
            caps = delivery_engine.get("capabilities") if isinstance(delivery_engine.get("capabilities"), list) else []
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
    baseline_version = str(baseline.get("version") or "") if isinstance(baseline, dict) else ""
    baseline_age_days = None
    if BASELINE_JSON.exists():
        baseline_age_days = int(
            (datetime.now(timezone.utc).timestamp() - BASELINE_JSON.stat().st_mtime) // 86400
        )

    if os.getenv("SEMANTIC_BEHAVIOR_BOOTSTRAP") == "1":
        BASELINE_JSON.parent.mkdir(parents=True, exist_ok=True)
        now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        BASELINE_JSON.write_text(
            json.dumps({"version": "v1", "meta": {"generated_at": now_iso}, "cases": observed}, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
        warnings.append("baseline bootstrapped from current observed semantics")
        baseline_cases = {k: v for k, v in observed.items()}
        baseline_version = "v1"
        baseline_age_days = 0

    if not baseline_cases:
        errors.append(f"missing baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
    if baseline_version and baseline_version != "v1":
        warnings.append(f"unexpected_baseline_version={baseline_version}")
    max_age_days = max(1, int(os.getenv("SEMANTIC_BEHAVIOR_BASELINE_MAX_AGE_DAYS", "30")))
    if baseline_age_days is not None and baseline_age_days > max_age_days:
        warnings.append(f"baseline_age_days={baseline_age_days} (> {max_age_days})")

    drift_items = []
    missing_baseline_cases = []
    for key, row in observed.items():
        baseline_row = baseline_cases.get(key) if isinstance(baseline_cases.get(key), dict) else {}
        baseline_fp = str(baseline_row.get("fingerprint") or "")
        current_fp = str(row.get("fingerprint") or "")
        if not baseline_fp:
            missing_baseline_cases.append(key)
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
            "baseline_missing_case_count": len(missing_baseline_cases),
            "baseline_version": baseline_version or "unknown",
            "baseline_age_days": baseline_age_days,
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
