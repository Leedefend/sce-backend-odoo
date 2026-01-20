#!/usr/bin/env bash
set -euo pipefail

REPORT_OUT="${REPORT_OUT:-${1:-}}"
SUMMARY_FILE="${SUMMARY_FILE:-${2:-}}"
STAGE_NAME="${STAGE:-unknown}"
STAGE_STATUS="${STAGE_STATUS:-FAIL}"
REPORT_JSON="${REPORT_JSON:-}"

if [[ -z "$REPORT_OUT" || -z "$SUMMARY_FILE" ]]; then
  echo "FAIL: REPORT_OUT and SUMMARY_FILE are required"
  exit 2
fi

branch="$(git rev-parse --abbrev-ref HEAD)"
sha="$(git rev-parse --short HEAD)"
status="$(git status --porcelain)"

{
  echo "# Stage Execution Report"
  echo
  echo "## Stage / Branch / SHA"
  echo "- stage: ${STAGE_NAME}"
  echo "- branch: ${branch}"
  echo "- sha: ${sha}"
  echo "- result: ${STAGE_STATUS}"
  echo
  echo "## Commands + Evidence Markers"
  while IFS='|' read -r idx cmd markers cmd_status; do
    echo "- cmd${idx}: ${cmd}"
    echo "  - markers: ${markers}"
    echo "  - status: ${cmd_status}"
  done < "${SUMMARY_FILE}"
  echo
  echo "## git status --porcelain"
  if [[ -z "$status" ]]; then
    echo "(clean)"
  else
    echo "$status"
  fi
} > "${REPORT_OUT}"

if [[ -z "$REPORT_JSON" ]]; then
  if [[ "$REPORT_OUT" == *.md ]]; then
    REPORT_JSON="${REPORT_OUT%.md}.json"
  else
    REPORT_JSON="${REPORT_OUT}.json"
  fi
fi

generated_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
python3 - "$SUMMARY_FILE" "$REPORT_JSON" "$STAGE_NAME" "$STAGE_STATUS" "$branch" "$sha" "$status" "$generated_at" <<'PY'
import json
import sys

summary_file, report_json, stage, stage_status, branch, sha, git_status, generated_at = sys.argv[1:]
commands = []
with open(summary_file, "r", encoding="utf-8") as f:
    for raw in f:
        line = raw.rstrip("\n")
        if not line:
            continue
        idx, cmd, markers, cmd_status = line.split("|", 3)
        markers_list = []
        if markers and markers != "(none)":
            markers_list = [m for m in markers.split(";") if m]
        commands.append(
            {
                "index": int(idx),
                "command": cmd,
                "markers": markers_list,
                "status": cmd_status,
            }
        )

data = {
    "stage": stage,
    "branch": branch,
    "sha": sha,
    "result": stage_status,
    "generated_at": generated_at,
    "commands": commands,
    "git_status": git_status.splitlines() if git_status else [],
}

with open(report_json, "w", encoding="utf-8") as out:
    json.dump(data, out, ensure_ascii=True, indent=2)
    out.write("\n")
PY

python3 -m json.tool "$REPORT_JSON" >/dev/null

reports_dir="$(dirname "$REPORT_OUT")"
if [[ "$(basename "$reports_dir")" == "stage_reports" ]]; then
  readme="${reports_dir}/README.md"
  report_file="$(basename "$REPORT_OUT")"
  if [[ ! -f "$readme" ]]; then
    {
      echo "# Stage Reports"
      echo
      echo "Auto-generated index of stage execution reports."
      echo
    } > "$readme"
  fi
  echo "- ${report_file} | stage=${STAGE_NAME} | result=${STAGE_STATUS}" >> "$readme"
fi
