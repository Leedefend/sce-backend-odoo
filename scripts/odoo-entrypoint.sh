#!/bin/sh
set -e

TPL="/etc/odoo/odoo.conf.template"
OUT="${ODOO_CONF_OUT:-/var/lib/odoo/odoo.conf}"
DB="${ODOO_DB:-${DB_NAME}}"

echo "[entrypoint] render odoo.conf: ${TPL} -> ${OUT}"

# ensure output directory writable
mkdir -p "$(dirname "$OUT")"

if command -v envsubst >/dev/null 2>&1; then
  echo "[entrypoint] using envsubst"
  # envsubst doesn't validate unresolved vars; python renderer acts as validator
  envsubst < "$TPL" > "$OUT"
else
  echo "[entrypoint] envsubst not found, using python3 renderer"
  python3 /usr/local/bin/render_odoo_conf.py "$TPL" "$OUT"
fi

echo "[entrypoint] rendered odoo.conf (show dbfilter line):"
grep -n "dbfilter" "$OUT" || true

echo "[entrypoint] check base bootstrap state"
if python3 - "$DB" <<'PY'
import os
import sys

import psycopg2

db = sys.argv[1]
try:
    conn = psycopg2.connect(
        dbname=db,
        user=os.environ.get("DB_USER", "odoo"),
        password=os.environ.get("DB_PASSWORD", "odoo"),
        host=os.environ.get("DB_HOST", "db"),
        port=int(os.environ.get("DB_PORT", "5432")),
        connect_timeout=5,
    )
except Exception:
    sys.exit(1)

try:
    with conn, conn.cursor() as cur:
        cur.execute("select to_regclass('public.ir_module_module')")
        if not cur.fetchone()[0]:
            sys.exit(1)
        cur.execute("select state from ir_module_module where name = 'base' limit 1")
        row = cur.fetchone()
        if not row or row[0] != "installed":
            sys.exit(1)
finally:
    conn.close()

sys.exit(0)
PY
then
  echo "[entrypoint] base already installed; skip base bootstrap reload"
else
  echo "[entrypoint] bootstrap base (without demo) if needed"
  if ! odoo -c "$OUT" -d "$DB" --no-http --workers=0 --max-cron-threads=0 \
      -i base --without-demo=all --stop-after-init >/dev/null 2>&1; then
    echo "[entrypoint] base bootstrap returned non-zero; continuing to normal start"
  fi
fi

echo "[entrypoint] start odoo"
exec odoo -c "$OUT"
