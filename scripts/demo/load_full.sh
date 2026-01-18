#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

: "${DB_NAME:?DB_NAME is required}"

guard_prod_forbid

printf '[demo.load.full] db=%s\n' "$DB_NAME"

bash "$ROOT_DIR/scripts/demo/load_all.sh"

printf '[demo.load.full] seed demo_full\n'
PROFILE=demo_full DB_NAME="$DB_NAME" bash "$ROOT_DIR/scripts/seed/run.sh"
