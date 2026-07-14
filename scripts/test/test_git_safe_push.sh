#!/usr/bin/env bash
set -uo pipefail

SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET="$ROOT_DIR/scripts/ops/git_safe_push.sh"

contains_word() {
  local words=" ${1:-} "
  local needle="$2"
  [[ "$words" == *" $needle "* ]]
}

fake_git() {
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
        printf '%s\n' ' M tracked-file'
      fi
      ;;
    remote)
      local remote="${3:-}"
      if contains_word "${FAKE_MISSING_REMOTES:-}" "$remote"; then
        return 2
      fi
      printf 'fake://%s\n' "$remote"
      ;;
    ls-remote)
      local remote
      if [[ "${2:-}" == "--exit-code" ]]; then
        remote="${4:-}"
        if contains_word "${FAKE_INACCESSIBLE_REMOTES:-}" "$remote"; then
          return 128
        fi
        contains_word "${FAKE_EXISTING_REMOTES:-origin gitee}" "$remote"
      else
        remote="${2:-}"
        ! contains_word "${FAKE_INACCESSIBLE_REMOTES:-}" "$remote"
      fi
      ;;
    push)
      local remote
      if [[ "${2:-}" == "-u" ]]; then
        remote="${3:-}"
      else
        remote="${2:-}"
      fi
      ! contains_word "${FAKE_PUSH_FAIL_REMOTES:-}" "$remote"
      ;;
    *)
      printf 'unexpected fake git invocation: %s\n' "$*" >&2
      return 99
      ;;
  esac
}

if [[ "$(basename "$0")" == "git" ]]; then
  fake_git "$@"
  exit $?
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
mkdir -p "$tmp_dir/bin"
ln -s "$SELF" "$tmp_dir/bin/git"
log_file="$tmp_dir/git.log"

output=''
status=0

run_push() {
  : >"$log_file"
  output="$(
    PATH="$tmp_dir/bin:$PATH" \
      FAKE_GIT_LOG="$log_file" \
      FAKE_BRANCH="${FAKE_BRANCH:-fix/test-branch}" \
      FAKE_MISSING_REMOTES="${FAKE_MISSING_REMOTES:-}" \
      FAKE_INACCESSIBLE_REMOTES="${FAKE_INACCESSIBLE_REMOTES:-}" \
      FAKE_EXISTING_REMOTES="${FAKE_EXISTING_REMOTES:-origin gitee}" \
      FAKE_PUSH_FAIL_REMOTES="${FAKE_PUSH_FAIL_REMOTES:-}" \
      FAKE_DIRTY="${FAKE_DIRTY:-0}" \
      FAKE_INVALID_BRANCH="${FAKE_INVALID_BRANCH:-0}" \
      bash "$TARGET" 2>&1
  )"
  status=$?
}

fail() {
  printf 'FAIL: %s\noutput:\n%s\nlog:\n' "$1" "$output" >&2
  sed -n '1,120p' "$log_file" >&2
  exit 1
}

assert_nonzero() {
  [[ "$status" -ne 0 ]] || fail "$1: expected nonzero status"
}

assert_zero() {
  [[ "$status" -eq 0 ]] || fail "$1: expected status 0, got $status"
}

assert_output() {
  [[ "$output" == *"$2"* ]] || fail "$1: missing output '$2'"
}

assert_push_count() {
  local count
  count="$(awk '$1 == "push" { count++ } END { print count + 0 }' "$log_file")"
  [[ "$count" -eq "$2" ]] || fail "$1: expected $2 push calls, got $count"
}

FAKE_MISSING_REMOTES=origin run_push
assert_nonzero 'missing origin'
assert_output 'missing origin' "required remote 'origin' not configured"
assert_push_count 'missing origin' 0

FAKE_MISSING_REMOTES=gitee run_push
assert_nonzero 'missing gitee'
assert_output 'missing gitee' "required remote 'gitee' not configured"
assert_push_count 'missing gitee' 0

FAKE_INACCESSIBLE_REMOTES=origin run_push
assert_nonzero 'origin inaccessible'
assert_output 'origin inaccessible' "remote 'origin' is not accessible"
assert_push_count 'origin inaccessible' 0

FAKE_INACCESSIBLE_REMOTES=gitee run_push
assert_nonzero 'gitee inaccessible'
assert_output 'gitee inaccessible' "remote 'gitee' is not accessible"
assert_push_count 'gitee inaccessible' 0

FAKE_EXISTING_REMOTES='origin gitee' run_push
assert_zero 'existing branches'
assert_push_count 'existing branches' 2
grep -q '^push origin fix/test-branch$' "$log_file" || fail 'existing branches: origin update push missing'
grep -q '^push gitee fix/test-branch$' "$log_file" || fail 'existing branches: gitee update push missing'

FAKE_EXISTING_REMOTES=none run_push
assert_zero 'new branches'
assert_push_count 'new branches' 2
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
assert_nonzero 'dirty worktree'
assert_output 'dirty worktree' 'working tree dirty'
assert_push_count 'dirty worktree' 0

FAKE_INVALID_BRANCH=1 run_push
assert_nonzero 'invalid branch name'
assert_output 'invalid branch name' 'invalid local branch name'
assert_push_count 'invalid branch name' 0

printf 'PASS: git_safe_push isolated scenarios=11 (no real remotes)\n'
