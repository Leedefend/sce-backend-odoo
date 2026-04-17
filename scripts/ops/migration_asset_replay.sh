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

guard_prod_forbid

: "${DB_NAME:?DB_NAME is required}"
PROTECTED_DB_NAME="${PROTECTED_DB_NAME:-sc_demo}"

if [[ "$DB_NAME" == "$PROTECTED_DB_NAME" ]]; then
  echo "[migration.assets.replay] REFUSE protected database: DB_NAME=$DB_NAME" >&2
  echo "[migration.assets.replay] Use a temporary database for fresh rebuild validation." >&2
  exit 2
fi

ASSET_ROOT="${ASSET_ROOT:-migration_assets}"
CONTAINER_ASSET_ROOT="${CONTAINER_ASSET_ROOT:-/tmp/migration_assets}"
HOST_ASSET_ROOT="$ROOT_DIR/$ASSET_ROOT"

if [[ ! -d "$HOST_ASSET_ROOT" ]]; then
  echo "[migration.assets.replay] missing asset root: $HOST_ASSET_ROOT" >&2
  exit 2
fi

ODOO_CID="$(compose_dev ps -q odoo | head -n 1)"
if [[ -z "$ODOO_CID" ]]; then
  echo "[migration.assets.replay] odoo container is not running" >&2
  exit 2
fi

echo "[migration.assets.replay] db=${DB_NAME} asset_root=${ASSET_ROOT}"
python3 "$ROOT_DIR/scripts/migration/migration_asset_catalog_verify.py" \
  --asset-root "$HOST_ASSET_ROOT" \
  --catalog "$HOST_ASSET_ROOT/manifest/migration_asset_catalog_v1.json" \
  --check >/dev/null

docker exec -u 0 "$ODOO_CID" rm -rf "$CONTAINER_ASSET_ROOT"
docker cp "$HOST_ASSET_ROOT" "$ODOO_CID:$CONTAINER_ASSET_ROOT"

compose_dev exec -T \
  -e MIGRATION_ASSET_ROOT="$CONTAINER_ASSET_ROOT" \
  -e MIGRATION_ASSET_MODULE="${MIGRATION_ASSET_MODULE:-migration_assets}" \
  -e MIGRATION_ASSET_BATCH_SIZE="${MIGRATION_ASSET_BATCH_SIZE:-1000}" \
  odoo \
  odoo shell \
  --config="$ODOO_CONF" \
  -d "$DB_NAME" \
  < "$ROOT_DIR/scripts/migration/migration_asset_replay.py"
