#!/usr/bin/env bash
set -euo pipefail

flow="${FLOW:-}"
if [[ -z "$flow" ]]; then
  echo "FLOW is required (fast|snapshot|gate)" >&2
  exit 2
fi

branch="$(git rev-parse --abbrev-ref HEAD)"
ts="$(date +%Y%m%d-%H%M%S)"
base_dir="artifacts/codex/${branch}/${ts}"

mkdir -p "${base_dir}/fast" "${base_dir}/snapshot" "${base_dir}/gate"

env_file="${base_dir}/env.md"
{
  echo "branch: ${branch}"
  echo "timestamp: ${ts}"
  echo "host: $(hostname)"
  echo "user: $(whoami)"
  echo "pwd: ${PWD}"
  if command -v docker >/dev/null 2>&1; then
    echo "docker: $(docker --version)"
  fi
  if command -v codex >/dev/null 2>&1; then
    echo "codex: $(codex --version 2>/dev/null || echo unknown)"
  fi
} > "${env_file}"

log_dir="${base_dir}/${flow}"
log_file="${log_dir}/run.log"
status="PASS"
command=""

case "$flow" in
  fast)
    command="make codex.fast"
    if ! make codex.fast >"${log_file}" 2>&1; then
      status="FAIL"
    fi
    ;;
  snapshot)
    command="make codex.snapshot (x2 for stability)"
    if ! make codex.snapshot >"${log_file}" 2>&1; then
      status="FAIL"
    fi
    find docs/contract/snapshots -type f -name "*.json" -print0 | sort -z | xargs -0 sha256sum > "${log_dir}/snapshot_hashes_1.txt"
    if ! make codex.snapshot >>"${log_file}" 2>&1; then
      status="FAIL"
    fi
    find docs/contract/snapshots -type f -name "*.json" -print0 | sort -z | xargs -0 sha256sum > "${log_dir}/snapshot_hashes_2.txt"
    if ! diff -u "${log_dir}/snapshot_hashes_1.txt" "${log_dir}/snapshot_hashes_2.txt" > "${log_dir}/snapshot_hashes_diff.txt"; then
      status="FAIL"
    fi
    git status --porcelain > "${log_dir}/git_status.txt"
    git diff --stat > "${log_dir}/git_diff_stat.txt"
    ;;
  gate)
    command="make codex.gate"
    if ! make codex.gate >"${log_file}" 2>&1; then
      status="FAIL"
    fi
    ;;
  *)
    echo "unknown FLOW=${flow}" >&2
    exit 2
    ;;
esac

summary="${base_dir}/summary.md"
{
  echo "command: ${command}"
  echo "flow: ${flow}"
  echo "status: ${status}"
  echo "log: ${log_file}"
  echo "env: ${env_file}"
} >> "${summary}"

if [[ "${status}" != "PASS" ]]; then
  exit 1
fi
