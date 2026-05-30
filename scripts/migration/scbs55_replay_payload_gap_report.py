#!/usr/bin/env python3
"""Build a replay payload gap report for the SCBS55 full migration package."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ONECLICK = ROOT / "scripts/migration/history_continuity_oneclick.sh"
OUTPUT_JSON = ROOT / "docs/migration_alignment/scbs55_replay_payload_gap_report_v1.json"
OUTPUT_MD = ROOT / "docs/migration_alignment/scbs55_replay_payload_gap_report_v1.md"

RUN_STEP_RE = re.compile(r"run_step\s+(?P<step>[A-Za-z0-9_]+)\s+(?P<command>.*)")
SCRIPT_RE = re.compile(r'scripts/migration/(?P<script>[A-Za-z0-9_./-]+\.py)')
ARTIFACT_RE = re.compile(r'(?P<path>artifacts/migration/[A-Za-z0-9_./\-\u4e00-\u9fa5]+(?:\.csv|\.json|\.gz|\.tsv|\.md|\.xml|\.tgz))')
OUTPUT_NAME_RE = re.compile(r'(?P<name>[A-Za-z0-9_./-]+(?:payload|result|report|snapshot|targets|manifest)[A-Za-z0-9_./-]*(?:\.csv|\.json|\.md|\.tsv|\.gz))')

OPTIONAL_STEP_MARKERS = (
    "attendance_checkin",
    "personnel_movement",
    "salary_line",
    "payment_request_outflow_approved_recovery",
    "payment_request_outflow_done_recovery",
    "project_lifecycle_continuity",
    "contract_unreached_ready",
    "contract_partner_recovery",
    "contract_direction_defer_recovery",
    "partner_master_targeted",
    "partner_master_direction_defer",
    "receipt_parent_recovery",
    "receipt_partner_targeted",
)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def normalize_artifact(path: str) -> str:
    return path.replace("/mnt/", "").replace(str(ROOT) + "/", "").lstrip("./")


def script_path_from_command(command: str) -> Path | None:
    match = SCRIPT_RE.search(command)
    if not match:
        return None
    return ROOT / "scripts/migration" / match.group("script")


def artifact_paths_from_script(script: Path) -> dict[str, list[str]]:
    text = read_text(script)
    inputs: set[str] = set()
    outputs: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        paths = {normalize_artifact(match.group("path")) for match in ARTIFACT_RE.finditer(stripped)}
        if not paths:
            # Some scripts build output names separately from ARTIFACT_ROOT.
            if re.match(r"^(OUTPUT|ROLLBACK|POST|PRE|REPORT)[A-Z0-9_]*\s*=", stripped):
                for match in OUTPUT_NAME_RE.finditer(stripped):
                    outputs.add("artifacts/migration/" + match.group("name").split("/")[-1])
            continue
        if re.match(r"^(INPUT|.*INPUT|.*PAYLOAD|.*MANIFEST|.*CSV|.*JSON)[A-Z0-9_]*\s*=", stripped) and not stripped.startswith(("OUTPUT", "ROLLBACK", "POST", "PRE")):
            inputs.update(paths)
        if re.match(r"^(OUTPUT|ROLLBACK|POST|PRE|REPORT)[A-Z0-9_]*\s*=", stripped):
            outputs.update(paths)
    return {"inputs": sorted(inputs), "outputs": sorted(outputs)}


def step_kind(step: str) -> str:
    if step.endswith("_adapter"):
        return "adapter"
    if step.endswith("_replay") or step.endswith("_completed") or step.endswith("_pending"):
        return "write_replay"
    if "projection" in step:
        return "formal_projection"
    if "probe" in step:
        return "probe"
    if "normalize" in step:
        return "normalization"
    return "other"


def scope_for_step(step: str) -> str:
    return "optional_or_recovery" if any(marker in step for marker in OPTIONAL_STEP_MARKERS) else "required"


def build_report() -> dict[str, Any]:
    text = read_text(ONECLICK)
    rows: list[dict[str, Any]] = []
    missing_inputs: list[dict[str, str]] = []
    runtime_outputs: list[dict[str, str]] = []
    for line in text.splitlines():
        match = RUN_STEP_RE.search(line)
        if not match:
            continue
        step = match.group("step")
        command = match.group("command").strip()
        script = script_path_from_command(command)
        artifacts = artifact_paths_from_script(script) if script else {"inputs": [], "outputs": []}
        inputs = []
        outputs = []
        for item in artifacts["inputs"]:
            exists = (ROOT / item).exists()
            inputs.append({"path": item, "exists": exists})
            if not exists and scope_for_step(step) == "required":
                missing_inputs.append({"step": step, "script": rel(script) if script else "", "path": item})
        for item in artifacts["outputs"]:
            exists = (ROOT / item).exists()
            outputs.append({"path": item, "exists": exists})
            if not exists:
                runtime_outputs.append({"step": step, "script": rel(script) if script else "", "path": item})
        rows.append(
            {
                "step": step,
                "kind": step_kind(step),
                "scope": scope_for_step(step),
                "script": rel(script) if script and script.exists() else "",
                "script_exists": bool(script and script.exists()),
                "input_artifacts": inputs,
                "output_artifacts": outputs,
            }
        )
    kind_counts = Counter(row["kind"] for row in rows)
    scope_counts = Counter(row["scope"] for row in rows)
    adapter_steps = [row for row in rows if row["kind"] == "adapter"]
    adapters_with_packaged_outputs = [
        row for row in adapter_steps if row["output_artifacts"] and all(item["exists"] for item in row["output_artifacts"])
    ]
    status = "PASS" if not missing_inputs and not runtime_outputs else "PASS_WITH_GAPS"
    return {
        "report_version": "scbs55_replay_payload_gap_report_v1",
        "status": status,
        "oneclick": rel(ONECLICK),
        "step_count": len(rows),
        "by_kind": dict(sorted(kind_counts.items())),
        "by_scope": dict(sorted(scope_counts.items())),
        "adapter_step_count": len(adapter_steps),
        "adapters_with_packaged_outputs": len(adapters_with_packaged_outputs),
        "required_missing_input_count": len(missing_inputs),
        "runtime_output_count": len(runtime_outputs),
        "missing_required_inputs": missing_inputs,
        "runtime_outputs_not_currently_packaged": runtime_outputs[:200],
        "steps": rows,
        "decision": "gap report is informational until a release package is fetched; release-package verification remains the blocking gate",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    kind_lines = "\n".join(f"- `{key}`: `{value}`" for key, value in payload["by_kind"].items())
    scope_lines = "\n".join(f"- `{key}`: `{value}`" for key, value in payload["by_scope"].items())
    missing_lines = "\n".join(
        f"- `{row['step']}` `{row['path']}`" for row in payload["missing_required_inputs"][:80]
    ) or "- none"
    runtime_lines = "\n".join(
        f"- `{row['step']}` `{row['path']}`" for row in payload["runtime_outputs_not_currently_packaged"][:80]
    ) or "- none"
    return f"""# SCBS55 Replay Payload Gap Report v1

Status: `{payload["status"]}`

## Summary

- oneclick: `{payload["oneclick"]}`
- steps: `{payload["step_count"]}`
- adapter steps: `{payload["adapter_step_count"]}`
- adapters with packaged outputs: `{payload["adapters_with_packaged_outputs"]}`
- required missing inputs: `{payload["required_missing_input_count"]}`
- runtime outputs not currently packaged: `{payload["runtime_output_count"]}`

## Step Kinds

{kind_lines}

## Step Scope

{scope_lines}

## Missing Required Inputs

{missing_lines}

## Runtime Output Promotion Backlog

{runtime_lines}

## Decision

`{payload["decision"]}`
"""


def main() -> int:
    payload = build_report()
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    print(
        "SCBS55_REPLAY_PAYLOAD_GAP_REPORT="
        + json.dumps(
            {
                "status": payload["status"],
                "steps": payload["step_count"],
                "adapter_steps": payload["adapter_step_count"],
                "adapters_with_packaged_outputs": payload["adapters_with_packaged_outputs"],
                "required_missing_inputs": payload["required_missing_input_count"],
                "runtime_outputs": payload["runtime_output_count"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
