#!/usr/bin/env python3
"""Replay migration business topics in a controlled sequence."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = REPO_ROOT / "artifacts/migration/replay"
DEFAULT_CONTAINER = "sc-backend-odoo-dev-odoo-1"
DEFAULT_ODOO_CONFIG = "/var/lib/odoo/odoo.conf"


@dataclass(frozen=True)
class ReplayStep:
    step_id: str
    kind: str
    description: str
    script: str | None = None


TOPICS: dict[str, list[ReplayStep]] = {
    "imported_business_continuity_v1": [
        ReplayStep(
            step_id="project_continuity",
            kind="odoo_sync",
            description="Align imported projects with downstream facts to execution state.",
            script="project_continuity_downstream_fact_state_sync.py",
        ),
        ReplayStep(
            step_id="contract_continuity",
            kind="odoo_sync",
            description="Align imported contracts to confirmed/running from downstream facts.",
            script="contract_continuity_downstream_fact_state_sync.py",
        ),
        ReplayStep(
            step_id="payment_downstream_fact_screen",
            kind="host_python",
            description="Regenerate payment downstream approval evidence rows.",
            script="legacy_payment_approval_downstream_fact_screen.py",
        ),
        ReplayStep(
            step_id="payment_done_fact",
            kind="odoo_sync",
            description="Align downstream-approved payment requests to done/validated.",
            script="legacy_payment_approval_downstream_fact_state_sync.py",
        ),
        ReplayStep(
            step_id="payment_linkage_fact",
            kind="odoo_sync",
            description="Align deterministic payment company and contract links.",
            script="payment_linkage_fact_sync.py",
        ),
        ReplayStep(
            step_id="operational_verify",
            kind="odoo_verify",
            description="Verify post-replay project, contract, and payment continuity metrics.",
        ),
    ]
}


VERIFY_SQL = r'''
import json

def row(query):
    env.cr.execute(query)
    cols = [c[0] for c in env.cr.description]
    return dict(zip(cols, env.cr.fetchone()))

result = {
    "database": env.cr.dbname,
    "project": row("""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE lifecycle_state='in_progress' AND phase_key='execution' AND sc_execution_state='in_progress') AS running,
               COUNT(*) FILTER (WHERE lifecycle_state='draft') AS draft
          FROM project_project
    """),
    "contract": row("""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE state IN ('confirmed','running')) AS usable,
               COUNT(*) FILTER (WHERE state='draft') AS draft,
               COUNT(*) FILTER (WHERE project_id IS NULL OR partner_id IS NULL OR company_id IS NULL) AS missing_required_links
          FROM construction_contract
    """),
    "payment": row("""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE state='done' AND validation_status='validated') AS done_validated,
               COUNT(*) FILTER (WHERE company_id IS NOT NULL) AS company_linked,
               COUNT(*) FILTER (WHERE contract_id IS NOT NULL) AS contract_linked,
               COUNT(*) FILTER (WHERE company_id IS NULL) AS missing_company,
               COUNT(*) FILTER (WHERE contract_id IS NULL) AS missing_contract
          FROM payment_request
    """),
    "payment_contract_company_mismatch": row("""
        SELECT COUNT(*) AS mismatch
          FROM payment_request pr
          JOIN construction_contract cc ON cc.id = pr.contract_id
         WHERE pr.company_id IS DISTINCT FROM cc.company_id
    """),
}
print("BUSINESS_TOPIC_REPLAY_VERIFY=" + json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
'''


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True, choices=sorted(TOPICS))
    parser.add_argument("--db", required=True)
    parser.add_argument("--mode", required=True, choices=["plan", "check", "write"])
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--odoo-config", default=DEFAULT_ODOO_CONFIG)
    parser.add_argument("--run-id", default="")
    return parser.parse_args()


def now_run_id() -> str:
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def run_command(
    command: list[str],
    log_path: Path,
    *,
    cwd: Path = REPO_ROOT,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
) -> dict[str, object]:
    merged_env = dict(os.environ)
    if env:
        merged_env.update(env)
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        env=merged_env,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(completed.stdout, encoding="utf-8")
    return {
        "command": command,
        "returncode": completed.returncode,
        "log": str(log_path.relative_to(REPO_ROOT)),
    }


def odoo_sync_command(container: str, db: str, config: str, script: str, sync_mode: str) -> list[str]:
    script_path = f"/mnt/scripts/migration/{script}"
    inner = f"SYNC_MODE={sync_mode} odoo shell -d {db} -c {config} < {script_path}"
    return ["docker", "exec", container, "sh", "-lc", inner]


def odoo_verify_command(container: str, db: str, config: str) -> list[str]:
    return ["docker", "exec", "-i", container, "odoo", "shell", "-d", db, "-c", config]


def run_step(args: argparse.Namespace, run_dir: Path, step: ReplayStep, mode: str) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    if step.kind == "host_python":
        command = ["python3", f"scripts/migration/{step.script}", "--check"]
        results.append(run_command(command, run_dir / f"{step.step_id}.log"))
        return results

    if step.kind == "odoo_sync":
        modes = ["check"] if mode == "check" else ["check", "write"]
        for sync_mode in modes:
            command = odoo_sync_command(args.container, args.db, args.odoo_config, step.script or "", sync_mode)
            results.append(run_command(command, run_dir / f"{step.step_id}.{sync_mode}.log"))
            if results[-1]["returncode"] != 0:
                return results
        return results

    if step.kind == "odoo_verify":
        command = odoo_verify_command(args.container, args.db, args.odoo_config)
        results.append(
            run_command(
                command,
                run_dir / f"{step.step_id}.log",
                input_text=VERIFY_SQL,
            )
        )
        return results

    raise RuntimeError(f"Unsupported step kind: {step.kind}")


def plan_payload(topic: str, steps: list[ReplayStep]) -> dict[str, object]:
    return {
        "topic": topic,
        "steps": [
            {
                "step_id": step.step_id,
                "kind": step.kind,
                "script": step.script or "",
                "description": step.description,
            }
            for step in steps
        ],
    }


def main() -> int:
    args = parse_args()
    steps = TOPICS[args.topic]
    run_id = args.run_id or now_run_id()
    run_dir = ARTIFACT_ROOT / args.topic / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, object] = {
        "status": "PASS",
        "topic": args.topic,
        "mode": args.mode,
        "database": args.db,
        "run_id": run_id,
        "artifact_dir": str(run_dir.relative_to(REPO_ROOT)),
        "plan": plan_payload(args.topic, steps)["steps"],
        "steps": [],
    }

    if args.mode == "plan":
        (run_dir / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("BUSINESS_TOPIC_REPLAY_PLAN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0

    for step in steps:
        step_result = {
            "step_id": step.step_id,
            "kind": step.kind,
            "description": step.description,
            "runs": run_step(args, run_dir, step, args.mode),
        }
        step_result["status"] = "PASS" if all(item["returncode"] == 0 for item in step_result["runs"]) else "FAIL"
        result["steps"].append(step_result)
        if step_result["status"] != "PASS":
            result["status"] = "FAIL"
            break

    (run_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("BUSINESS_TOPIC_REPLAY_RESULT=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
