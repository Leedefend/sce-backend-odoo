#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_company_snapshot_collect.json"
SNAPSHOT_GUARD_PATH = ROOT / "scripts" / "verify" / "scene_registry_asset_snapshot_guard.py"


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


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    text = _text(value).lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
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


def _run_snapshot(profile_key: str, company_id: int, state_file: str, require_live: bool) -> tuple[int, str]:
    env = os.environ.copy()
    env["SC_SCENE_REGISTRY_ASSET_SNAPSHOT_STATE_FILE"] = state_file
    env["SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE"] = "1" if require_live else "0"
    if company_id > 0:
        env["E2E_COMPANY_ID"] = str(company_id)
    else:
        env.pop("E2E_COMPANY_ID", None)

    process = subprocess.run(
        [sys.executable, SNAPSHOT_GUARD_PATH.as_posix()],
        cwd=ROOT.as_posix(),
        env=env,
        capture_output=True,
        text=True,
    )
    merged = "\n".join([_text(process.stdout), _text(process.stderr)]).strip()
    header = f"[{profile_key}] company_id={company_id if company_id > 0 else 'auto'} state_file={state_file}"
    output = f"{header}\n{merged}".strip()
    return process.returncode, output


def main() -> int:
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        print("[scene_company_snapshot_collect] FAIL")
        print(f" - missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    profiles = _as_list(baseline.get("profiles"))
    if not profiles:
        print("[scene_company_snapshot_collect] FAIL")
        print(" - profiles is empty")
        return 1

    min_profiles_success = _safe_int(baseline.get("min_profiles_success"), 1)
    require_distinct_company_ids = _safe_bool(baseline.get("require_distinct_company_ids"), False)
    min_distinct_company_ids = _safe_int(baseline.get("min_distinct_company_ids"), 1)
    require_live = _safe_bool(baseline.get("require_live"), True)
    allow_state_fallback_on_guard_failure = _safe_bool(
        baseline.get("allow_state_fallback_on_guard_failure"), True
    )

    report_json_path = ROOT / _text(
        baseline.get("report_json") or "artifacts/backend/scene_company_snapshot_collect_report.json"
    )
    report_md_path = ROOT / _text(
        baseline.get("report_md") or "artifacts/backend/scene_company_snapshot_collect_report.md"
    )

    errors: list[str] = []
    warnings: list[str] = []
    profile_reports: list[dict[str, Any]] = []
    observed_company_ids: set[int] = set()

    for row in profiles:
        profile = _as_dict(row)
        profile_key = _text(profile.get("key"))
        if not profile_key:
            errors.append("profile key is required")
            continue
        company_id = _safe_int(profile.get("company_id"), 0)
        state_file = _text(profile.get("state_file"))
        if not state_file:
            errors.append(f"{profile_key}: state_file is required")
            continue

        code, output = _run_snapshot(profile_key, company_id, state_file, require_live)
        state_payload = _load_json(ROOT / state_file)
        effective_company_id = _safe_int(state_payload.get("company_id"), 0)
        if effective_company_id > 0:
            observed_company_ids.add(effective_company_id)

        ok = code == 0
        if code != 0:
            state_scene_count = _safe_int(state_payload.get("scene_count"), 0)
            if allow_state_fallback_on_guard_failure and state_scene_count > 0:
                ok = True
                warnings.append(
                    f"{profile_key}: snapshot guard failed but fallback state accepted (scene_count={state_scene_count})"
                )
            else:
                errors.append(f"{profile_key}: snapshot guard failed")

        profile_reports.append(
            {
                "key": profile_key,
                "requested_company_id": company_id,
                "effective_company_id": effective_company_id,
                "state_file": state_file,
                "ok": ok,
                "guard_exit_code": code,
                "output": output,
            }
        )

    success_count = sum(1 for item in profile_reports if bool(item.get("ok")))
    if success_count < min_profiles_success:
        errors.append(f"success profile count {success_count} < {min_profiles_success}")

    distinct_count = len(observed_company_ids)
    if distinct_count < min_distinct_company_ids:
        warnings.append(
            f"observed distinct company ids {distinct_count} < target {min_distinct_company_ids}; observed={sorted(observed_company_ids)}"
        )
        if require_distinct_company_ids:
            errors.append(
                f"distinct company ids requirement not met: {distinct_count} < {min_distinct_company_ids}"
            )

    report = {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "profile_count": len(profile_reports),
            "success_count": success_count,
            "observed_company_ids": sorted(observed_company_ids),
            "distinct_company_id_count": distinct_count,
            "captured_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        },
        "profiles": profile_reports,
        "thresholds": {
            "min_profiles_success": min_profiles_success,
            "min_distinct_company_ids": min_distinct_company_ids,
            "require_distinct_company_ids": require_distinct_company_ids,
            "require_live": require_live,
        },
        "sources": {
            "baseline": BASELINE_PATH.relative_to(ROOT).as_posix(),
            "snapshot_guard": SNAPSHOT_GUARD_PATH.relative_to(ROOT).as_posix(),
        },
    }

    lines = [
        "# Scene Company Snapshot Collect Report",
        "",
        f"- profile_count: `{len(profile_reports)}`",
        f"- success_count: `{success_count}`",
        f"- observed_company_ids: `{sorted(observed_company_ids)}`",
    ]
    if warnings:
        lines.extend(["", "## Warnings"] + [f"- {item}" for item in warnings])
    if errors:
        lines.extend(["", "## Errors"] + [f"- {item}" for item in errors])

    _write(report_json_path, json.dumps(report, ensure_ascii=False, indent=2))
    _write(report_md_path, "\n".join(lines) + "\n")

    if errors:
        print("[scene_company_snapshot_collect] FAIL")
        for item in errors:
            print(f" - {item}")
        print(report_json_path)
        print(report_md_path)
        return 1

    print(report_json_path)
    print(report_md_path)
    if warnings:
        print("[scene_company_snapshot_collect] PASS_WITH_WARNINGS")
        for item in warnings:
            print(f" - {item}")
    else:
        print("[scene_company_snapshot_collect] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
