#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PORT="${VITE_DEV_PORT:-5174}"
HOST="${VITE_DEV_HOST:-127.0.0.1}"
PIDFILE="${FRONTEND_DEV_PIDFILE:-/tmp/sc-frontend-dev.pid}"
LOGFILE="${FRONTEND_DEV_LOGFILE:-/tmp/sc-frontend-dev.log}"
READY_URL="${FRONTEND_DEV_READY_URL:-http://${HOST}:${PORT}/}"
NVM_SH="${NVM_SH:-$HOME/.nvm/nvm.sh}"
TMUX_SESSION="${FRONTEND_DEV_TMUX_SESSION:-sc-frontend-dev}"

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

log "start frontend dev host=${HOST} port=${PORT}"
cd "${ROOT_DIR}"
rm -f "${LOGFILE}"
if ! command -v tmux >/dev/null 2>&1; then
  log "tmux is required for stable frontend dev runtime"
  exit 1
fi

tmux new-session -d -s "${TMUX_SESSION}" "bash -lc 'source \"${NVM_SH}\" >/dev/null 2>&1 && nvm use 20 >/dev/null && cd \"${ROOT_DIR}\" && exec pnpm -C frontend/apps/web dev --host \"${HOST}\" --port \"${PORT}\" > \"${LOGFILE}\" 2>&1'"
sleep 1
new_pid="$(tmux list-panes -t "${TMUX_SESSION}" -F '#{pane_pid}' 2>/dev/null | head -n 1)"
echo "${new_pid:-tmux:${TMUX_SESSION}}" > "${PIDFILE}"

for _ in $(seq 1 60); do
  if ! tmux has-session -t "${TMUX_SESSION}" 2>/dev/null; then
    log "frontend dev exited unexpectedly"
    tail -n 120 "${LOGFILE}" 2>/dev/null || true
    exit 1
  fi
  if command -v curl >/dev/null 2>&1 && curl -fsI --max-time 2 "${READY_URL}" >/dev/null 2>&1; then
    current_pid="$(tmux list-panes -t "${TMUX_SESSION}" -F '#{pane_pid}' 2>/dev/null | head -n 1)"
    log "frontend dev ready pid=${current_pid:-unknown} session=${TMUX_SESSION} url=http://${HOST}:${PORT}/"
    exit 0
  fi
  sleep 1
done

log "frontend dev did not become ready in time"
tail -n 120 "${LOGFILE}" 2>/dev/null || true
exit 1
