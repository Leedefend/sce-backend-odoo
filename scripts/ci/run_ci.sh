#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"

: "${MODULE:?MODULE required}"
: "${DB_CI:?DB_CI required}"
: "${DB_USER:=odoo}"
: "${DB_PASSWORD:=${DB_USER}}"
: "${ADDONS_EXTERNAL_MOUNT:?ADDONS_EXTERNAL_MOUNT required}"
: "${DOCS_MOUNT_HOST:?DOCS_MOUNT_HOST required}"
: "${DOCS_MOUNT_CONT:?DOCS_MOUNT_CONT required}"

mkdir -p "${CI_ARTIFACT_DIR}"

TEST_TAGS_FINAL="$(normalize_test_tags "${MODULE}" "${TEST_TAGS:-}")"
log "CI run: MODULE=${MODULE} DB_CI=${DB_CI}"
log "CI run: TEST_TAGS=${TEST_TAGS:-}"
log "CI run: TEST_TAGS_FINAL=${TEST_TAGS_FINAL}"

# 0) 准备数据库（保证干净）
log "CI db reset: ${DB_CI}"
compose ${COMPOSE_TEST_FILES} up -d db redis

# 等待 Postgres 就绪（容器刚启动时 socket 可能还没创建）
log "CI db wait: pg_isready"
for i in $(seq 1 60); do
  if compose ${COMPOSE_TEST_FILES} exec -T db pg_isready -U "${DB_USER}" -d postgres >/dev/null 2>&1; then
    log "CI db ready"
    break
  fi
  if [[ "$i" -eq 60 ]]; then
    log "CI db NOT ready after 60s"
    compose ${COMPOSE_TEST_FILES} logs --tail=200 db || true
    exit 2
  fi
  sleep 1
done

# 断开可能残留的连接，保证 DROP 成功
compose ${COMPOSE_TEST_FILES} exec -T db psql -U "${DB_USER}" -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_CI}';" >/dev/null || true
compose ${COMPOSE_TEST_FILES} exec -T db psql -U "${DB_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${DB_CI};"
compose ${COMPOSE_TEST_FILES} exec -T db psql -U "${DB_USER}" -d postgres -c \
  "CREATE DATABASE ${DB_CI} OWNER ${DB_USER} TEMPLATE template0 ENCODING 'UTF8';"

# 1) 确保依赖（解决 odoo_test_helper 缺失）
bash "$(dirname "$0")/ensure_testdeps.sh"

# 2) 跑测试（统一挂载 docs，避免 permission_matrix 文档找不到）
# 注意：这里“每次都 pip install”是稳定优先策略（镜像不改也能跑通）
# shellcheck disable=SC2086
compose ${COMPOSE_TEST_FILES} run --rm -T \
  -v "${DOCS_MOUNT_HOST}:${DOCS_MOUNT_CONT}:ro" \
  --entrypoint bash odoo -lc "
    pip3 install -q odoo-test-helper >/dev/null 2>&1 || true
    exec /usr/bin/odoo \
      --db_host=db --db_port=5432 --db_user=${DB_USER} --db_password=${DB_PASSWORD} \
      -d ${DB_CI} \
      --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,${ADDONS_EXTERNAL_MOUNT} \
      -i ${MODULE} \
      --without-demo=all \
      --no-http --workers=0 --max-cron-threads=0 \
      --test-enable \
      --test-tags \"${TEST_TAGS_FINAL}\" \
      --stop-after-init \
      --log-level=test
  " 2>&1 | tee "${CI_ARTIFACT_DIR}/${CI_LOG}"

log "CI finished. Log: ${CI_ARTIFACT_DIR}/${CI_LOG}"

# 3) 简单验收：看通过签名（你可以按需强化）
if grep -Eq "${CI_PASS_SIG_RE}" "${CI_ARTIFACT_DIR}/${CI_LOG}"; then
  log "PASS signature matched: ${CI_PASS_SIG_RE}"
else
  log "WARN: PASS signature NOT found (check logs)."
  exit 1
fi

# 4) 可选：清理 artifacts（保留最近 N 份）
if [[ "${CI_ARTIFACT_PURGE:-1}" == "1" ]]; then
  log "purge artifacts keep=${CI_ARTIFACT_KEEP}"
  ls -1t "${CI_ARTIFACT_DIR}"/*.log 2>/dev/null | tail -n "+$((CI_ARTIFACT_KEEP+1))" | xargs -r rm -f
fi
