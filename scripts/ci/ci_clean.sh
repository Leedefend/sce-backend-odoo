#!/usr/bin/env bash
set -euo pipefail
source scripts/common/compose.sh
compose_ci down -v --remove-orphans || true
