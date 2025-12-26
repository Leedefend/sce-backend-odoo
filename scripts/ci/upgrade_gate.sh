#!/usr/bin/env bash
set -euo pipefail
source scripts/common/env.sh
source scripts/common/compose.sh

compose_ci down -v --remove-orphans >/dev/null 2>&1 || true

# phase1: install
compose_ci run --rm -T odoo \
  -d "$DB_CI" \
  -i "$MODULE" \
  --without-demo=all \
  --stop-after-init

# phase2: upgrade + essential tests
compose_ci run --rm -T odoo \
  -d "$DB_CI" \
  -u "$MODULE" \
  --test-enable \
  --test-tags "/$MODULE:post_install,/$MODULE:sc_upgrade,/$MODULE:sc_gate,/$MODULE:sc_perm" \
  --stop-after-init

compose_ci down -v --remove-orphans >/dev/null 2>&1 || true
