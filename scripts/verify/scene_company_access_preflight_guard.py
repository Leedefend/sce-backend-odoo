#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_company_access_preflight_guard.json"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        print("[scene_company_access_preflight_guard] FAIL")
        print(f" - missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    profiles = _as_list(baseline.get("profiles"))
    if not profiles:
        print("[scene_company_access_preflight_guard] FAIL")
        print(" - profiles is empty")
        return 1

    min_reachable_block = _safe_int(baseline.get("min_reachable_count_block"), 1)
    min_reachable_target = _safe_int(baseline.get("min_reachable_count_target"), 2)
    strict_mode = _text(os.getenv("SC_COMPANY_ACCESS_PREFLIGHT_STRICT")).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    report_json_path = ROOT / _text(
        baseline.get("report_json") or "artifacts/backend/scene_company_access_preflight_report.json"
    )
    report_md_path = ROOT / _text(
        baseline.get("report_md") or "artifacts/backend/scene_company_access_preflight_report.md"
    )

    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    reachable_count = 0

    for item in profiles:
        row = _as_dict(item)
        key = _text(row.get("key"))
        state_file = _text(row.get("state_file"))
        target_company_id = _safe_int(row.get("target_company_id"), 0)
        if not key or not state_file or target_company_id <= 0:
            errors.append(f"invalid profile config: key={key or '-'} state_file={state_file or '-'} target={target_company_id}")
            continue

        state = _load_json(ROOT / state_file)
        if not state:
            errors.append(f"{key}: missing state file {state_file}")
            continue

        effective_company_id = _safe_int(state.get("company_id"), 0)
        allowed_company_ids = [_safe_int(v, 0) for v in _as_list(state.get("allowed_company_ids")) if _safe_int(v, 0) > 0]
        requested_company_id = _safe_int(state.get("login_company_id_requested"), 0)
        reachable = target_company_id == effective_company_id or target_company_id in allowed_company_ids
        if reachable:
            reachable_count += 1
        else:
            warnings.append(
                f"{key}: target company {target_company_id} not reachable (effective={effective_company_id}, allowed={allowed_company_ids})"
            )

        rows.append(
            {
                "key": key,
                "target_company_id": target_company_id,
                "requested_company_id": requested_company_id,
                "effective_company_id": effective_company_id,
                "allowed_company_ids": allowed_company_ids,
                "reachable": reachable,
                "state_file": state_file,
            }
        )

    if reachable_count < min_reachable_block:
        errors.append(f"reachable company profile count {reachable_count} < block threshold {min_reachable_block}")
    if reachable_count < min_reachable_target:
        warnings.append(f"reachable company profile count {reachable_count} < target {min_reachable_target}")
        if strict_mode:
            errors.append(
                f"strict mode enabled and reachable count {reachable_count} < target {min_reachable_target}"
            )

    report = {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "profile_count": len(rows),
            "reachable_count": reachable_count,
            "min_reachable_count_block": min_reachable_block,
            "min_reachable_count_target": min_reachable_target,
            "strict_mode": strict_mode,
            "captured_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        },
        "profiles": rows,
        "sources": {"baseline": BASELINE_PATH.relative_to(ROOT).as_posix()},
    }

    lines = [
        "# Scene Company Access Preflight Report",
        "",
        f"- reachable_count: `{reachable_count}` / `{len(rows)}`",
        f"- strict_mode: `{strict_mode}`",
    ]
    for row in rows:
        lines.append(
            f"- {row['key']}: target={row['target_company_id']} requested={row['requested_company_id']} "
            f"effective={row['effective_company_id']} allowed={row['allowed_company_ids']} reachable={row['reachable']}"
        )
    if warnings:
        lines.extend(["", "## Warnings"] + [f"- {item}" for item in warnings])
    if errors:
        lines.extend(["", "## Errors"] + [f"- {item}" for item in errors])

    _write(report_json_path, json.dumps(report, ensure_ascii=False, indent=2))
    _write(report_md_path, "\n".join(lines) + "\n")

    if errors:
        print("[scene_company_access_preflight_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        print(report_json_path)
        print(report_md_path)
        return 1

    print(report_json_path)
    print(report_md_path)
    if warnings:
        print("[scene_company_access_preflight_guard] PASS_WITH_WARNINGS")
        for item in warnings:
            print(f" - {item}")
    else:
        print("[scene_company_access_preflight_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

