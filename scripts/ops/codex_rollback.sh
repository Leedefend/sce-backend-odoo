#!/usr/bin/env bash
set -euo pipefail

branch="$(git rev-parse --abbrev-ref HEAD)"
ts="$(date +%Y%m%d-%H%M%S)"
base_dir="artifacts/codex/${branch}/${ts}/rollback"
mkdir -p "${base_dir}"

log_file="${base_dir}/rollback.log"
exec > >(tee -a "${log_file}") 2>&1

orig_branch="${ORIG_BRANCH:-}"
if [[ -z "${orig_branch}" ]]; then
  latest_origin="$(find artifacts/codex -name orig_branch.txt -type f 2>/dev/null | sort | tail -n 1 || true)"
  if [[ -n "${latest_origin}" ]]; then
    orig_branch="$(cat "${latest_origin}" | head -n 1)"
  fi
fi

echo "[codex.rollback] current=${branch} orig=${orig_branch:-unknown}"

git merge --abort || true
git restore --staged . || true
git restore . || true

if [[ "${branch}" == "main" && -n "${orig_branch}" ]]; then
  git checkout "${orig_branch}" || true
fi

echo "[codex.rollback] done"
