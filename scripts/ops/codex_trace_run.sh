#!/usr/bin/env bash
set -o pipefail

# Codex Trace Mode is a sidecar observation wrapper. By default it runs Codex;
# tests may pass a harmless command such as `true` to validate log creation.

DATE=$(date +%Y-%m-%d)
TIME=$(date +%H%M%S)

BASE_DIR="artifacts/codex_trace/$DATE"
LOG_FILE="$BASE_DIR/session_$TIME.log"
LATEST_LINK="artifacts/codex_trace/latest.log"

mkdir -p "$BASE_DIR"

echo "[Codex Trace Mode]"
echo "Date: $DATE"
echo "Time: $TIME"
echo "Log:  $LOG_FILE"
echo "-------------------------------------"

if [ "$#" -gt 0 ]; then
  "$@" | tee "$LOG_FILE"
else
  codex | tee "$LOG_FILE"
fi
STATUS=${PIPESTATUS[0]}

ln -sfn "$DATE/session_$TIME.log" "$LATEST_LINK"

echo "-------------------------------------"
echo "[Trace Saved]"
echo "$LOG_FILE"

exit "$STATUS"
