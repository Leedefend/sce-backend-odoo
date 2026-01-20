#!/usr/bin/env bash
set -euo pipefail

branch="$(git rev-parse --abbrev-ref HEAD)"
sha="$(git rev-parse --short HEAD)"

echo "CODEx PREFLIGHT"
echo "BRANCH: ${branch}"
echo "SHA: ${sha}"

if [[ "$branch" == "main" ]]; then
  echo "FAIL: branch is main"
  exit 1
fi

status="$(git status --porcelain)"
if [[ -z "$status" ]]; then
  echo "OK: working tree clean"
  exit 0
fi

if echo "$status" | awk '{print $2}' | grep -E '^docs/audit/.*\.csv$' >/dev/null 2>&1; then
  echo "FAIL: docs/audit changes detected (restore required)"
  exit 1
fi

echo "FAIL: working tree not clean"
exit 1
