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

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "❌ remote 'origin' not configured" >&2
  exit 2
fi

if git ls-remote --exit-code --heads origin "$branch" >/dev/null 2>&1; then
  echo "[pr.push] pushing to origin/${branch}"
  git push origin "$branch"
else
  echo "[pr.push] pushing new branch to origin/${branch}"
  git push -u origin "$branch"
fi
