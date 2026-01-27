#!/usr/bin/env bash
set -euo pipefail

branch="$(git rev-parse --abbrev-ref HEAD)"
if ! echo "$branch" | grep -qE '^codex/'; then
  echo "codex.merge only allowed on codex/* branches (current=$branch)" >&2
  exit 2
fi

ts="$(date +%Y%m%d-%H%M%S)"
base_dir="artifacts/codex/${branch}/${ts}/merge"
mkdir -p "${base_dir}"

log_file="${base_dir}/merge.log"
exec > >(tee -a "${log_file}") 2>&1

echo "[codex.merge] branch=${branch}"
echo "${branch}" > "${base_dir}/orig_branch.txt"

echo "[codex.merge] snapshot"
make codex.snapshot

echo "[codex.merge] verify.smart_core"
make verify.smart_core

echo "[codex.merge] gate"
make codex.gate CODEX_MODE=gate

merge_msg="${MERGE_COMMIT_MSG:-merge: codex autonomous delivery (${branch})}"

echo "[codex.merge] sync main"
git checkout main
git pull --ff-only origin main

echo "[codex.merge] squash merge"
git merge --squash "${branch}"
git commit -m "${merge_msg}"

echo "[codex.merge] push main"
git push origin main

echo "[codex.merge] return to branch"
git checkout "${branch}"

echo "[codex.merge] done"
