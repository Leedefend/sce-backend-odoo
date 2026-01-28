#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(pwd)}"

# Workspace-owned paths (avoid read-only /home and /tmp).
CODEX_HOME_DIR="${CODEX_HOME_DIR:-$ROOT_DIR/.codex_home}"
CODEX_TMP_DIR="${CODEX_TMP_DIR:-$ROOT_DIR/.tmp/codex}"
CODEX_XDG_CACHE="${CODEX_XDG_CACHE:-$ROOT_DIR/.cache}"
CODEX_XDG_STATE="${CODEX_XDG_STATE:-$ROOT_DIR/.state}"
CODEX_XDG_CONFIG="${CODEX_XDG_CONFIG:-$ROOT_DIR/.config}"

mkdir -p "${CODEX_HOME_DIR}" "${CODEX_TMP_DIR}" "${CODEX_XDG_CACHE}" "${CODEX_XDG_STATE}" "${CODEX_XDG_CONFIG}"

export HOME="${CODEX_HOME_DIR}"
export TMPDIR="${CODEX_TMP_DIR}"
export TEMP="${CODEX_TMP_DIR}"
export TMP="${CODEX_TMP_DIR}"
export XDG_CACHE_HOME="${CODEX_XDG_CACHE}"
export XDG_STATE_HOME="${CODEX_XDG_STATE}"
export XDG_CONFIG_HOME="${CODEX_XDG_CONFIG}"

extra_dir="${CODEX_ADD_DIR:-$HOME/.codex}"
sandbox="${CODEX_SANDBOX:-workspace-write}"
approval="${CODEX_APPROVAL_POLICY:-on-failure}"

echo "[codex.cli] HOME=${HOME}"
echo "[codex.cli] TMPDIR=${TMPDIR}"

exec codex \
  --add-dir "${extra_dir}" \
  --sandbox "${sandbox}" \
  --ask-for-approval "${approval}" \
  ${CODEX_CLI_ARGS:-}
