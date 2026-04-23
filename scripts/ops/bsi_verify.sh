#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/../_lib/common.sh"

DB_NAME="${DB_NAME:-sc_demo}"
SERVICE_LOGIN="${SERVICE_LOGIN:-svc_project_ro}"
MENU_XMLID="${MENU_XMLID:-smart_construction_core.menu_sc_project_project}"
ROOT_XMLID="${ROOT_XMLID:-smart_construction_core.menu_sc_root}"
ODOO_CONF="${ODOO_CONF:-/var/lib/odoo/odoo.conf}"

log "bsi.verify: db=${DB_NAME} login=${SERVICE_LOGIN} menu=${MENU_XMLID} root=${ROOT_XMLID}"

# shellcheck disable=SC2086
compose ${COMPOSE_FILES} exec -T odoo sh -lc "
odoo shell -d ${DB_NAME} -c ${ODOO_CONF} <<'PY'
from odoo import api, SUPERUSER_ID

login = '${SERVICE_LOGIN}'
menu_xmlid = '${MENU_XMLID}'
root_xmlid = '${ROOT_XMLID}'

try:
    env
except NameError:
    env = api.Environment(cr, SUPERUSER_ID, {})

u = env['res.users'].search([('login', '=', login)], limit=1)
if not u:
    raise SystemExit(f'BSI user not found: {login}')

def check_visible(xmlid):
    try:
        m = env.ref(xmlid)
    except Exception:
        return (False, 'XMLID_NOT_FOUND', None)
    Menu = env['ir.ui.menu'].with_user(u).with_context({'ir.ui.menu.full_list': False})
    visible = Menu.search([('id', '=', m.id)], limit=1)
    return (bool(visible), 'VISIBLE' if visible else 'NOT_VISIBLE', m.id)

ok_menu, msg_menu, id_menu = check_visible(menu_xmlid)
ok_root, msg_root, id_root = check_visible(root_xmlid)

roots = env['ir.ui.menu'].with_user(u).search([('parent_id', '=', False)])
print('=== BSI VERIFY RESULT ===')
print('login=', login, 'uid=', u.id)
print('menu_xmlid=', menu_xmlid, '=>', msg_menu, 'menu_id=', id_menu)
print('root_xmlid=', root_xmlid, '=>', msg_root, 'menu_id=', id_root)
print('visible_root_count=', len(roots))
print('sample_roots=', [(m.id, m.name) for m in roots[:12]])

if not ok_menu:
    raise SystemExit(2)
PY
"
