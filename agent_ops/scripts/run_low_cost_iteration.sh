#!/usr/bin/env bash
set -euo pipefail

TASK_INPUT="${1:?base task id or task path is required}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

resolve_base_id() {
  local raw="$1"
  local stem
  stem="$(basename "$raw")"
  stem="${stem%.yaml}"
  stem="${stem%-A}"
  stem="${stem%-B}"
  stem="${stem%-C}"
  printf '%s\n' "$stem"
}

run_stage() {
  local stage_id="$1"
  local stage_path="$ROOT_DIR/agent_ops/tasks/${stage_id}.yaml"

  if [ ! -f "$stage_path" ]; then
    printf '{\n'
    printf '  "status": "STOP",\n'
    printf '  "stage": "%s",\n' "$stage_id"
    printf '  "decision": "missing stage task: %s"\n' "$stage_path"
    printf '}\n'
    return 2
  fi

  printf 'Using new session for %s\n' "$stage_id"
  printf 'carry_long_context=false\n'

  if ! python3 "$ROOT_DIR/agent_ops/scripts/validate_task.py" "$stage_path"; then
    printf '{\n'
    printf '  "status": "FAIL",\n'
    printf '  "stage": "%s",\n' "$stage_id"
    printf '  "decision": "task validation failed"\n'
    printf '}\n'
    return 1
  fi

  printf '{\n'
  printf '  "status": "PASS",\n'
  printf '  "stage": "%s",\n' "$stage_id"
  printf '  "decision": "stage gate passed"\n'
  printf '}\n'
}

BASE_ID="$(resolve_base_id "$TASK_INPUT")"

run_stage "${BASE_ID}-A"
run_stage "${BASE_ID}-B"
if ! run_stage "${BASE_ID}-C"; then
  exit 1
fi

printf '{\n'
printf '  "status": "PASS",\n'
printf '  "task_id": "%s",\n' "$BASE_ID"
printf '  "next_suggestion": "Start the next low-cost batch from a new session using the generated stage tasks."\n'
printf '}\n'
