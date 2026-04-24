#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"

: "${DB_NAME:?DB_NAME is required}"

guard_prod_forbid

ASSET_ROOT="${ASSET_ROOT:-$ROOT_DIR/migration_assets}"
LANE="${LANE:-user}"
MODULE_NAMESPACE="${MODULE_NAMESPACE:-migration_assets}"
VERIFY_SCRIPT="$ROOT_DIR/scripts/migration/user_asset_verify.py"
SHELL_EXEC="$ROOT_DIR/scripts/ops/odoo_shell_exec.sh"
XML_PATH="$ASSET_ROOT/10_master/$LANE/${LANE}_master_v1.xml"

if [[ ! -f "$XML_PATH" ]]; then
  echo "❌ user history XML asset not found: $XML_PATH" >&2
  exit 2
fi

if [[ ! -f "$VERIFY_SCRIPT" ]]; then
  echo "❌ verifier script missing: $VERIFY_SCRIPT" >&2
  exit 2
fi

if [[ ! -f "$SHELL_EXEC" ]]; then
  echo "❌ odoo shell executor missing: $SHELL_EXEC" >&2
  exit 2
fi

echo "[history.users.rebuild] verifying asset package: lane=$LANE asset_root=$ASSET_ROOT"
python3 "$VERIFY_SCRIPT" --asset-root "$ASSET_ROOT" --lane "$LANE" --check

payload_file="$(mktemp)"
trap 'rm -f "$payload_file"' EXIT

python3 - "$XML_PATH" "$MODULE_NAMESPACE" >"$payload_file" <<'PY'
from __future__ import annotations

import base64
import sys
from pathlib import Path

xml_path = Path(sys.argv[1])
module_namespace = sys.argv[2]
xml_b64 = base64.b64encode(xml_path.read_bytes()).decode("ascii")

script = f"""
import base64
import xml.etree.ElementTree as ET

xml_bytes = base64.b64decode('''{xml_b64}'''.encode('ascii'))
root = ET.fromstring(xml_bytes)
Users = env['res.users'].sudo().with_context(active_test=False, no_reset_password=True)
Imd = env['ir.model.data'].sudo().with_context(active_test=False)
main_company = env.ref('base.main_company')
created = 0
updated = 0
xmlids_linked = 0

for rec in root.findall('.//record'):
    xmlid_name = (rec.attrib.get('id') or '').strip()
    model = (rec.attrib.get('model') or '').strip()
    if model != 'res.users' or not xmlid_name:
        continue
    fields = {{}}
    for field in rec.findall('field'):
        name = (field.attrib.get('name') or '').strip()
        fields[name] = (field.text or '').strip()
    login = fields.get('login')
    if not login:
        raise RuntimeError({{'missing_login': xmlid_name}})
    email = fields.get('email') or False
    if email in ('', 'null', 'None'):
        email = False
    active = (fields.get('active', '1') or '1') in ('1', 'true', 'True')
    vals = {{
        'name': fields.get('name') or login,
        'login': login,
        'email': email,
        'share': False,
        'company_id': main_company.id,
        'company_ids': [(6, 0, [main_company.id])],
    }}
    imd = Imd.search([
        ('module', '=', '{module_namespace}'),
        ('name', '=', xmlid_name),
        ('model', '=', 'res.users'),
    ], limit=1)
    user = env['res.users']
    if imd and imd.res_id:
        user = Users.browse(imd.res_id).exists()
    if not user:
        user = Users.search([('login', '=', login)], limit=1)
    if user:
        user.write(dict(vals, active=active))
        updated += 1
    else:
        user = Users.create(dict(vals, active=True))
        if not active:
            user.write({{'active': False}})
        created += 1
    if imd:
        if imd.res_id != user.id:
            imd.write({{'res_id': user.id}})
            xmlids_linked += 1
    else:
        Imd.create({{
            'module': '{module_namespace}',
            'name': xmlid_name,
            'model': 'res.users',
            'res_id': user.id,
            'noupdate': True,
        }})
        xmlids_linked += 1

env.cr.commit()
legacy_users = Users.search_count([('login', 'like', 'legacy_%')])
legacy_users_active = Users.search_count([('login', 'like', 'legacy_%'), ('active', '=', True)])
legacy_users_inactive = Users.search_count([('login', 'like', 'legacy_%'), ('active', '=', False)])
legacy_imd = Imd.search_count([
    ('module', '=', '{module_namespace}'),
    ('name', 'like', 'legacy_user_sc_%'),
    ('model', '=', 'res.users'),
])
sample = [
    {{
        'id': u.id,
        'login': u.login,
        'name': u.name,
        'active': u.active,
    }}
    for u in Users.search([('login', 'like', 'legacy_%')], limit=5, order='login asc')
]
print({{
    'status': 'PASS',
    'module': '{module_namespace}',
    'created': created,
    'updated': updated,
    'xmlids_linked': xmlids_linked,
    'legacy_users': legacy_users,
    'active': legacy_users_active,
    'inactive': legacy_users_inactive,
    'legacy_user_xmlids': legacy_imd,
    'sample': sample,
}})
"""

print(script)
PY

echo "[history.users.rebuild] importing historical users into db=$DB_NAME module=$MODULE_NAMESPACE"
DB_NAME="$DB_NAME" bash "$SHELL_EXEC" <"$payload_file"
