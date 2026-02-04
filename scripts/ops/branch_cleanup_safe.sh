#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

branch="${1:-}"
if [[ -z "$branch" ]]; then
  echo "❌ CLEAN_BRANCH is required" >&2
  exit 2
fi
if [[ "$branch" == "HEAD" ]]; then
  echo "❌ detached HEAD; refusing cleanup" >&2
  exit 2
fi
if ! [[ "$branch" =~ ^(codex|feat|feature|experiment)/ ]]; then
  echo "❌ only codex/*, feat/*, feature/*, experiment/* can be deleted (current=${branch})" >&2
  exit 2
fi
if [[ "$branch" =~ ^(main|master|release/) ]]; then
  echo "❌ refusing to delete protected branch ${branch}" >&2
  exit 2
fi

if ! git show-ref --verify --quiet "refs/heads/${branch}"; then
  echo "❌ local branch not found: ${branch}" >&2
  exit 2
fi

current="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$current" == "$branch" ]]; then
  echo "❌ cannot delete currently checked-out branch (${branch})" >&2
  exit 2
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "❌ remote 'origin' not configured" >&2
  exit 2
fi

echo "[branch.cleanup.feature] checking merged into main: ${branch}"
git fetch origin main >/dev/null 2>&1 || true
branch_sha="$(git rev-parse "${branch}")"
main_sha="$(git rev-parse origin/main 2>/dev/null || git rev-parse main)"
if git merge-base --is-ancestor "$branch_sha" "$main_sha"; then
  echo "[branch.cleanup.feature] merge-base check: ok"
else
  if ! command -v gh >/dev/null 2>&1; then
    echo "❌ gh not found; cannot verify merged PR for ${branch}" >&2
    exit 2
  fi
  pr_count="$(gh pr list --state merged --search "head:${branch}" --json number --jq 'length')" || \
    (echo "❌ gh pr list failed; network/auth required to verify merge for ${branch}" >&2; exit 2)
  if [[ "$pr_count" -lt 1 ]]; then
    echo "❌ branch not merged into main yet: ${branch}" >&2
    exit 2
  fi
  echo "[branch.cleanup.feature] merged PR detected for ${branch}"
fi

echo "[branch.cleanup.feature] deleting local: ${branch}"
git branch -d "${branch}"

echo "[branch.cleanup.feature] deleting remote: ${branch}"
git push origin --delete "${branch}"

echo "✅ [branch.cleanup.feature] done"
