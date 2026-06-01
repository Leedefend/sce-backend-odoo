#!/usr/bin/env python3
"""Gate user data migration closure with durable local/server evidence."""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_JSON_NAME = "user_data_migration_closure_gate_result_v1.json"
OUTPUT_REPORT_NAME = "user_data_migration_closure_gate_report_v1.md"


class GateError(RuntimeError):
    pass


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def artifact_root() -> Path:
    root = Path(os.getenv("USER_DATA_MIGRATION_CLOSURE_ARTIFACT_ROOT", str(ROOT / "artifacts/migration")))
    root.mkdir(parents=True, exist_ok=True)
    return root


def parse_prefixed_json(output: str, prefix: str) -> dict[str, Any]:
    for line in reversed(output.splitlines()):
        if line.startswith(prefix):
            return json.loads(line[len(prefix):])
    raise GateError(f"missing output prefix: {prefix}")


def run_process(name: str, command: list[str], env: dict[str, str] | None = None, stdin: str | None = None) -> dict[str, Any]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    proc = subprocess.run(
        command,
        cwd=ROOT,
        env=merged_env,
        input=stdin,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {
        "name": name,
        "command": command,
        "returncode": proc.returncode,
        "output": proc.stdout,
    }


def run_odoo_probe(name: str, script: Path, prefix: str, db_name: str, container_artifact_root: str) -> dict[str, Any]:
    env = {
        "DB_NAME": db_name,
        "MIGRATION_REPLAY_DB_ALLOWLIST": ",".join(sorted({db_name, "sc_demo", "sc_migration_fresh", "sc_prod_sim"})),
        "MIGRATION_ARTIFACT_ROOT": container_artifact_root,
    }
    result = run_process(
        name,
        ["bash", "scripts/ops/odoo_shell_exec.sh"],
        env=env,
        stdin=script.read_text(encoding="utf-8"),
    )
    parsed: dict[str, Any] = {}
    try:
        parsed = parse_prefixed_json(result["output"], prefix)
    except (GateError, json.JSONDecodeError):
        parsed = {}
    result["parsed"] = parsed
    return result


def report_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# User Data Migration Closure Gate",
        "",
        f"Status: {payload['status']}",
        f"Database: {payload['database']}",
        f"Generated At: {payload['generated_at']}",
        "",
        "| Step | Status | Return Code | Key Result |",
        "| --- | --- | ---: | --- |",
    ]
    for step in payload["steps"]:
        lines.append(
            "| {name} | {status} | {returncode} | {summary} |".format(
                name=step["name"],
                status=step["status"],
                returncode=step["returncode"],
                summary=step.get("summary", ""),
            )
        )
    if payload["blocking"]:
        lines.extend(["", "## Blocking", "", "```json", json.dumps(payload["blocking"], ensure_ascii=False, indent=2), "```"])
    return "\n".join(lines) + "\n"


def main() -> int:
    db_name = os.getenv("DB_NAME") or "sc_demo"
    output_root = artifact_root()
    container_artifact_root = os.getenv(
        "USER_DATA_MIGRATION_CLOSURE_CONTAINER_ARTIFACT_ROOT",
        f"/tmp/user_data_migration_closure/{db_name}",
    )

    raw_steps: list[dict[str, Any]] = []
    blocking: list[dict[str, Any]] = []

    asset_verify = run_process(
        "user_asset_verify",
        ["python3", "scripts/migration/user_asset_verify.py", "--asset-root", "migration_assets", "--lane", "user", "--check"],
    )
    asset_payload: dict[str, Any] = {}
    if asset_verify["returncode"] == 0:
        asset_payload = parse_prefixed_json(asset_verify["output"], "USER_ASSET_VERIFY=")
    asset_verify["parsed"] = asset_payload
    raw_steps.append(asset_verify)

    probes = [
        (
            "history_legacy_user_recovery_probe",
            ROOT / "scripts/migration/history_legacy_user_recovery_probe.py",
            "HISTORY_LEGACY_USER_RECOVERY_PROBE=",
        ),
        (
            "user_data_reconciliation_full_scope_probe",
            ROOT / "scripts/verify/user_data_reconciliation_full_scope_probe.py",
            "USER_DATA_RECONCILIATION_FULL_SCOPE_PROBE=",
        ),
        (
            "scbs_55_user_visible_business_data_final_probe",
            ROOT / "scripts/migration/scbs_55_user_visible_business_data_final_probe.py",
            "SCBS_55_USER_VISIBLE_BUSINESS_DATA_FINAL_PROBE=",
        ),
    ]
    for name, script, prefix in probes:
        raw_steps.append(run_odoo_probe(name, script, prefix, db_name, container_artifact_root))

    steps = []
    for raw in raw_steps:
        parsed = raw.get("parsed") or {}
        name = raw["name"]
        status = "PASS" if raw["returncode"] == 0 and parsed.get("status") == "PASS" else "FAIL"
        summary = ""
        if name == "user_asset_verify":
            summary = f"records={parsed.get('records', 0)} package={parsed.get('asset_package_id', '')}"
        elif name == "history_legacy_user_recovery_probe":
            counts = parsed.get("counts") or {}
            summary = (
                f"profiles={counts.get('profiles_total', 0)} roles={counts.get('roles_total', 0)} "
                f"scopes={counts.get('scopes_total', 0)}"
            )
        elif name == "user_data_reconciliation_full_scope_probe":
            summary = (
                f"blocking={parsed.get('blocking_gap_count', 0)} warnings={parsed.get('warning_count', 0)} "
                f"models={parsed.get('model_count', 0)}"
            )
            if parsed.get("blocking_gap_count"):
                status = "FAIL"
        elif name == "scbs_55_user_visible_business_data_final_probe":
            summary = f"rows={parsed.get('row_count', 0)} review={parsed.get('review_count', 0)}"
            if parsed.get("review_count"):
                status = "FAIL"
        if status != "PASS":
            blocking.append(
                {
                    "name": name,
                    "returncode": raw["returncode"],
                    "parsed_status": parsed.get("status"),
                    "output_tail": "\n".join(raw.get("output", "").splitlines()[-40:]),
                }
            )
        steps.append({"name": name, "status": status, "returncode": raw["returncode"], "summary": clean(summary), "parsed": parsed})

    payload = {
        "status": "PASS" if not blocking else "FAIL",
        "mode": "user_data_migration_closure_gate",
        "database": db_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "step_count": len(steps),
        "blocking_count": len(blocking),
        "steps": steps,
        "blocking": blocking,
    }
    (output_root / OUTPUT_JSON_NAME).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_root / OUTPUT_REPORT_NAME).write_text(report_markdown(payload), encoding="utf-8")
    print("USER_DATA_MIGRATION_CLOSURE_GATE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
