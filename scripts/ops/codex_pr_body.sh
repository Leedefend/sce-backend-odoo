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
architecture_impact="${PR_ARCHITECTURE_IMPACT:-Repository-level change; review the generated file summary and validation evidence.}"
layer_target="${PR_LAYER_TARGET:-Not provided by the caller.}"
affected_modules="${PR_AFFECTED_MODULES:-$(
  printf '%s\n' "${changed_files}" \
    | sed -n 's#^\(addons/[^/]*\)/.*#\1#p' \
    | sort -u \
    | head -n 20 \
    | paste -sd ',' - \
    | sed 's/,/, /g'
)}"
affected_modules="${affected_modules:-repository tooling/config/docs}"
change_sample_limit=100
change_sample="$(
  printf '%s\n' "${changed_files}" \
    | sed '/^$/d' \
    | awk -v limit="${change_sample_limit}" '
        NR <= limit {
          if (length($0) > 300) {
            print substr($0, 1, 297) "..."
          } else {
            print
          }
        }
      '
)"

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
  echo "## Architecture Impact"
  echo "${architecture_impact}"
  echo
  echo "## Layer Target"
  echo "${layer_target}"
  echo
  echo "## Affected Modules"
  echo "${affected_modules}"
  echo
  echo "## Evidence"
  if [[ -n "${latest_dir}" ]]; then
    echo "- latest artifacts: ${latest_dir}"
  else
    echo "- artifacts: ${evidence_dir}"
  fi
  echo
  echo "## Changes"
  if [[ -n "${change_sample}" ]]; then
    echo '```'
    echo "${change_sample}"
    echo '```'
    if (( file_count > change_sample_limit )); then
      echo
      echo "_showing first ${change_sample_limit} files; $((file_count - change_sample_limit)) additional files omitted_"
    fi
  else
    echo "_no file diff detected_"
  fi
} > "${out_file}"
