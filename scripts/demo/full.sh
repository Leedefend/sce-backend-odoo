#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR
cd "$ROOT_DIR"

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

: "${DB_NAME:?DB_NAME is required}"

echo "[demo.full] start db=${DB_NAME}"
make demo.reset DB="$DB_NAME"
make demo.load.all DB="$DB_NAME"
make demo.verify DB="$DB_NAME"
echo "[demo.full] OK db=${DB_NAME}"
