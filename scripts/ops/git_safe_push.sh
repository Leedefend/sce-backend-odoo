#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$branch" == "HEAD" ]]; then
  echo "❌ detached HEAD; checkout a branch before pushing" >&2
  exit 2
fi
if [[ "$branch" == "main" || "$branch" == "master" || "$branch" == "release" || "$branch" == release/* || "$branch" == "prod" || "$branch" == prod/* ]]; then
  echo "❌ push forbidden on main/master/release/prod branches (current=${branch})" >&2
  exit 2
fi
if ! git check-ref-format --branch "$branch" >/dev/null 2>&1; then
  echo "❌ invalid local branch name (current=${branch})" >&2
  exit 2
fi
if ! [[ "$branch" =~ ^(codex|feat|feature|fix|experiment)/ ]]; then
  echo "❌ push only allowed on codex/*, feat/*, feature/*, fix/*, experiment/* (current=${branch})" >&2
  exit 2
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "❌ working tree dirty; commit or stash before push" >&2
  exit 2
fi

for remote in origin gitee; do
  if ! git remote get-url "$remote" >/dev/null 2>&1; then
    echo "❌ required remote '${remote}' not configured" >&2
    exit 2
  fi
done

declare -A branch_exists
for remote in origin gitee; do
  echo "[pr.push] preflight remote=${remote}"
  if ! git ls-remote "$remote" >/dev/null 2>&1; then
    echo "❌ preflight_failed: remote '${remote}' is not accessible; no push attempted" >&2
    exit 3
  fi
done

for remote in origin gitee; do
  if git ls-remote --exit-code --heads "$remote" "refs/heads/${branch}" >/dev/null 2>&1; then
    branch_exists["$remote"]=1
  else
    branch_exists["$remote"]=0
  fi
done

echo "[pr.push] preflight complete; remotes=origin,gitee branch=${branch} worktree=clean"

if [[ "${branch_exists[origin]}" == "1" ]]; then
  echo "[pr.push] pushing to origin/${branch}"
  if ! git push origin "$branch"; then
    echo "❌ sync_failed: successful_remotes=none failed_remote=origin" >&2
    echo "recovery_command: make pr.push" >&2
    exit 4
  fi
else
  echo "[pr.push] pushing new branch to origin/${branch}"
  if ! git push -u origin "$branch"; then
    echo "❌ sync_failed: successful_remotes=none failed_remote=origin" >&2
    echo "recovery_command: make pr.push" >&2
    exit 4
  fi
fi

if [[ "${branch_exists[gitee]}" == "1" ]]; then
  echo "[pr.push] pushing to gitee/${branch}"
else
  echo "[pr.push] pushing new branch to gitee/${branch}"
fi
if ! git push gitee "$branch"; then
  echo "❌ partial_sync: successful_remotes=origin failed_remote=gitee" >&2
  echo "recovery_command: make pr.push" >&2
  exit 5
fi

echo "[pr.push] sync complete; successful_remotes=origin,gitee branch=${branch}"
