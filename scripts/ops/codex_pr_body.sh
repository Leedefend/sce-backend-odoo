#!/usr/bin/env bash
set -euo pipefail

out_file="${1:-}"
evidence_dir="${2:-}"

if [[ -z "${out_file}" || -z "${evidence_dir}" ]]; then
  echo "usage: codex_pr_body.sh <out_file> <evidence_dir>" >&2
  exit 2
fi

branch="$(git rev-parse --abbrev-ref HEAD)"
head_sha="$(git rev-parse --short HEAD)"
base_branch="main"

if git show-ref --verify --quiet "refs/remotes/origin/main"; then
  base_branch="origin/main"
fi

changed_files="$(git diff --name-only "${base_branch}...HEAD" || true)"
file_count="$(echo "${changed_files}" | sed '/^$/d' | wc -l | tr -d ' ')"

upgrade_needed="no"
if echo "${changed_files}" | grep -E -q '^addons/.*/(views|security|data)/|^addons/.*/ir\.model\.access\.csv$'; then
  upgrade_needed="yes"
fi

latest_dir="$(ls -1dt "${evidence_dir}"/* 2>/dev/null | head -n 1 || true)"

{
  echo "## Summary"
  echo "- branch: ${branch}"
  echo "- head: ${head_sha}"
  echo "- changed files: ${file_count}"
  echo "- upgrade needed: ${upgrade_needed}"
  echo
  echo "## Evidence"
  if [[ -n "${latest_dir}" ]]; then
    echo "- latest artifacts: ${latest_dir}"
  else
    echo "- artifacts: ${evidence_dir}"
  fi
  echo
  echo "## Changes"
  if [[ -n "${changed_files}" ]]; then
    echo '```'
    echo "${changed_files}"
    echo '```'
  else
    echo "_no file diff detected_"
  fi
} > "${out_file}"
