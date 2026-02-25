#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import random
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "scripts" / "verify" / "baselines" / "capability_scale_stress.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "capability_scale_stress_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "capability_scale_stress_report.json"


def _load_baseline() -> dict:
    if not BASELINE.is_file():
        return {}
    try:
        payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    arr = sorted(values)
    idx = int(round(0.95 * (len(arr) - 1)))
    return float(arr[idx])


def _build_capability_groups(capabilities: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for idx, cap in enumerate(capabilities or []):
        if not isinstance(cap, dict):
            continue
        group_key = str(cap.get("group_key") or "others").strip() or "others"
        bucket = grouped.setdefault(
            group_key,
            {
                "key": group_key,
                "label": str(cap.get("group_label") or group_key),
                "sequence": len(grouped) + 1,
                "capabilities": [],
                "capability_count": 0,
            },
        )
        cap_copy = dict(cap)
        cap_copy["group_sequence"] = idx + 1
        bucket["capabilities"].append(cap_copy)
        bucket["capability_count"] = int(bucket.get("capability_count") or 0) + 1
    result = list(grouped.values())
    result.sort(key=lambda item: str(item.get("key") or ""))
    for seq, item in enumerate(result, start=1):
        item["sequence"] = seq
    return result


def _build_summary(capabilities: list[dict], capability_groups: list[dict]) -> dict:
    summary = {
        "capability_count": len(capabilities or []),
        "group_count": len(capability_groups or []),
        "state_counts": {"READY": 0, "LOCKED": 0, "PREVIEW": 0},
        "capability_state_counts": {"allow": 0, "readonly": 0, "deny": 0, "pending": 0, "coming_soon": 0},
    }
    for cap in capabilities or []:
        if not isinstance(cap, dict):
            continue
        state = str(cap.get("state") or "").strip().upper()
        if state in summary["state_counts"]:
            summary["state_counts"][state] = int(summary["state_counts"].get(state) or 0) + 1
        capability_state = str(cap.get("capability_state") or "").strip().lower()
        if capability_state in summary["capability_state_counts"]:
            summary["capability_state_counts"][capability_state] = (
                int(summary["capability_state_counts"].get(capability_state) or 0) + 1
            )
    return summary


def _gen_capabilities(cap_count: int, role_count: int, group_count: int) -> list[dict]:
    roles = [f"role_{i:02d}" for i in range(role_count)]
    groups = [f"scale_group_{i:02d}" for i in range(group_count)]
    states = ["allow", "readonly", "deny", "pending", "coming_soon"]
    out = []
    random.seed(42)
    for i in range(cap_count):
        key = f"scale.domain_{i % 12:02d}.action_{i:03d}"
        sample_roles = sorted(set(random.sample(roles, k=max(1, (i % 4) + 1))))
        out.append(
            {
                "key": key,
                "name": f"Scale Capability {i:03d}",
                "group_key": groups[i % group_count],
                "group_label": f"Scale Group {i % group_count:02d}",
                "state": "READY",
                "capability_state": states[i % len(states)],
                "required_roles": sample_roles,
                "required_groups": [],
            }
        )
    return out


def main() -> int:
    baseline = _load_baseline()
    iterations = int(baseline.get("iterations") or 30)
    cap_count = int(baseline.get("capability_count") or 120)
    role_count = int(baseline.get("role_count") or 24)
    group_count = int(baseline.get("group_count") or 8)
    max_p95 = float(baseline.get("max_p95_ms") or 25.0)
    max_payload_bytes = int(baseline.get("max_payload_bytes") or 600000)

    errors: list[str] = []
    warnings: list[str] = []
    timings_ms: list[float] = []
    payload_sizes: list[int] = []
    observed_group_counts: list[int] = []

    capabilities = _gen_capabilities(cap_count, role_count, group_count)
    for _ in range(iterations):
        ts0 = time.perf_counter()
        groups = _build_capability_groups(capabilities)
        summary = _build_summary(capabilities, groups)
        elapsed_ms = (time.perf_counter() - ts0) * 1000.0
        timings_ms.append(elapsed_ms)
        payload = {"capabilities": capabilities, "capability_groups": groups, "summary": summary}
        payload_sizes.append(len(json.dumps(payload, ensure_ascii=False).encode("utf-8")))
        observed_group_counts.append(len(groups))

        if summary.get("capability_count") != cap_count:
            errors.append("capability_count mismatch in summary")
            break
        if len(groups) <= 0:
            errors.append("group_count invalid (zero)")
            break
        group_sum = sum(int((item or {}).get("capability_count") or 0) for item in groups if isinstance(item, dict))
        if group_sum != cap_count:
            errors.append("group capability_count sum mismatch")
            break

    p95 = _p95(timings_ms)
    max_payload = max(payload_sizes) if payload_sizes else 0
    if p95 > max_p95:
        errors.append(f"capability scale p95 exceeded: {p95:.2f} > {max_p95:.2f}")
    if max_payload > max_payload_bytes:
        errors.append(f"capability payload exceeded: {max_payload} > {max_payload_bytes}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "iterations": iterations,
            "capability_count": cap_count,
            "role_count": role_count,
            "configured_group_count": group_count,
            "observed_group_count": max(observed_group_counts) if observed_group_counts else 0,
            "p95_ms": round(p95, 2),
            "max_payload_bytes": max_payload,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "thresholds": {
            "max_p95_ms": max_p95,
            "max_payload_bytes": max_payload_bytes,
        },
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Capability Scale Stress Report",
        "",
        f"- iterations: {iterations}",
        f"- capability_count: {cap_count}",
        f"- role_count: {role_count}",
        f"- observed_group_count: {payload['summary']['observed_group_count']}",
        f"- p95_ms: {payload['summary']['p95_ms']}",
        f"- max_payload_bytes: {max_payload}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## Errors",
        "",
    ]
    if errors:
        for item in errors:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        for item in warnings:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[capability_scale_stress_report] FAIL")
        return 2
    print("[capability_scale_stress_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
