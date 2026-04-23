#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/../_lib/common.sh"

DB_NAME="${DB_NAME:-sc_demo}"
SERVICE_LOGIN="${SERVICE_LOGIN:-svc_project_ro}"
SERVICE_PASSWORD="${SERVICE_PASSWORD:-svc_project_ro_ChangeMe_123!}"
GROUP_XMLIDS="${GROUP_XMLIDS:-base.group_user,project.group_project_user}"
ODOO_CONF="${ODOO_CONF:-/var/lib/odoo/odoo.conf}"

log "bsi.create: db=${DB_NAME} login=${SERVICE_LOGIN}"

# shellcheck disable=SC2086
compose ${COMPOSE_FILES} exec -T odoo sh -lc "
odoo shell -d ${DB_NAME} -c ${ODOO_CONF} <<'PY'
from odoo import api, SUPERUSER_ID

login = '${SERVICE_LOGIN}'
password = '${SERVICE_PASSWORD}'
group_xmlids = '${GROUP_XMLIDS}'.split(',') if '${GROUP_XMLIDS}'.strip() else []

try:
    env
except NameError:
    env = api.Environment(cr, SUPERUSER_ID, {})

def ref(xmlid):
    try:
        return env.ref(xmlid.strip())
    except Exception:
        return None

group_ids, missing = [], []
for xid in group_xmlids:
    if not xid.strip():
        continue
    g = ref(xid)
    if not g:
        missing.append(xid)
    else:
        group_ids.append(g.id)

Users = env['res.users'].sudo()
u = Users.search([('login', '=', login)], limit=1)
if not u:
    u = Users.create({
        'name': 'Service - Project Readonly',
        'login': login,
        'password': password,
        'email': f'{login}@example.invalid',
        'active': True,
        'groups_id': [(6, 0, group_ids)],
    })
    action = 'CREATED'
else:
    u.write({'groups_id': [(6, 0, group_ids)]})
    action = 'UPDATED'

print('=== BSI CREATE RESULT ===')
print('action=', action)
print('login=', login)
print('uid=', u.id)
print('groups_xmlids=', group_xmlids)
if missing:
    print('WARNING missing group xmlids:', missing)

env.cr.commit()
PY
"
