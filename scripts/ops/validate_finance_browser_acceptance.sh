#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARTIFACT_DIR="${FINANCE_BROWSER_ARTIFACT_DIR:-${ROOT_DIR}/artifacts/finance-browser-handling/current}"
mkdir -p "$ARTIFACT_DIR"
chmod 0777 "$ARTIFACT_DIR"
rm -f "$ARTIFACT_DIR"/summary.json "$ARTIFACT_DIR"/summary.md "$ARTIFACT_DIR"/error.json

resolve_browser() {
  if [[ -n "${CHROMIUM_EXECUTABLE_PATH:-}" && -x "${CHROMIUM_EXECUTABLE_PATH}" ]]; then
    printf '%s\n' "$CHROMIUM_EXECUTABLE_PATH"
    return 0
  fi
  if [[ -n "${PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH:-}" && -x "${PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH}" ]]; then
    printf '%s\n' "$PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"
    return 0
  fi
  local candidate
  for candidate in google-chrome-stable google-chrome chromium chromium-browser; do
    if command -v "$candidate" >/dev/null 2>&1; then
      command -v "$candidate"
      return 0
    fi
  done
  (
    cd "$ROOT_DIR"
    node <<'NODE'
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const requireBase = fs.existsSync(path.join(process.cwd(), 'frontend/apps/web/package.json'))
  ? path.join(process.cwd(), 'frontend/apps/web/package.json')
  : path.join(process.cwd(), 'package.json');
const requireFromRoot = createRequire(requireBase);
try {
  const { chromium } = requireFromRoot('playwright');
  const executablePath = chromium.executablePath();
  if (executablePath && fs.existsSync(executablePath)) {
    console.log(executablePath);
    process.exit(0);
  }
} catch (err) {
  // Browser runtime is an environment prerequisite; do not install here.
}
process.exit(1);
NODE
  )
}

if ! BROWSER_PATH="$(resolve_browser)"; then
  cat >&2 <<'EOF'
FINANCE_BROWSER_ACCEPTANCE=ENV_MISSING
Missing Chromium/Chrome runtime for browser acceptance.
Set CHROMIUM_EXECUTABLE_PATH or PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH to a preinstalled browser, or prepare the environment outside this validation command.
This validation intentionally does not run `playwright install` and does not mutate test data when the browser runtime is missing.
EOF
  exit 12
fi

DB_NAME="${DB_NAME:?}" bash "$ROOT_DIR/scripts/ops/odoo_shell_exec.sh" < "$ROOT_DIR/scripts/verify/finance_handling_browser_setup.py"
(
  cd "$ROOT_DIR"
  CHROMIUM_EXECUTABLE_PATH="$BROWSER_PATH" FINANCE_BROWSER_ARTIFACT_DIR="$ARTIFACT_DIR" FRONTEND_URL="${FRONTEND_URL:-http://localhost:18081}" DB_NAME="${DB_NAME:?}" node "$ROOT_DIR/scripts/verify/finance_handling_browser_acceptance.js"
)

echo "FINANCE_BROWSER_ACCEPTANCE=PASS"
echo "ARTIFACT_DIR=$ARTIFACT_DIR"
