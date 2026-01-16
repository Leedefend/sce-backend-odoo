# Environment Usage (dev/test/prod)

This project supports multiple environments via `.env.<env>` files. Use `ENV=<env>` or `ENV_FILE=<path>` to select which environment to run.

## 1) Files

- `.env.dev` (local development)
- `.env.test` (test/regression)
- `.env.prod` (production)

Each file defines:
- `COMPOSE_PROJECT_NAME` (unique per env)
- `DB_NAME`
- `ODOO_DBFILTER`
- `DB_DATA` / `REDIS_DATA` / `ODOO_DATA` (data isolation; named volumes or bind mounts)
- `NGINX_PORT` / `ODOO_PORT` (port isolation)

Note: if you use bind mounts (paths like `./runtime/...`), prefer Linux filesystem paths on WSL to avoid permission issues. Named volumes avoid this entirely.

## 2) Common Commands

Use `ENV=<env>` with Make:

```bash
# Start services
ENV=dev make up
ENV=test make up
ENV=prod make up

# Logs
ENV=dev make logs
ENV=test make logs
ENV=prod make logs

# Restart (dev only by default)
ENV=dev make restart
```

Or select a file explicitly:

```bash
ENV_FILE=.env.dev make up
```

## 3) Local Development (dev)

Goal: day-to-day coding/debugging.

```bash
ENV=dev make up
ENV=dev make logs
ENV=dev make restart
```

Notes:
- Uses `.env.dev`
- Default ports: `NGINX_PORT=18081`, `ODOO_PORT=8070`
- Data: `DB_DATA=db_data`, `REDIS_DATA=redis_data`, `ODOO_DATA=odoo_data`
- Locked DB: `ODOO_DBFILTER=^sc_demo$`

## 4) Test Environment (test)

Goal: regression and automation.

```bash
ENV=test make up
ENV=test make test
```

Notes:
- Uses `.env.test`
- Default ports: `NGINX_PORT=18082`, `ODOO_PORT=8071`
- Data: `DB_DATA=db_data`, `REDIS_DATA=redis_data`, `ODOO_DATA=odoo_data`
- Locked DB: `ODOO_DBFILTER=^sc_test$`

## 5) Production (prod)

Goal: server runtime.

```bash
ENV=prod make up
```

Notes:
- Uses `.env.prod`
- Replace `DB_PASSWORD`, `ADMIN_PASSWD`, `JWT_SECRET`
- Default ports: `NGINX_PORT=18083`, `ODOO_PORT=8072`
- Data: `DB_DATA=db_data`, `REDIS_DATA=redis_data`, `ODOO_DATA=odoo_data`
- Locked DB: `ODOO_DBFILTER=^sc_prod$`

## 6) Troubleshooting

- Check effective env:

```bash
ENV=dev make diag.project
```

- Verify Odoo DB lock:

```bash
docker compose --env-file .env.dev exec -T odoo grep dbfilter /var/lib/odoo/odoo.conf
```

- Full logs (no truncation):

```bash
ENV=dev docker compose logs --no-color --timestamps --tail=0 odoo nginx
```
