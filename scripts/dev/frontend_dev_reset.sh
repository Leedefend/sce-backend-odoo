#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PORT="${VITE_DEV_PORT:-5174}"
HOST="${VITE_DEV_HOST:-127.0.0.1}"
FRONTEND_PROFILE="${FRONTEND_PROFILE:-daily}"
PROXY_TARGET_DEFAULT="${VITE_API_PROXY_TARGET:-}"
PIDFILE="${FRONTEND_DEV_PIDFILE:-/tmp/sc-frontend-dev.pid}"
LOGFILE="${FRONTEND_DEV_LOGFILE:-/tmp/sc-frontend-dev.log}"
READY_URL="${FRONTEND_DEV_READY_URL:-http://${HOST}:${PORT}/}"
NVM_SH="${NVM_SH:-$HOME/.nvm/nvm.sh}"
TMUX_SESSION="${FRONTEND_DEV_TMUX_SESSION:-sc-frontend-dev}"

resolve_profile_defaults() {
  case "${FRONTEND_PROFILE}" in
    daily)
      PROFILE_DB="sc_demo"
      PROFILE_PROXY_TARGET="http://localhost:8069"
      ;;
    test)
      PROFILE_DB="sc_test"
      PROFILE_PROXY_TARGET="http://localhost:8071"
      ;;
    uat|prod-sim)
      PROFILE_DB="sc_prod_sim"
      PROFILE_PROXY_TARGET="http://localhost:18069"
      ;;
    *)
      log "unknown FRONTEND_PROFILE=${FRONTEND_PROFILE}, fallback to daily"
      FRONTEND_PROFILE="daily"
      PROFILE_DB="sc_demo"
      PROFILE_PROXY_TARGET="http://localhost:8069"
      ;;
  esac

  if [[ -n "${PROXY_TARGET_DEFAULT}" ]]; then
    PROFILE_PROXY_TARGET="${PROXY_TARGET_DEFAULT}"
  fi
}

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

stop_tmux_session_if_exists() {
  if ! command -v tmux >/dev/null 2>&1; then
    return 0
  fi
  if tmux has-session -t "${TMUX_SESSION}" 2>/dev/null; then
    log "stop previous frontend dev tmux session=${TMUX_SESSION}"
    tmux kill-session -t "${TMUX_SESSION}" 2>/dev/null || true
  fi
}

if [[ -f "${PIDFILE}" ]]; then
  old_pid="$(cat "${PIDFILE}" 2>/dev/null || true)"
  [[ -n "${old_pid:-}" ]] && log "stop previous frontend dev pid=${old_pid}"
  kill_pid_if_alive "${old_pid:-}"
fi

stop_tmux_session_if_exists
kill_existing_port_listener "${PORT}"

resolve_profile_defaults
log "start frontend dev host=${HOST} port=${PORT} profile=${FRONTEND_PROFILE} db=${PROFILE_DB} proxy=${PROFILE_PROXY_TARGET}"
cd "${ROOT_DIR}"
rm -f "${LOGFILE}"
START_CMD="cd \"${ROOT_DIR}\" && export VITE_API_PROXY_TARGET=\"${PROFILE_PROXY_TARGET}\" VITE_ODOO_DB=\"${PROFILE_DB}\" && exec pnpm -C frontend/apps/web dev --host \"${HOST}\" --port \"${PORT}\" > \"${LOGFILE}\" 2>&1"

new_pid=""
if command -v setsid >/dev/null 2>&1; then
  setsid bash -lc "${START_CMD}" >/dev/null 2>&1 < /dev/null &
  new_pid="$!"
else
  nohup bash -lc "${START_CMD}" >/dev/null 2>&1 &
  new_pid="$!"
fi

echo "${new_pid}" > "${PIDFILE}"

for _ in $(seq 1 60); do
  if command -v curl >/dev/null 2>&1 && curl -fsI --max-time 2 "${READY_URL}" >/dev/null 2>&1; then
    log "frontend dev ready pid=${new_pid:-unknown} url=http://${HOST}:${PORT}/"
    exit 0
  fi
  sleep 1
done

log "frontend dev did not become ready in time"
tail -n 120 "${LOGFILE}" 2>/dev/null || true
exit 1
