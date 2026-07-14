#!/usr/bin/env bash
set -euo pipefail
NAME=sc-backend-odoo-acceptance
if docker ps --format '{{.Names}}' | grep -qx "$NAME"; then echo "[backend.acceptance.up] already running"; exit 0; fi
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker compose run -d --no-deps --name "$NAME" -p 127.0.0.1:18082:8069 -e ODOO_DB=sc_frontend_acceptance -e DB_NAME=sc_frontend_acceptance -e ODOO_DBFILTER='^sc_frontend_acceptance$' -e LIST_DB=false odoo >/dev/null
for _ in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:18082/web/login >/dev/null 2>&1; then echo "[backend.acceptance.up] PASS db=sc_frontend_acceptance port=18082"; exit 0; fi
  sleep 2
done
docker logs --tail 100 "$NAME" >&2
exit 1
