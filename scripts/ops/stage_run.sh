#!/usr/bin/env bash
set -euo pipefail

STAGE_NAME="${STAGE:-${1:-}}"
DB_NAME="${DB:-${2:-}}"
STAGE_DEF="${STAGE_DEF:-}"
ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

trap 'STAGE_STATUS="FAIL"; finalize_report; echo "STAGE_RESULT: FAIL"' ERR
trap 'git restore --source=HEAD --worktree --staged -- docs/audit >/dev/null 2>&1 || true' EXIT

if [[ -z "$STAGE_NAME" ]]; then
  echo "FAIL: STAGE is required"
  exit 2
fi

if [[ -z "$DB_NAME" ]]; then
  echo "FAIL: DB is required"
  exit 2
fi

export DB="$DB_NAME"

if [[ -z "$STAGE_DEF" ]]; then
  if [[ -f "$ROOT_DIR/docs/ops/stage_defs/${STAGE_NAME}.yml" ]]; then
    STAGE_DEF="$ROOT_DIR/docs/ops/stage_defs/${STAGE_NAME}.yml"
  fi
fi

SUMMARY_FILE="$(mktemp)"
REPORT_OUT="${REPORT_OUT:-}"
STAGE_STATUS="FAIL"

read_yaml_list() {
  local key="$1"
  local file="$2"
  awk -v key="$key" '
    $0 ~ "^"key":" {found=1; next}
    found && $0 ~ /^  - / {sub(/^  - /,""); print; next}
    found {exit}
  ' "$file"
}

read_yaml_scalar() {
  local key="$1"
  local file="$2"
  awk -F': ' -v key="$key" '$1 == key {print $2; exit}' "$file"
}

read_yaml_cmd_markers() {
  local cmd_index="$1"
  local file="$2"
  awk -v cmd="cmd${cmd_index}:" '
    $0 ~ /^evidence_markers:/ {in_list=1; next}
    in_list && $0 ~ "^  "cmd {in_cmd=1; next}
    in_list && in_cmd && $0 ~ /^    - / {sub(/^    - /,""); print; next}
    in_list && in_cmd {exit}
    in_list && $0 !~ /^  / {exit}
  ' "$file"
}

check_db_exists() {
  local db_name="$1"
  # shellcheck source=../common/env.sh
  source "$ROOT_DIR/scripts/common/env.sh"
  # shellcheck source=../common/compose.sh
  source "$ROOT_DIR/scripts/common/compose.sh"
  DB_PASSWORD="${DB_PASSWORD:-${DB_USER}}"

  db_exists="$(compose_dev exec -T -e PGPASSWORD="$DB_PASSWORD" db psql -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${db_name}';" || true)"
  db_exists="$(echo "$db_exists" | tr -d '[:space:]')"
  if [[ "$db_exists" != "1" ]]; then
    echo "FAIL database ${db_name} not found"
    echo "Fix: make db.reset DB=${db_name}  # or make mod.upgrade MODULE=smart_construction_core DB=${db_name}"
    return 1
  fi
}

finalize_report() {
  if [[ -z "$REPORT_OUT" ]]; then
    return 0
  fi
  mkdir -p "$(dirname "$REPORT_OUT")"
  STAGE="$STAGE_NAME" STAGE_STATUS="$STAGE_STATUS" SUMMARY_FILE="$SUMMARY_FILE" REPORT_OUT="$REPORT_OUT" \
    bash "$ROOT_DIR/scripts/ops/stage_report.sh" >/dev/null 2>&1 || true
}

DB="$DB_NAME" bash "$ROOT_DIR/scripts/ops/stage_preflight.sh"

if [[ -n "$STAGE_DEF" ]]; then
  echo "STAGE_DEF: ${STAGE_DEF}"
  db_must_exist="$(read_yaml_scalar "db_must_exist" "$STAGE_DEF")"
  if [[ "$db_must_exist" == "true" ]]; then
    check_db_exists "$DB_NAME"
  fi

  evidence_markers_strict="$(read_yaml_scalar "evidence_markers_strict" "$STAGE_DEF")"

  cmd_index=0
  commands_raw="$(read_yaml_list "required_commands" "$STAGE_DEF")"
  if [[ -z "$commands_raw" ]]; then
    echo "FAIL: required_commands is empty"
    exit 1
  fi
  while IFS= read -r cmd; do
    cmd_index=$((cmd_index + 1))
    echo "[stage] run: ${cmd}"
    tmp_out="$(mktemp)"
    if ! bash -lc "$cmd" < /dev/null 2>&1 | tee "$tmp_out"; then
      echo "${cmd_index}|${cmd}|(command failed)|FAIL" >> "$SUMMARY_FILE"
      exit 1
    fi

    markers="$(read_yaml_cmd_markers "$cmd_index" "$STAGE_DEF")"
    if [[ -z "$markers" ]]; then
      if [[ "$evidence_markers_strict" == "true" ]]; then
        echo "FAIL: no evidence markers configured for cmd${cmd_index}"
        echo "${cmd_index}|${cmd}|(none)|FAIL" >> "$SUMMARY_FILE"
        exit 1
      else
        echo "${cmd_index}|${cmd}|(none)|PASS" >> "$SUMMARY_FILE"
        continue
      fi
    fi

    markers_sanitized="$(echo "$markers" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")"
    missing=0
    markers_flat="$(echo "$markers_sanitized" | sed '/^$/d' | tr '\n' ';')"
    while IFS= read -r m; do
      if ! grep -F -q "$m" "$tmp_out"; then
        echo "FAIL: marker not found for cmd${cmd_index}: ${m}"
        missing=1
      fi
    done < <(echo "$markers_sanitized" | sed '/^$/d')

    if [[ "$missing" -ne 0 ]]; then
      echo "${cmd_index}|${cmd}|${markers_flat}|FAIL" >> "$SUMMARY_FILE"
      exit 1
    fi

    echo "${cmd_index}|${cmd}|${markers_flat}|PASS" >> "$SUMMARY_FILE"
  done < <(read_yaml_list "required_commands" "$STAGE_DEF")

  if [[ -z "$REPORT_OUT" ]]; then
    timestamp="$(date +%Y%m%d_%H%M%S)"
    REPORT_OUT="$ROOT_DIR/out/stage_reports/${STAGE_NAME}_${timestamp}.md"
  fi
  STAGE_STATUS="PASS"
  finalize_report

  while IFS= read -r cleanup_cmd; do
    if [[ -n "$cleanup_cmd" ]]; then
      bash -lc "$cleanup_cmd"
    fi
  done < <(read_yaml_list "post_cleanup" "$STAGE_DEF")
else
  make ci.gate.tp08 DB=sc_demo
  case "$STAGE_NAME" in
    p2*)
      make p2.smoke DB="$DB_NAME"
      ;;
    p3*)
      make p3.smoke DB="$DB_NAME"
      make p3.audit DB="$DB_NAME"
      ;;
    *)
      echo "FAIL: unsupported STAGE '${STAGE_NAME}'"
      exit 2
      ;;
  esac
fi

echo "STAGE_RESULT: PASS"
