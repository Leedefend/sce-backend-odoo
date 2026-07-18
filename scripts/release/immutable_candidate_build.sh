#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"

source_sha="${CANDIDATE_SOURCE_SHA:?CANDIDATE_SOURCE_SHA is required}"
if [[ "$(git rev-parse origin/main)" != "$source_sha" ]]; then
  echo "[candidate.build] origin/main no longer matches locked source SHA" >&2
  exit 2
fi
if git diff --quiet "$source_sha" -- addons addons_external frontend requirements-odoo.txt config/odoo.conf.template scripts/odoo-entrypoint.sh scripts/render_odoo_conf.py; then
  :
else
  echo "[candidate.build] product/runtime files differ from locked source SHA" >&2
  git diff --name-only "$source_sha" -- addons addons_external frontend requirements-odoo.txt config/odoo.conf.template scripts/odoo-entrypoint.sh scripts/render_odoo_conf.py >&2
  exit 2
fi

artifacts="${CANDIDATE_ARTIFACTS:-artifacts/release/immutable-production-candidate-v1}"
dist="frontend/apps/web/dist-production-candidate"
short_sha="${source_sha:0:12}"
image="${CANDIDATE_IMAGE:-sce-production-candidate:${short_sha}}"
build_time="${CANDIDATE_BUILD_TIME:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
node_version="$(node --version)"
pnpm_version="$(scripts/dev/pnpm_exec.sh --version)"
python_version="$(docker run --rm --entrypoint python3 odoo:17.0 --version | awk '{print $2}')"

mkdir -p "$artifacts"
rm -rf "$dist"
VITE_ODOO_DB=sc_user_data_rehearsal_candidate \
VITE_ODOO_DB_LOCKED=1 \
VITE_APP_ENV=production \
VITE_BUILD_MODE=production \
VITE_BUILD_OUT_DIR="$root/$dist" \
  scripts/dev/pnpm_exec.sh -C frontend/apps/web exec vite build --mode production

frontend_hash="$(find "$dist" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')"
printf '%s\n' "$frontend_hash" > "$artifacts/frontend-build.sha256"

docker build \
  --file Dockerfile.production-candidate \
  --tag "$image" \
  --build-arg "SOURCE_SHA=$source_sha" \
  --build-arg "FRONTEND_BUILD_SHA256=$frontend_hash" \
  --build-arg "BUILD_TIME=$build_time" \
  --build-arg "PYTHON_VERSION=$python_version" \
  --build-arg "NODE_VERSION=$node_version" \
  --build-arg "PNPM_VERSION=$pnpm_version" \
  .

image_id="$(docker image inspect "$image" --format '{{.Id}}')"
odoo_version="$(docker run --rm --entrypoint odoo "$image" --version | head -1)"
image_python="$(docker run --rm --entrypoint python3 "$image" --version | awk '{print $2}')"
archive="$artifacts/candidate-image.tar"
docker save --output "$archive" "$image"
archive_sha="$(sha256sum "$archive" | awk '{print $1}')"

IMAGE="$image" IMAGE_ID="$image_id" SOURCE_SHA="$source_sha" FRONTEND_HASH="$frontend_hash" \
BUILD_TIME="$build_time" ODOO_VERSION="$odoo_version" PYTHON_VERSION="$image_python" \
NODE_VERSION="$node_version" PNPM_VERSION="$pnpm_version" ARCHIVE_SHA="$archive_sha" \
python3 - <<'PY'
import json, os
from pathlib import Path

out = Path(os.environ.get("CANDIDATE_ARTIFACTS", "artifacts/release/immutable-production-candidate-v1"))
payload = {
    "schema_version": 1,
    "source_sha": os.environ["SOURCE_SHA"],
    "image": os.environ["IMAGE"],
    "image_id": os.environ["IMAGE_ID"],
    "image_digest": os.environ["IMAGE_ID"],
    "frontend_build_sha256": os.environ["FRONTEND_HASH"],
    "build_time": os.environ["BUILD_TIME"],
    "versions": {
        "odoo": os.environ["ODOO_VERSION"],
        "python": os.environ["PYTHON_VERSION"],
        "node": os.environ["NODE_VERSION"],
        "pnpm": os.environ["PNPM_VERSION"],
    },
    "archive": "candidate-image.tar",
    "archive_sha256": os.environ["ARCHIVE_SHA"],
    "contains": ["odoo_backend", "production_frontend_static", "formal_addons", "python_dependencies", "startup_configuration", "nginx"],
    "host_source_mounts": 0,
}
(out / "image-manifest.json").write_text(json.dumps(payload, indent=2) + "\n")
PY

docker image rm "$image" >/dev/null
docker load --input "$archive" >/dev/null
reloaded_id="$(docker image inspect "$image" --format '{{.Id}}')"
if [[ "$reloaded_id" != "$image_id" ]]; then
  echo "[candidate.build] immutable reload image ID mismatch" >&2
  exit 1
fi
printf '%s\n' "$reloaded_id" > "$artifacts/reloaded-image-id.txt"
echo "[candidate.build] PASS image=$image digest=$image_id frontend=$frontend_hash"
