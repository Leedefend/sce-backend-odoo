#!/usr/bin/env bash
set -euo pipefail

STAGE_NAME="${STAGE:-${1:-}}"
DB_NAME="${DB:-${2:-}}"
STAGE_DEF="${STAGE_DEF:-}"
ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

trap 'STAGE_STATUS="FAIL"; finalize_report; echo "STAGE_RESULT: FAIL"' ERR

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

  declare -A markers_by_cmd
  all_markers=""
  markers_raw="$(read_yaml_list "evidence_markers" "$STAGE_DEF")"
  if [[ -z "$markers_raw" ]]; then
    echo "FAIL: evidence_markers is empty"
    exit 1
  fi
  while IFS= read -r marker; do
    if [[ "$marker" =~ ^cmd([0-9]+):(.+)$ ]]; then
      idx="${BASH_REMATCH[1]}"
      val="${BASH_REMATCH[2]}"
      markers_by_cmd["$idx"]+="${val}"$'\n'
    elif [[ "$marker" =~ ^all:(.+)$ ]]; then
      all_markers+="${BASH_REMATCH[1]}"$'\n'
    else
      all_markers+="${marker}"$'\n'
    fi
  done < <(echo "$markers_raw")

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

    markers="${all_markers}${markers_by_cmd[$cmd_index]:-}"
    if [[ -z "$markers" ]]; then
      echo "FAIL: no evidence markers configured for cmd${cmd_index}"
      echo "${cmd_index}|${cmd}|(none)|FAIL" >> "$SUMMARY_FILE"
      exit 1
    fi

    missing=0
    markers_flat="$(echo "$markers" | sed '/^$/d' | tr '\n' ';')"
    while IFS= read -r m; do
      if ! grep -F -q "$m" "$tmp_out"; then
        echo "FAIL: marker not found for cmd${cmd_index}: ${m}"
        missing=1
      fi
    done < <(echo "$markers" | sed '/^$/d')

    if [[ "$missing" -ne 0 ]]; then
      echo "${cmd_index}|${cmd}|${markers_flat}|FAIL" >> "$SUMMARY_FILE"
      exit 1
    fi

    echo "${cmd_index}|${cmd}|${markers_flat}|PASS" >> "$SUMMARY_FILE"
  done < <(read_yaml_list "required_commands" "$STAGE_DEF")

  if [[ -z "$REPORT_OUT" ]]; then
    timestamp="$(date +%Y%m%d_%H%M%S)"
    REPORT_OUT="$ROOT_DIR/out/stage_report_${STAGE_NAME}_${timestamp}.md"
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
