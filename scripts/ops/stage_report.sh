#!/usr/bin/env bash
set -euo pipefail

REPORT_OUT="${REPORT_OUT:-${1:-}}"
SUMMARY_FILE="${SUMMARY_FILE:-${2:-}}"
STAGE_NAME="${STAGE:-unknown}"
STAGE_STATUS="${STAGE_STATUS:-FAIL}"

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
