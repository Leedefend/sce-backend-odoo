#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"

: "${DB_NAME:?DB_NAME required}"
: "${DB_USER:?DB_USER required}"
: "${COMPOSE_FILES:?COMPOSE_FILES required}"

DB_PASSWORD=${DB_PASSWORD:-${DB_USER}}

log "db reset: ${DB_NAME}"
compose ${COMPOSE_FILES} up -d db redis

log "db wait: pg_isready"
for i in $(seq 1 60); do
  if compose ${COMPOSE_FILES} exec -T db pg_isready -U "${DB_USER}" -d postgres >/dev/null 2>&1; then
    log "db ready"
    break
  fi
  if [[ "$i" -eq 60 ]]; then
    log "db NOT ready after 60s"
    compose ${COMPOSE_FILES} logs --tail=200 db || true
    exit 2
  fi
  sleep 1
done

# terminate existing connections to allow drop
compose ${COMPOSE_FILES} exec -T db psql -U "${DB_USER}" -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}';" >/dev/null || true

compose ${COMPOSE_FILES} exec -T db psql -U "${DB_USER}" -d postgres -c \
  "DROP DATABASE IF EXISTS ${DB_NAME};"
compose ${COMPOSE_FILES} exec -T db psql -U "${DB_USER}" -d postgres -c \
  "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER} TEMPLATE template0 ENCODING 'UTF8';"

log "db reset done: ${DB_NAME}"
