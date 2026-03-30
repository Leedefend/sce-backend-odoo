#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PORT="${VITE_DEV_PORT:-5174}"
HOST="${VITE_DEV_HOST:-127.0.0.1}"
PIDFILE="${FRONTEND_DEV_PIDFILE:-/tmp/sc-frontend-dev.pid}"
LOGFILE="${FRONTEND_DEV_LOGFILE:-/tmp/sc-frontend-dev.log}"
READY_URL="${FRONTEND_DEV_READY_URL:-http://${HOST}:${PORT}/}"

log() { printf '[%s] %s\n' "$(date +'%H:%M:%S')" "$*"; }

kill_pid_if_alive() {
  local pid="$1"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 20); do
      if ! kill -0 "$pid" 2>/dev/null; then
        return 0
      fi
      sleep 0.2
    done
    kill -9 "$pid" 2>/dev/null || true
  fi
}

kill_existing_port_listener() {
  local port="$1"
  local pids=""
  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true)"
  elif command -v ss >/dev/null 2>&1; then
    pids="$(ss -ltnp 2>/dev/null | awk -v target=":${port}" '$4 ~ target {print $NF}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | sort -u)"
  fi
  [[ -z "$pids" ]] && return 0
  for pid in $pids; do
    local cmdline=""
    cmdline="$(ps -p "$pid" -o args= 2>/dev/null || true)"
    if [[ "$cmdline" == *"vite"* ]] || [[ "$cmdline" == *"/frontend/apps/web"* ]]; then
      log "stop existing frontend dev listener pid=${pid} port=${port}"
      kill_pid_if_alive "$pid"
    fi
  done
}

if [[ -f "${PIDFILE}" ]]; then
  old_pid="$(cat "${PIDFILE}" 2>/dev/null || true)"
  [[ -n "${old_pid:-}" ]] && log "stop previous frontend dev pid=${old_pid}"
  kill_pid_if_alive "${old_pid:-}"
fi

kill_existing_port_listener "${PORT}"

log "start frontend dev host=${HOST} port=${PORT}"
cd "${ROOT_DIR}"
rm -f "${LOGFILE}"
nohup pnpm -C frontend/apps/web dev --host "${HOST}" --port "${PORT}" >"${LOGFILE}" 2>&1 &
new_pid=$!
echo "${new_pid}" > "${PIDFILE}"

for _ in $(seq 1 60); do
  if ! kill -0 "${new_pid}" 2>/dev/null; then
    log "frontend dev exited unexpectedly"
    tail -n 120 "${LOGFILE}" 2>/dev/null || true
    exit 1
  fi
  if command -v curl >/dev/null 2>&1 && curl -fsI --max-time 2 "${READY_URL}" >/dev/null 2>&1; then
    log "frontend dev ready pid=${new_pid} url=http://${HOST}:${PORT}/"
    exit 0
  fi
  sleep 1
done

log "frontend dev did not become ready in time"
tail -n 120 "${LOGFILE}" 2>/dev/null || true
exit 1
