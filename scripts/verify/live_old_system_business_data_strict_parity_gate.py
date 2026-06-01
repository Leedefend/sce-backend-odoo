#!/usr/bin/env python3
"""Run the live old-system strict parity gate for user acceptance data.

This gate is intentionally conservative: cached old-system evidence is not
enough for closure. It requires live SCBS/SCBSLY credentials, refreshes the
old-system captures, then runs the strict new-system checks.
"""

from __future__ import annotations

import csv
import json
import os
import shlex
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = ROOT / "docs/migration_alignment/scbs_55_user_visible_surface_live_alignment_v1.csv"
OUTPUT = ROOT / "artifacts/migration/live_old_system_business_data_strict_parity_gate_v1.json"
OUTPUT_MD = ROOT / "artifacts/migration/live_old_system_business_data_strict_parity_gate_v1.md"


@dataclass(frozen=True)
class Step:
    name: str
    scope: str
    command: list[str] | str
    shell: bool = False
    required_env: tuple[str, ...] = ()
    env: dict[str, str] = field(default_factory=dict)


def utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def clean(value: object) -> str:
    return str(value or "").strip()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def command_text(command: list[str] | str) -> str:
    if isinstance(command, str):
        return command
    return " ".join(shlex.quote(part) for part in command)


def discover_scbs55_list_seqs() -> list[int]:
    seqs: list[int] = []
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if clean(row.get("config_type")) != "List":
                continue
            if not clean(row.get("config_id")):
                continue
            seqs.append(int(clean(row["seq"])))
    if not seqs:
        raise RuntimeError(f"no SCBS55 list seqs discovered from {INPUT_CSV}")
    return seqs


def env_missing(required: tuple[str, ...], env: dict[str, str]) -> list[str]:
    return [key for key in required if not clean(env.get(key))]


def preflight(env: dict[str, str]) -> dict[str, Any]:
    missing: list[str] = []
    if not clean(env.get("OLD_SCBS_USERNAME")):
        missing.append("OLD_SCBS_USERNAME")
    if not clean(env.get("OLD_SCBS_PASSWORD")):
        missing.append("OLD_SCBS_PASSWORD")

    scbsly_has_dedicated = clean(env.get("SCBSLY_USERNAME")) and clean(env.get("SCBSLY_PASSWORD"))
    scbsly_has_fallback = clean(env.get("OLD_SCBS_USERNAME")) and clean(env.get("OLD_SCBS_PASSWORD"))
    if not scbsly_has_dedicated and not scbsly_has_fallback:
        missing.extend(["SCBSLY_USERNAME or OLD_SCBS_USERNAME", "SCBSLY_PASSWORD or OLD_SCBS_PASSWORD"])

    if not clean(env.get("LIVE_STRICT_ODOO_SHELL_CMD")):
        missing.append("LIVE_STRICT_ODOO_SHELL_CMD")

    if scbsly_has_dedicated:
        scbsly_credentials_source = "SCBSLY_*"
    elif scbsly_has_fallback:
        scbsly_credentials_source = "OLD_SCBS_* fallback"
    else:
        scbsly_credentials_source = "unavailable"

    return {
        "status": "PASS" if not missing else "FAIL",
        "missing_env": missing,
        "scbs_base_url": env.get("OLD_SCBS_BASE_URL") or "https://www.builderp.cn/SCBS",
        "scbsly_base_url": env.get("SCBSLY_BASE_URL") or "https://www.builderp.cn/SCBSLY_V2",
        "scbsly_credentials_source": scbsly_credentials_source,
        "cached_evidence_allowed_for_closure": False,
    }


