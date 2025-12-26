#!/usr/bin/env bash
set -euo pipefail

echo "[CI] odoo_ci.sh path=$(realpath "$0" 2>/dev/null || echo "$0")"
echo "[CI] whoami=$(whoami) uid=$(id -u) gid=$(id -g) groups=$(id -Gn || true)"
echo "[CI] env (raw): DB_CI=${DB_CI:-} MODULE=${MODULE:-} TEST_TAGS_FINAL=${TEST_TAGS_FINAL:-}"
echo

# ========= 必填 =========
: "${DB_CI:?DB_CI is required}"
: "${MODULE:?MODULE is required}"
: "${TEST_TAGS_FINAL:?TEST_TAGS_FINAL is required}"

# ========= 默认参数 =========
ODOO_BIN="${ODOO_BIN:-/usr/bin/odoo}"
ODOO_CONF="${ODOO_CONF:-/etc/odoo/odoo.conf}"

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-odoo}"
DB_PASSWORD="${DB_PASSWORD:-odoo}"

WITHOUT_DEMO="${WITHOUT_DEMO:-all}"

CI_LOG_DIR="${CI_LOG_DIR:-/tmp/ci}"
PHASE1_LOG="${PHASE1_LOG:-${CI_LOG_DIR}/phase1_install.log}"
PHASE2_LOG="${PHASE2_LOG:-${CI_LOG_DIR}/phase2_tests.log}"

mkdir -p "${CI_LOG_DIR}"

# ========= 失败时自动把关键信息吐出来 =========
on_fail() {
  local ec=$?
  echo
  echo "==================== [CI][FAIL] exit_code=${ec} ===================="
  echo "[CI] odoo.conf head:"
  (head -n 80 "${ODOO_CONF}" || true) | sed 's/^/[CI][odoo.conf] /'
  echo
  echo "[CI] last 200 lines: phase1"
  (tail -n 200 "${PHASE1_LOG}" 2>/dev/null || true) | sed 's/^/[CI][phase1] /'
  echo
  echo "[CI] last 200 lines: phase2"
  (tail -n 200 "${PHASE2_LOG}" 2>/dev/null || true) | sed 's/^/[CI][phase2] /'
  echo "==================================================================="
  exit "${ec}"
}
trap on_fail ERR

# ========= 自动降权：root -> odoo =========
# 你的镜像里 root 会直接退出(255)，所以必须降权。
if [[ "$(id -u)" == "0" ]]; then
  echo "[CI] running as root -> will re-exec as 'odoo' user to avoid exit 255"

  # 给 odoo 一个稳定 HOME（避免写到 /root/.local 之类）
  export HOME="${HOME:-/var/lib/odoo}"
  mkdir -p "${HOME}" || true
  chown -R odoo:odoo "${HOME}" 2>/dev/null || true

  if command -v gosu >/dev/null 2>&1; then
    exec gosu odoo:odoo "$0"
  elif command -v su-exec >/dev/null 2>&1; then
    exec su-exec odoo:odoo "$0"
  elif command -v runuser >/dev/null 2>&1; then
    exec runuser -u odoo -- "$0"
  elif command -v su >/dev/null 2>&1; then
    exec su -s /bin/bash -c "$0" odoo
  else
    echo "[CI][FATAL] no gosu/su-exec/runuser/su found; cannot drop privileges." >&2
    exit 127
  fi
fi

# ========= 进入非 root 后再继续 =========
set -x  # ★你要的 shell trace，放在降权之后才有意义

[[ -x "${ODOO_BIN}" ]] || { echo "[CI][FATAL] ODOO_BIN not executable: ${ODOO_BIN}" >&2; exit 127; }
[[ -f "${ODOO_CONF}" ]] || { echo "[CI][FATAL] ODOO_CONF not found: ${ODOO_CONF}" >&2; exit 2; }

echo "[CI] ODOO_BIN=${ODOO_BIN}"
echo "[CI] ODOO_CONF=${ODOO_CONF}"
echo "[CI] DB=${DB_CI} module=${MODULE} test_tags_FINAL=${TEST_TAGS_FINAL}"
echo "[CI] db_host=${DB_HOST} db_port=${DB_PORT} db_user=${DB_USER}"
echo "[CI] logs: ${PHASE1_LOG} | ${PHASE2_LOG}"
echo

echo "[CI] odoo.conf excerpt (log*):"
grep -E '^\s*(logfile|log_level|log_handler|syslog)\s*=' "${ODOO_CONF}" || true
echo

run_odoo() {
  local logfile="$1"; shift
  echo "[CI] run: ${ODOO_BIN} $*"
  (
    export PYTHONUNBUFFERED=1
    export PYTHONDONTWRITEBYTECODE=1
    if command -v stdbuf >/dev/null 2>&1; then
      stdbuf -oL -eL "${ODOO_BIN}" "$@"
    else
      "${ODOO_BIN}" "$@"
    fi
  ) 2>&1 | tee "${logfile}"
  return "${PIPESTATUS[0]}"
}

common_args=(
  --config="${ODOO_CONF}"
  --db_host="${DB_HOST}"
  --db_port="${DB_PORT}"
  --db_user="${DB_USER}"
  --db_password="${DB_PASSWORD}"
  --no-http
  --without-demo="${WITHOUT_DEMO}"
  --workers=0
  --max-cron-threads=0
  --logfile=-
  # 更稳：用 info/test 两段分别控
  --log-handler :INFO
  --log-handler odoo:INFO
  --log-handler odoo.modules:INFO
  --log-handler odoo.addons:INFO
  --log-handler odoo.tests:INFO
  --log-handler odoo.tests.common:INFO
  --log-handler odoo.tests.result:INFO
)

echo "[CI] phase1 install"
: > "${PHASE1_LOG}"
run_odoo "${PHASE1_LOG}" \
  "${common_args[@]}" \
  --log-level=info \
  -d "${DB_CI}" -i "${MODULE}" --stop-after-init
echo "[CI] phase1 OK"
echo

echo "[CI] phase2 upgrade+tests"
: > "${PHASE2_LOG}"
run_odoo "${PHASE2_LOG}" \
  "${common_args[@]}" \
  --log-level=test \
  -d "${DB_CI}" -u "${MODULE}" \
  --test-enable \
  --test-tags "${TEST_TAGS_FINAL}" \
  --stop-after-init
echo "[CI] phase2 OK"
echo

echo "[CI] done."
