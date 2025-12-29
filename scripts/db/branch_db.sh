#!/usr/bin/env bash
set -euo pipefail

BRANCH="${1:-}"
if [[ -z "${BRANCH}" ]]; then
  BRANCH="$(git rev-parse --abbrev-ref HEAD)"
fi

# slug: lower + replace / - with _
SLUG="$(echo "${BRANCH}" | tr '[:upper:]' '[:lower:]' | sed 's#[/-]#_#g' | sed 's/[^a-z0-9_]/_/g')"
# 截断避免过长
SLUG="${SLUG:0:40}"

echo "sc_dev__${SLUG}"
