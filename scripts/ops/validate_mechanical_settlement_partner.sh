#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${DB_NAME:-sc_demo}"

docker compose exec -T odoo odoo shell \
  -d "$DB_NAME" \
  --db_host=db \
  --db_port=5432 \
  --db_user=odoo \
  --db_password=odoo \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux \
  --logfile=/dev/null \
  --log-level=warn < scripts/verify/mechanical_settlement_partner_audit.py
