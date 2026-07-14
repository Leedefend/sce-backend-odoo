#!/usr/bin/env bash
set -euo pipefail

contains_word() {
  local words=" ${1:-} "
  local needle="$2"
  [[ "$words" == *" $needle "* ]]
}

if [[ "${GIT_SAFE_PUSH_FAKE_GIT:-0}" == "1" && "$(basename "$0")" == "git" ]]; then
  printf '%s\n' "$*" >>"${FAKE_GIT_LOG:?}"
  case "${1:-}" in
    rev-parse)
      printf '%s\n' "${FAKE_BRANCH:-fix/test-branch}"
      ;;
    check-ref-format)
      [[ "${FAKE_INVALID_BRANCH:-0}" != "1" ]]
      ;;
    status)
      if [[ "${FAKE_DIRTY:-0}" == "1" ]]; then
        printf '%s\n' '?? generated-file'
      fi
      ;;
    remote)
      remote="${3:-}"
      if contains_word "${FAKE_MISSING_REMOTES:-}" "$remote"; then
        exit 2
      fi
      printf 'fake://%s\n' "$remote"
      ;;
    ls-remote)
      if [[ "${2:-}" == "--exit-code" ]]; then
        remote="${4:-}"
        if contains_word "${FAKE_INACCESSIBLE_REMOTES:-}" "$remote"; then
          exit 128
        fi
        contains_word "${FAKE_EXISTING_REMOTES:-origin gitee}" "$remote"
      else
        remote="${2:-}"
        ! contains_word "${FAKE_INACCESSIBLE_REMOTES:-}" "$remote"
      fi
      ;;
    push)
      if [[ "${2:-}" == "-u" ]]; then
        remote="${3:-}"
      else
        remote="${2:-}"
      fi
      ! contains_word "${FAKE_PUSH_FAIL_REMOTES:-}" "$remote"
      ;;
    *)
      printf 'unexpected fake git invocation: %s\n' "$*" >&2
      exit 99
      ;;
  esac
  exit $?
fi

if [[ "${1:-}" == "--self-test" ]]; then
  self="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT
  mkdir -p "$tmp_dir/bin"
  ln -s "$self" "$tmp_dir/bin/git"
  log_file="$tmp_dir/git.log"
  output=''
  status=0

  run_push() {
    : >"$log_file"
    set +e
    output="$(
      PATH="$tmp_dir/bin:$PATH" \
        GIT_SAFE_PUSH_FAKE_GIT=1 \
        FAKE_GIT_LOG="$log_file" \
        FAKE_BRANCH="${FAKE_BRANCH:-fix/test-branch}" \
        FAKE_MISSING_REMOTES="${FAKE_MISSING_REMOTES:-}" \
        FAKE_INACCESSIBLE_REMOTES="${FAKE_INACCESSIBLE_REMOTES:-}" \
        FAKE_EXISTING_REMOTES="${FAKE_EXISTING_REMOTES:-origin gitee}" \
        FAKE_PUSH_FAIL_REMOTES="${FAKE_PUSH_FAIL_REMOTES:-}" \
        FAKE_DIRTY="${FAKE_DIRTY:-0}" \
        FAKE_INVALID_BRANCH="${FAKE_INVALID_BRANCH:-0}" \
        bash "$self" 2>&1
    )"
    status=$?
    set -e
  }

  fail() {
    printf 'FAIL: %s\noutput:\n%s\nlog:\n' "$1" "$output" >&2
    sed -n '1,120p' "$log_file" >&2
    exit 1
  }
  assert_nonzero() { [[ "$status" -ne 0 ]] || fail "$1: expected nonzero status"; }
  assert_zero() { [[ "$status" -eq 0 ]] || fail "$1: expected status 0, got $status"; }
  assert_output() { [[ "$output" == *"$2"* ]] || fail "$1: missing output '$2'"; }
  assert_push_count() {
    count="$(awk '$1 == "push" { count++ } END { print count + 0 }' "$log_file")"
    [[ "$count" -eq "$2" ]] || fail "$1: expected $2 push calls, got $count"
  }

  FAKE_MISSING_REMOTES=origin run_push
  assert_nonzero 'missing origin'; assert_output 'missing origin' "required remote 'origin' not configured"; assert_push_count 'missing origin' 0
  FAKE_MISSING_REMOTES=gitee run_push
  assert_nonzero 'missing gitee'; assert_output 'missing gitee' "required remote 'gitee' not configured"; assert_push_count 'missing gitee' 0
  FAKE_INACCESSIBLE_REMOTES=origin run_push
  assert_nonzero 'origin inaccessible'; assert_output 'origin inaccessible' "remote 'origin' is not accessible"; assert_push_count 'origin inaccessible' 0
  FAKE_INACCESSIBLE_REMOTES=gitee run_push
  assert_nonzero 'gitee inaccessible'; assert_output 'gitee inaccessible' "remote 'gitee' is not accessible"; assert_push_count 'gitee inaccessible' 0

  FAKE_EXISTING_REMOTES='origin gitee' run_push
  assert_zero 'existing branches'; assert_push_count 'existing branches' 2
  grep -q '^push origin fix/test-branch$' "$log_file" || fail 'existing branches: origin update push missing'
  grep -q '^push gitee fix/test-branch$' "$log_file" || fail 'existing branches: gitee update push missing'

  FAKE_EXISTING_REMOTES=none run_push
  assert_zero 'new branches'; assert_push_count 'new branches' 2
  grep -q '^push -u origin fix/test-branch$' "$log_file" || fail 'new branches: origin tracking push missing'
  grep -q '^push gitee fix/test-branch$' "$log_file" || fail 'new branches: gitee push missing'

  FAKE_PUSH_FAIL_REMOTES=gitee run_push
  assert_nonzero 'gitee write failure'
  assert_output 'gitee write failure' 'partial_sync: successful_remotes=origin failed_remote=gitee'
  assert_output 'gitee write failure' 'recovery_command: make pr.push'
  assert_push_count 'gitee write failure' 2

  for protected_branch in main release release/1.0 prod prod/production; do
    FAKE_BRANCH="$protected_branch" run_push
    assert_nonzero "protected branch $protected_branch"
    assert_output "protected branch $protected_branch" 'push forbidden on main/master/release/prod branches'
    assert_push_count "protected branch $protected_branch" 0
  done

  FAKE_DIRTY=1 run_push
  assert_nonzero 'dirty worktree'; assert_output 'dirty worktree' 'working tree dirty'; assert_push_count 'dirty worktree' 0
  grep -q '^status --porcelain --untracked-files=all$' "$log_file" || fail 'dirty worktree: explicit untracked-file scan missing'
  FAKE_INVALID_BRANCH=1 run_push
  assert_nonzero 'invalid branch name'; assert_output 'invalid branch name' 'invalid local branch name'; assert_push_count 'invalid branch name' 0

  printf 'PASS: git_safe_push isolated scenarios=11 (no real remotes)\n'
  exit 0
fi

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

if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
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
