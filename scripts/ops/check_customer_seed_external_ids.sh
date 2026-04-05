#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

DB_NAME="${DB_NAME:-${DB:-sc_prod_sim}}"

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME is required}"

SEED_LOGINS=(
  wutao
  yangdesheng
  zhangwencui
  lijianfeng
  yelingyue
  lidexue
  chenshuai
)

DB_PASSWORD="${DB_PASSWORD:-${DB_USER}}"

quote_login_list() {
  local out=""
  for login in "${SEED_LOGINS[@]}"; do
    if [[ -n "$out" ]]; then
      out+=" ,"
    fi
    out+="'${login}'"
  done
  printf '%s' "$out"
}

LOGIN_SQL_LIST="$(quote_login_list)"

psql_query() {
  local sql="$1"
  compose_dev exec -T -e PGPASSWORD="$DB_PASSWORD" db \
    psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -F $'\t' -Atc "$sql"
}

echo "[seed.external-id.guard] db=${DB_NAME}"

status=0

duplicate_rows="$(psql_query "
SELECT login, COUNT(*)
FROM res_users
WHERE login IN (${LOGIN_SQL_LIST})
GROUP BY login
HAVING COUNT(*) > 1
ORDER BY login;
")"

if [[ -n "$duplicate_rows" ]]; then
  echo "FAIL duplicate login rows detected:"
  echo "$duplicate_rows"
  status=1
else
  echo "OK no duplicate logins for seed users"
fi

missing_mapping_rows="$(psql_query "
WITH seed(login, xml_name) AS (
  VALUES
    ('wutao', 'user_sc_baosheng_wutao'),
    ('yangdesheng', 'user_sc_baosheng_yangdesheng'),
    ('zhangwencui', 'user_sc_baosheng_zhangwencui'),
    ('lijianfeng', 'user_sc_baosheng_lijianfeng'),
    ('yelingyue', 'user_sc_baosheng_yelingyue'),
    ('lidexue', 'user_sc_baosheng_lidexue'),
    ('chenshuai', 'user_sc_baosheng_chenshuai')
), existing AS (
  SELECT s.login, s.xml_name, u.id AS user_id
  FROM seed s
  JOIN res_users u ON u.login = s.login
), mapped AS (
  SELECT e.login, e.xml_name, e.user_id,
         imd.id AS imd_id,
         imd.res_id AS mapped_res_id
  FROM existing e
  LEFT JOIN ir_model_data imd
    ON imd.module = 'smart_construction_custom'
   AND imd.name = e.xml_name
   AND imd.model = 'res.users'
)
SELECT login, user_id, xml_name
FROM mapped
WHERE imd_id IS NULL OR mapped_res_id <> user_id
ORDER BY login;
")"

if [[ -n "$missing_mapping_rows" ]]; then
  echo "FAIL missing/misaligned smart_construction_custom external-id mapping:"
  echo "$missing_mapping_rows"
  status=1
else
  echo "OK external-id mappings aligned for existing seed users"
fi

presence_rows="$(psql_query "
SELECT login, COUNT(*)
FROM res_users
WHERE login IN (${LOGIN_SQL_LIST})
GROUP BY login
ORDER BY login;
")"

echo "INFO current seed login presence:"
if [[ -n "$presence_rows" ]]; then
  echo "$presence_rows"
else
  echo "(none)"
fi

if [[ "$status" -ne 0 ]]; then
  echo "RESULT: FAIL"
  exit 1
fi

echo "RESULT: PASS"
