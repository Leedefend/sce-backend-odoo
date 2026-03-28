#!/usr/bin/env bash
set -euo pipefail

TASK_PATH="${1:?task path is required}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOCK_PATH="$ROOT_DIR/agent_ops/state/run_iteration.lock"

mkdir -p "$(dirname "$LOCK_PATH")"
exec 9>"$LOCK_PATH"
if command -v flock >/dev/null 2>&1; then
  flock 9
fi

validate_output="$(python3 "$ROOT_DIR/agent_ops/scripts/validate_task.py" "$TASK_PATH")"
printf '%s\n' "$validate_output"

verify_json="$(python3 - "$ROOT_DIR" "$TASK_PATH" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

import yaml

root = Path(sys.argv[1])
task_path = Path(sys.argv[2])
if not task_path.is_absolute():
    task_path = root / task_path

with task_path.open("r", encoding="utf-8") as handle:
    task = yaml.safe_load(handle)

results = []
passed = True
for command in task.get("acceptance", {}).get("commands", []):
    completed = subprocess.run(
        command,
        shell=True,
        cwd=str(root),
        text=True,
        capture_output=True,
        check=False,
    )
    results.append(
        {
            "command": command,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    )
    if completed.returncode != 0:
        passed = False

print(json.dumps({"passed": passed, "results": results}, ensure_ascii=True))
sys.exit(0)
PY
)"

set +e
risk_output="$(python3 "$ROOT_DIR/agent_ops/scripts/risk_scan.py")"
risk_exit=$?
verify_exit=0
if ! python3 -c 'import json,sys; payload=json.load(sys.stdin); sys.exit(0 if payload["passed"] else 1)' <<<"$verify_json"; then
  verify_exit=1
fi
risk_stop=0
if ! python3 -c 'import json,sys; payload=json.load(sys.stdin); sys.exit(0 if not payload["stop_required"] else 1)' <<<"$risk_output"; then
  risk_stop=1
fi
set -e

python3 - "$ROOT_DIR" "$TASK_PATH" "$validate_output" "$verify_json" "$risk_output" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
task_path = Path(sys.argv[2])
validate_output = json.loads(sys.argv[3])
verify_output = json.loads(sys.argv[4])
risk_output = json.loads(sys.argv[5])

task_id = validate_output.get("task_id")
last_run = {
    "task_id": task_id,
    "task_path": str(task_path),
    "validate": {
        "passed": validate_output.get("status") == "PASS",
        "errors": validate_output.get("errors", []),
    },
    "verify": verify_output,
    "risk_scan": risk_output,
}

state_dir = root / "agent_ops" / "state"
state_dir.mkdir(parents=True, exist_ok=True)
last_run_path = state_dir / "last_run.json"
task_result_path = state_dir / "task_results" / f"{task_id}.json"
for path in (last_run_path, task_result_path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(last_run, handle, ensure_ascii=True, indent=2, sort_keys=True)
        handle.write("\n")
PY

set +e
classify_output="$(python3 "$ROOT_DIR/agent_ops/scripts/classify_result.py" "$TASK_PATH")"
classify_exit=$?
set -e
printf '%s\n' "$classify_output"

python3 - "$ROOT_DIR" "$TASK_PATH" "$classify_output" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
task_path = Path(sys.argv[2])
classification = json.loads(sys.argv[3])
last_run_path = root / "agent_ops" / "state" / "last_run.json"
iteration_cursor_path = root / "agent_ops" / "state" / "iteration_cursor.json"

with last_run_path.open("r", encoding="utf-8") as handle:
    payload = json.load(handle)

payload["classification"] = classification

task_id = payload["task_id"]
for path in (last_run_path, root / "agent_ops" / "state" / "task_results" / f"{task_id}.json"):
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2, sort_keys=True)
        handle.write("\n")

with iteration_cursor_path.open("w", encoding="utf-8") as handle:
    json.dump(
        {
            "last_task_id": task_id,
            "last_classification": classification.get("classification"),
            "triggered_stop_conditions": classification.get("triggered_stop_conditions", []),
            "task_path": str(task_path),
        },
        handle,
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    )
    handle.write("\n")
PY

python3 "$ROOT_DIR/agent_ops/scripts/build_report.py" "$TASK_PATH"

if [ "$risk_stop" -ne 0 ]; then
  printf '%s\n' "STOP: risk triggered"
fi

if [ "$verify_exit" -ne 0 ] || [ "$risk_exit" -ne 0 ] || [ "$classify_exit" -ne 0 ] || [ "$risk_stop" -ne 0 ]; then
  exit 1
fi
