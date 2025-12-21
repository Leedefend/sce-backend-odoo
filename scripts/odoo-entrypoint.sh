#!/bin/sh
set -e

echo "[entrypoint] start render odoo.conf"

if command -v envsubst >/dev/null 2>&1; then
  echo "[entrypoint] using envsubst"
  envsubst < /etc/odoo/odoo.conf.template > /etc/odoo/odoo.conf
else
  echo "[entrypoint] envsubst not found, using python3 renderer"
  python3 /usr/local/bin/render_odoo_conf.py /etc/odoo/odoo.conf.template /etc/odoo/odoo.conf
fi

echo "[entrypoint] rendered odoo.conf (show dbfilter line):"
grep -n "dbfilter" /etc/odoo/odoo.conf || true

echo "[entrypoint] bootstrap base (without demo) if needed"
odoo -c /etc/odoo/odoo.conf -d sc_odoo -i base --without-demo=all --stop-after-init || true

echo "[entrypoint] start odoo"
exec odoo -c /etc/odoo/odoo.conf
