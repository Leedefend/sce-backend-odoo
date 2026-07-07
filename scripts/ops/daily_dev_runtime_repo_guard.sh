#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$repo_root" ]]; then
  echo "[daily_dev_runtime_repo_guard] FAIL: not inside a git repository" >&2
  exit 2
fi

cd "$repo_root"

expected_branch="${DAILY_DEV_RUNTIME_BRANCH:-main}"
max_allowed_stashes="${DAILY_DEV_RUNTIME_MAX_STASHES:-0}"
forbidden_refs_pattern="${DAILY_DEV_RUNTIME_FORBIDDEN_REF_PATTERN:-refs/remotes/localpush/|refs/heads/archive/daily-dev-}"

errors=()

branch="$(git branch --show-current)"
if [[ "$branch" != "$expected_branch" ]]; then
  errors+=("expected branch '$expected_branch', got '$branch'")
fi

if [[ -n "$(git status --porcelain)" ]]; then
  errors+=("working tree is not clean")
fi

if git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' >/dev/null 2>&1; then
  ahead_behind="$(git rev-list --left-right --count 'HEAD...@{upstream}')"
  if [[ "$ahead_behind" != "0	0" ]]; then
    errors+=("branch is not aligned with upstream: $ahead_behind")
  fi
else
  errors+=("branch has no upstream")
fi

stash_count="$(git stash list | wc -l | tr -d ' ')"
if (( stash_count > max_allowed_stashes )); then
  errors+=("stash count $stash_count exceeds allowed $max_allowed_stashes")
fi

if git show-ref | grep -Eq "$forbidden_refs_pattern"; then
  errors+=("forbidden temporary/archive refs are present")
fi

for path in artifacts migration_assets tmp; do
  if [[ -d "$path" ]] && git status --porcelain -- "$path" | grep -q .; then
    errors+=("runtime repo contains uncommitted generated data under $path")
  fi
done

if (( ${#errors[@]} > 0 )); then
  echo "[daily_dev_runtime_repo_guard] FAIL"
  for error in "${errors[@]}"; do
    echo "- $error"
  done
  exit 1
fi

echo "[daily_dev_runtime_repo_guard] PASS branch=$branch head=$(git rev-parse --short HEAD)"