def build_steps(run_dir: Path, seqs: list[int], env: dict[str, str]) -> list[Step]:
    scbs55_dump_dir = run_dir / "scbs55_old_live_rows"
    scbsly_dump_dir = run_dir / "scbsly_direct_project_old_rows"
    common_env = {
        "SCBS55_OLD_FULL_DUMP_DIR": str(scbs55_dump_dir),
        "SCBS55_OLD_FULL_DUMP_SEQS": ",".join(str(seq) for seq in seqs),
        "MIGRATION_SCBS55_OLD_FULL_DUMP_DIR": str(scbs55_dump_dir),
        "SCBSLY_OLD_ROWS_DIR": str(scbsly_dump_dir),
        "MIGRATION_SCBSLY_OLD_ROWS_DIR": str(scbsly_dump_dir),
        "SCBSLY_OLD_ROW_DUMP_OVERWRITE": "1",
        "ARTIFACTS_DIR": str(ROOT / "artifacts"),
        "DB_NAME": env.get("DB_NAME") or env.get("E2E_DB") or "sc_demo",
        "FRONTEND_URL": env.get("FRONTEND_URL") or env.get("BASE_URL") or "http://1.95.85.92:18081",
        "E2E_LOGIN": env.get("E2E_LOGIN") or "wutao",
        "E2E_PASSWORD": env.get("E2E_PASSWORD") or "123456",
    }
    odoo_shell = clean(env.get("LIVE_STRICT_ODOO_SHELL_CMD"))
    odoo_env_prefix = (
        f"DB_NAME={shlex.quote(common_env['DB_NAME'])} "
        f"MIGRATION_ARTIFACT_ROOT={shlex.quote(str(run_dir / 'odoo_artifacts'))} "
        f"MIGRATION_SCBS55_OLD_FULL_DUMP_DIR={shlex.quote(str(scbs55_dump_dir))} "
        f"SCBS55_OLD_FULL_DUMP_DIR={shlex.quote(str(scbs55_dump_dir))} "
    )

    steps: list[Step] = [
        Step(
            name="scbs55_online_list_count_probe",
            scope="SCBS55 live old system",
            command=["python3", "scripts/verify/scbs_55_old_system_list_count_probe.py"],
            required_env=("OLD_SCBS_USERNAME", "OLD_SCBS_PASSWORD"),
        ),
        Step(
            name="scbs55_online_full_row_dump",
            scope="SCBS55 live old system",
            command=["python3", "scripts/verify/scbs_55_old_system_list_full_row_dump.py"],
            required_env=("OLD_SCBS_USERNAME", "OLD_SCBS_PASSWORD"),
            env=common_env,
        ),
        Step(
            name="scbs55_old_new_browser_surface_compare",
            scope="SCBS55 strict old/new visible surface",
            command=["node", "scripts/verify/scbs_55_old_new_browser_surface_compare.js"],
            required_env=("OLD_SCBS_USERNAME", "OLD_SCBS_PASSWORD"),
            env=common_env,
        ),
        Step(
            name="scbs55_browser_full_visible_data_coverage",
            scope="SCBS55 browser full visible data coverage",
            command=["node", "scripts/verify/scbs_55_browser_full_visible_data_coverage.js"],
            env=common_env,
        ),
        Step(
            name="scbs55_legacy_visible_field_full_reconcile",
            scope="SCBS55 new system Odoo strict field reconcile",
            command=odoo_env_prefix
            + f"{odoo_shell} < scripts/migration/scbs_55_legacy_visible_field_full_reconcile_probe.py",
            shell=True,
            required_env=("LIVE_STRICT_ODOO_SHELL_CMD",),
        ),
        Step(
            name="scbs55_user_visible_business_data_final_probe",
            scope="SCBS55 new system Odoo final business data probe",
            command=odoo_env_prefix
            + f"{odoo_shell} < scripts/migration/scbs_55_user_visible_business_data_final_probe.py",
            shell=True,
            required_env=("LIVE_STRICT_ODOO_SHELL_CMD",),
        ),
        Step(
            name="scbsly_online_menu_probe",
            scope="SCBSLY live old system",
            command=["python3", "scripts/verify/scbsly_direct_project_acceptance_menu_probe.py"],
            required_env=("OLD_SCBS_USERNAME", "OLD_SCBS_PASSWORD"),
            env=common_env,
        ),
        Step(
            name="scbsly_online_old_row_dump",
            scope="SCBSLY live old system",
            command=["python3", "scripts/verify/scbsly_direct_project_old_row_dump.py"],
            required_env=("OLD_SCBS_USERNAME", "OLD_SCBS_PASSWORD"),
            env=common_env,
        ),
        Step(
            name="scbsly_old_identity_lock",
            scope="SCBSLY live old system",
            command=["python3", "scripts/verify/scbsly_direct_project_old_identity_lock.py"],
            env=common_env,
        ),
        Step(
            name="scbsly_new_system_alignment_probe",
            scope="SCBSLY new system alignment",
            command=["node", "scripts/verify/scbsly_direct_project_new_system_alignment_probe.js"],
            env=common_env,
        ),
        Step(
            name="scbsly_strict_visible_acceptance",
            scope="SCBSLY strict old/new visible acceptance",
            command=["python3", "scripts/verify/scbsly_direct_project_strict_visible_acceptance.py"],
            required_env=("OLD_SCBS_USERNAME", "OLD_SCBS_PASSWORD"),
            env=common_env,
        ),
        Step(
            name="user_visible_business_fact_alignment",
            scope="Full user-visible business facts",
            command=odoo_env_prefix + f"{odoo_shell} < scripts/migration/user_visible_business_fact_alignment_probe.py",
            shell=True,
            required_env=("LIVE_STRICT_ODOO_SHELL_CMD",),
        ),
        Step(
            name="user_data_reconciliation_full_scope_probe",
            scope="Full user acceptance data scope",
            command=odoo_env_prefix + f"{odoo_shell} < scripts/verify/user_data_reconciliation_full_scope_probe.py",
            shell=True,
            required_env=("LIVE_STRICT_ODOO_SHELL_CMD",),
        ),
    ]
    return steps


