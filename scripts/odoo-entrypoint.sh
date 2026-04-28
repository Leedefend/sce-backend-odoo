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
if python3 - <<'PY'
import os
import sys

import psycopg2

db = os.environ.get("ODOO_DB") or os.environ.get("DB_NAME")
try:
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST", "db"),
        port=int(os.environ.get("DB_PORT", "5432")),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        dbname=db,
    )
    with conn.cursor() as cr:
        cr.execute("SELECT to_regclass('public.ir_module_module')")
        if not cr.fetchone()[0]:
            sys.exit(1)
        cr.execute("SELECT state FROM ir_module_module WHERE name='base' LIMIT 1")
        row = cr.fetchone()
        sys.exit(0 if row and row[0] == "installed" else 1)
except Exception:
    sys.exit(1)
PY
then
  echo "[entrypoint] base already installed; skip bootstrap"
else
  echo "[entrypoint] bootstrap base (without demo)"
  if ! odoo -c "$OUT" -d "$DB" --no-http --workers=0 --max-cron-threads=0 \
      -i base --without-demo=all --stop-after-init >/dev/null 2>&1; then
    echo "[entrypoint] base bootstrap returned non-zero; continuing to normal start"
  fi
fi

echo "[entrypoint] start odoo"
exec odoo -c "$OUT"
