#!/bin/sh
set -e

TPL="/etc/odoo/odoo.conf.template"
OUT="${ODOO_CONF_OUT:-/var/lib/odoo/odoo.conf}"
DB="${ODOO_DB:-${DB_NAME:-sc_odoo}}"

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

echo "[entrypoint] bootstrap base (without demo) if needed"
if ! odoo -c "$OUT" -d "$DB" --no-http --workers=0 --max-cron-threads=0 \
    -i base --without-demo=all --stop-after-init >/dev/null 2>&1; then
  echo "[entrypoint] base bootstrap returned non-zero; continuing to normal start"
fi

echo "[entrypoint] start odoo"
exec odoo -c "$OUT"