def run_step(step: Step, run_dir: Path, env: dict[str, str]) -> dict[str, Any]:
    missing = env_missing(step.required_env, env)
    log_path = run_dir / "logs" / f"{step.name}.log"
    if missing:
        return {
            "name": step.name,
            "scope": step.scope,
            "status": "SKIPPED",
            "blocking_reason": "missing_required_env",
            "missing_env": missing,
            "command": command_text(step.command),
            "log": str(log_path.relative_to(ROOT)),
        }

    log_path.parent.mkdir(parents=True, exist_ok=True)
    merged_env = os.environ.copy()
    merged_env.update(step.env)
    started = datetime.now(timezone.utc).isoformat()
    print(f"[live-strict-gate] RUN {step.name}: {command_text(step.command)}", flush=True)
    with log_path.open("w", encoding="utf-8") as handle:
        handle.write(f"$ {command_text(step.command)}\n")
        handle.flush()
        completed = subprocess.run(
            step.command,
            cwd=ROOT,
            env=merged_env,
            shell=step.shell,
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=False,
            text=True,
        )
    status = "PASS" if completed.returncode == 0 else "FAIL"
    print(f"[live-strict-gate] {status} {step.name} rc={completed.returncode}", flush=True)
    return {
        "name": step.name,
        "scope": step.scope,
        "status": status,
        "returncode": completed.returncode,
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "command": command_text(step.command),
        "log": str(log_path.relative_to(ROOT)),
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Live Old-System Business Data Strict Parity Gate v1",
        "",
        f"Status: `{report['status']}`",
        f"Blocking Reason: `{report.get('blocking_reason') or ''}`",
        f"Run Dir: `{report['run_dir']}`",
        f"Generated At: `{report['generated_at']}`",
        "",
        "## Preconditions",
        "",
        f"- SCBS: `{report['preflight']['scbs_base_url']}`",
        f"- SCBSLY: `{report['preflight']['scbsly_base_url']}`",
        f"- Cached evidence allowed for closure: `{report['preflight']['cached_evidence_allowed_for_closure']}`",
        f"- Missing env: `{', '.join(report['preflight']['missing_env']) or 'none'}`",
        "",
        "## Steps",
        "",
        "| Step | Scope | Status | Log |",
        "| --- | --- | --- | --- |",
    ]
    for row in report["steps"]:
        lines.append(
            "| {name} | {scope} | {status} | `{log}` |".format(
                name=row["name"],
                scope=row["scope"],
                status=row["status"],
                log=row.get("log", ""),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    env = os.environ.copy()
    run_dir = ROOT / "artifacts/migration/live_old_system_strict_parity_gate" / utc_slug()
    run_dir.mkdir(parents=True, exist_ok=True)
    seqs = discover_scbs55_list_seqs()
    steps = build_steps(run_dir, seqs, env)
    preflight_result = preflight(env)
    step_results: list[dict[str, Any]] = []

    if preflight_result["status"] == "FAIL":
        for step in steps:
            missing = env_missing(step.required_env, env)
            step_results.append(
                {
                    "name": step.name,
                    "scope": step.scope,
                    "status": "SKIPPED",
                    "blocking_reason": "preflight_failed",
                    "missing_env": missing,
                    "command": command_text(step.command),
                    "log": str((run_dir / "logs" / f"{step.name}.log").relative_to(ROOT)),
                }
            )
        status = "FAIL"
        if "LIVE_STRICT_ODOO_SHELL_CMD" in preflight_result["missing_env"]:
            blocking_reason = "missing_live_old_system_or_odoo_gate_configuration"
        else:
            blocking_reason = "missing_live_old_system_credentials"
    else:
        for step in steps:
            step_results.append(run_step(step, run_dir, env))
        failures = [row for row in step_results if row["status"] != "PASS"]
        status = "PASS" if not failures else "FAIL"
        blocking_reason = "" if status == "PASS" else "strict_parity_step_failed"

    report = {
        "mode": "live_old_system_business_data_strict_parity_gate",
        "status": status,
        "blocking_reason": blocking_reason,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir.relative_to(ROOT)),
        "scbs55_list_seq_count": len(seqs),
        "scbs55_list_seqs": seqs,
        "preflight": preflight_result,
        "steps": step_results,
    }
    write_json(OUTPUT, report)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(markdown(report), encoding="utf-8")
    print(f"LIVE_OLD_SYSTEM_BUSINESS_DATA_STRICT_PARITY_GATE={status} output={OUTPUT}")
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
