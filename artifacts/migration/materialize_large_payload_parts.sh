#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

materialize() {
  local path="$1"
  local expected_sha="$2"
  local parts_dir="${path}.parts"

  if [ ! -d "$parts_dir" ]; then
    echo "missing parts directory: $parts_dir" >&2
    return 1
  fi

  cat "$parts_dir"/part_* > "$path"
  local actual_sha
  actual_sha="$(sha256sum "$path" | awk '{print $1}')"
  if [ "$actual_sha" != "$expected_sha" ]; then
    echo "sha256 mismatch for $path: $actual_sha != $expected_sha" >&2
    return 1
  fi
  echo "materialized $path"
}

materialize \
  artifacts/migration/fresh_db_legacy_material_detail_replay_payload_v1.csv \
  a0137e5a678bf5facac3b3042e26db116920176539bf4b033b3328c5088f794b
materialize \
  artifacts/migration/fresh_db_legacy_workflow_detail_replay_payload_v1.csv \
  f110ead85c0861d41c5a49d2169197c52ce71bf6df66689158ebfc9e23a7ec2c
materialize \
  artifacts/migration/scbsly_direct_select3_status_online_dump_20260603.json \
  cedb2eb07be634af3780ff28cbf4d7ba238d0b9f2a7a3a5f935996fc1da23503
