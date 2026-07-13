#!/usr/bin/env bash
set -euo pipefail

: "${GITEE_ACCESS_TOKEN:?GITEE_ACCESS_TOKEN is required}"

REPO_NAME="${GITEE_REPO_NAME:-sce-backend-odoo}"
REPO_PATH="${GITEE_REPO_PATH:-${REPO_NAME}}"
REPO_DESCRIPTION="${GITEE_REPO_DESCRIPTION:-Domestic CI mirror for Leedefend/sce-backend-odoo}"
REPO_PRIVATE="${GITEE_REPO_PRIVATE:-true}"
GITEE_API_BASE="${GITEE_API_BASE:-https://gitee.com/api/v5}"

api_post() {
  local url="$1"
  local response_file status
  response_file="$(mktemp)"
  status="$(
    curl -sS -o "${response_file}" -w '%{http_code}' \
      -X POST "${url}" \
      -d "access_token=${GITEE_ACCESS_TOKEN}" \
      -d "name=${REPO_NAME}" \
      -d "path=${REPO_PATH}" \
      -d "description=${REPO_DESCRIPTION}" \
      -d "private=${REPO_PRIVATE}" \
      -d "has_issues=false" \
      -d "has_wiki=false"
  )"

  if [ "${status}" = "201" ]; then
    sed -n '1,120p' "${response_file}"
    rm -f "${response_file}"
    return 0
  fi

  echo "Gitee repository create failed: http_status=${status}" >&2
  sed -n '1,120p' "${response_file}" >&2
  rm -f "${response_file}"
  return 1
}

if [ -n "${GITEE_ORG:-}" ]; then
  api_post "${GITEE_API_BASE}/orgs/${GITEE_ORG}/repos"
else
  api_post "${GITEE_API_BASE}/user/repos"
fi
