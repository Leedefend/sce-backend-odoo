#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"

: "${DB_NAME:?DB_NAME required}"
: "${DB_USER:?DB_USER required}"
: "${COMPOSE_FILES:?COMPOSE_FILES required}"

DB_PASSWORD=${DB_PASSWORD:-${DB_USER}}

log "db reset: ${DB_NAME}"
compose ${COMPOSE_FILES} up -d db redis

log "db wait: pg_isready"
for i in $(seq 1 60); do
  if compose ${COMPOSE_FILES} exec -T db pg_isready -U "${DB_USER}" -d postgres >/dev/null 2>&1; then
    log "db ready"
    break
  fi
  if [[ "$i" -eq 60 ]]; then
    log "db NOT ready after 60s"
    compose ${COMPOSE_FILES} logs --tail=200 db || true
    exit 2
  fi
  sleep 1
done

# terminate existing connections to allow drop
compose ${COMPOSE_FILES} exec -T db psql -U "${DB_USER}" -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}';" >/dev/null || true

compose ${COMPOSE_FILES} exec -T db psql -U "${DB_USER}" -d postgres -c \
  "DROP DATABASE IF EXISTS ${DB_NAME};"
compose ${COMPOSE_FILES} exec -T db psql -U "${DB_USER}" -d postgres -c \
  "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER} TEMPLATE template0 ENCODING 'UTF8';"

# ====== Odoo 初始化 + 基线统一（lang/tz/currency）======
DEFAULT_LANG=${DEFAULT_LANG:-zh_CN}
DEFAULT_TZ=${DEFAULT_TZ:-Asia/Shanghai}
DEFAULT_CURRENCY=${DEFAULT_CURRENCY:-CNY}

# 统一 Odoo DB 参数（后续所有操作必须带，避免掉回本机 socket）
ODOO_DB_ARGS=(
  --db_host=db --db_port=5432
  --db_user="${DB_USER}" --db_password="${DB_PASSWORD}"
)

log "odoo init base (stop-after-init): ${DB_NAME}"
compose ${COMPOSE_FILES} run --rm -T \
  --entrypoint /usr/bin/odoo odoo \
  --config=/etc/odoo/odoo.conf \
  -d "${DB_NAME}" \
  "${ODOO_DB_ARGS[@]}" \
  -i base \
  --no-http --workers=0 --max-cron-threads=0 \
  --stop-after-init

log "baseline locale/currency: lang=${DEFAULT_LANG} tz=${DEFAULT_TZ} currency=${DEFAULT_CURRENCY}"

# 不用 `odoo shell`（你这版 /usr/bin/odoo 不支持），改用 python 引导 Odoo 环境执行脚本
compose ${COMPOSE_FILES} run --rm -T \
  --entrypoint /usr/bin/python3 odoo \
  - <<PY
import os

DB_NAME = os.environ.get("DB_NAME", "${DB_NAME}")
DB_HOST = "db"
DB_PORT = "5432"
DB_USER = os.environ.get("DB_USER", "${DB_USER}")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "${DB_PASSWORD}")

LANG = os.environ.get("DEFAULT_LANG", "${DEFAULT_LANG}")
TZ = os.environ.get("DEFAULT_TZ", "${DEFAULT_TZ}")
CUR = os.environ.get("DEFAULT_CURRENCY", "${DEFAULT_CURRENCY}")

# ---- bootstrap odoo ----
import odoo
from odoo import api, SUPERUSER_ID
from odoo.tools import config

# 让 config 拿到 addons_path 等基础配置（与你 /etc/odoo/odoo.conf 一致）
config.parse_config([
    "--config=/etc/odoo/odoo.conf",
    f"--db_host={DB_HOST}",
    f"--db_port={DB_PORT}",
    f"--db_user={DB_USER}",
    f"--db_password={DB_PASSWORD}",
])

# 建 registry + env
registry = odoo.registry(DB_NAME)
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    # 1) 确保语言存在（没装就装）
    env["res.lang"]._activate_lang(LANG)

    # 2) 系统参数（更偏向“默认值”）
    ICP = env["ir.config_parameter"].sudo()
    ICP.set_param("lang", LANG)
    ICP.set_param("tz", TZ)

    # 3) 公司级：币种
    company = env.company
    company.write({"currency_id": env.ref(f"base.{CUR}").id})

    # 4) admin 用户级：语言/时区
    admin = env.ref("base.user_admin")
    admin.write({"lang": LANG, "tz": TZ})

    cr.commit()

print("[db.reset] baseline applied")
PY

log "db reset done: ${DB_NAME}"
