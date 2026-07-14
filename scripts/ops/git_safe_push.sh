#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$branch" == "HEAD" ]]; then
  echo "❌ detached HEAD; checkout a branch before pushing" >&2
  exit 2
fi
if ! [[ "$branch" =~ ^(codex|feat|feature|experiment)/ ]]; then
  echo "❌ push only allowed on codex/*, feat/*, feature/*, experiment/* (current=${branch})" >&2
  exit 2
fi
if [[ "$branch" =~ ^(main|master|release/) ]]; then
  echo "❌ push forbidden on main/master/release/* (current=${branch})" >&2
  exit 2
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "❌ working tree dirty; commit or stash before push" >&2
  exit 2
fi

for remote in origin gitee; do
  if ! git remote get-url "$remote" >/dev/null 2>&1; then
    echo "❌ required remote '${remote}' not configured" >&2
    exit 2
  fi
done

for remote in origin gitee; do
  if git ls-remote --exit-code --heads "$remote" "$branch" >/dev/null 2>&1; then
    echo "[pr.push] pushing to ${remote}/${branch}"
    git push "$remote" "$branch"
  elif [[ "$remote" == "origin" ]]; then
    echo "[pr.push] pushing new branch to ${remote}/${branch}"
    git push -u "$remote" "$branch"
  else
    echo "[pr.push] pushing new branch to ${remote}/${branch}"
    git push "$remote" "$branch"
  fi
done
