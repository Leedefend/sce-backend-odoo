#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"
artifacts="${CANDIDATE_ARTIFACTS:-artifacts/release/immutable-production-candidate-v1}"
mkdir -p "$artifacts"
project="${COMPOSE_PROJECT_NAME:?COMPOSE_PROJECT_NAME is required}"
configured_image="${ODOO_IMAGE:-unknown}"
containers="$(docker ps --filter "label=com.docker.compose.project=$project" --format '{{.Names}}|{{.Image}}|{{.ID}}|{{.Status}}|{{.Ports}}')"
image_id=""
if docker image inspect "$configured_image" >/dev/null 2>&1; then
  image_id="$(docker image inspect "$configured_image" --format '{{.Id}}')"
fi

PROJECT="$project" CONFIGURED_IMAGE="$configured_image" IMAGE_ID="$image_id" CONTAINERS="$containers" \
SOURCE_SHA="$(git rev-parse HEAD)" python3 - <<'PY'
import json, os
from datetime import datetime, timezone
from pathlib import Path

rows = []
for line in os.environ.get("CONTAINERS", "").splitlines():
    if not line:
        continue
    name, image, container_id, status, ports = (line.split("|", 4) + [""] * 5)[:5]
    rows.append({"name": name, "image": image, "container_id": container_id, "status": status, "ports": ports})
payload = {
    "schema_version": 1,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "mode": "production_readonly",
    "production_database_write_count": 0,
    "compose_project": os.environ["PROJECT"],
    "configured_backend_image": os.environ["CONFIGURED_IMAGE"],
    "configured_image_id": os.environ.get("IMAGE_ID") or None,
    "running_containers": rows,
    "runtime_available": bool(rows),
    "collector_source_sha": os.environ["SOURCE_SHA"],
    "unavailable_fields": [] if rows else [
        "backend_source_sha", "frontend_build_hash", "running_image_digest", "runtime_versions",
        "module_versions", "pending_modules", "demo_module_state", "database_size",
        "filestore_fingerprint", "paired_backup", "tls", "renewal", "public_ports",
        "database_selector", "health",
    ],
}
out = Path(os.environ.get("CANDIDATE_ARTIFACTS", "artifacts/release/immutable-production-candidate-v1"))
(out / "production-readonly-baseline.json").write_text(json.dumps(payload, indent=2) + "\n")
print(f"[production.baseline] runtime_available={payload['runtime_available']} writes=0")
PY
