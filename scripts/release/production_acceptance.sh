#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"
out="artifacts/release/frontend-pilot-readiness"
mkdir -p "$out"
export VITE_ODOO_DB=sc_frontend_acceptance VITE_ODOO_DB_LOCKED=1 VITE_APP_ENV=acceptance
scripts/dev/pnpm_exec.sh -C frontend/apps/web exec vite build --outDir dist-release
find frontend/apps/web/dist-release -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' > "$out/frontend-build.sha256"
export FRONTEND_ACCEPTANCE_MODE=production
export FRONTEND_ACCEPTANCE_STATIC_DIST="$root/frontend/apps/web/dist-release"
export FRONTEND_URL=http://127.0.0.1:5175
make --no-print-directory verify.frontend.fixture.browser
make --no-print-directory verify.frontend.navigation.access
make --no-print-directory verify.frontend.financial_workspace.browser
make --no-print-directory verify.frontend.my_work_approval.browser
make --no-print-directory verify.frontend.delivery_hardening.browser
python3 scripts/release/release_acceptance_report.py
