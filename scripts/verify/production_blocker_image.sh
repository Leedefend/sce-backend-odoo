#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"

image="${BLOCKER_RUNTIME_IMAGE:-sce-blocker-runtime:test}"
image_a="${image%:*}:repro-a"
image_b="${image%:*}:repro-b"
artifacts="${BLOCKER_IMAGE_ARTIFACTS:-artifacts/production-blocker/image}"
frontend_dist="$artifacts/frontend-dist"
trivy_cache="$artifacts/trivy-cache"
source_sha="$(git rev-parse HEAD)"
mkdir -p "$artifacts" "$trivy_cache"

scripts/dev/pnpm_exec.sh -C frontend/packages/design-tokens build
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod VITE_ODOO_DB=sc_prod \
  VITE_APP_ENV=production FRONTEND_DIST_DIR="$frontend_dist" \
  bash scripts/dev/frontend_static_build.sh
frontend_sha="$(cd "$frontend_dist" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')"
printf '%s\n' "$frontend_sha" > "$artifacts/frontend-build.sha256"

build_image() {
  local tag="$1"
  docker build --pull --no-cache \
    --build-arg "SOURCE_SHA=$source_sha" \
    --build-arg "FRONTEND_BUILD_SHA256=$frontend_sha" \
    --build-arg VITE_ODOO_DB=sc_prod \
    --build-arg VITE_APP_ENV=production \
    -t "$tag" .
}

build_image "$image_a"
build_image "$image_b"
docker tag "$image_b" "$image"

for suffix in a b; do
  tag_var="image_$suffix"
  tag="${!tag_var}"
  docker image inspect "$tag" > "$artifacts/image-$suffix-inspect.json"
  docker run --rm --entrypoint sh "$tag" -c \
    "dpkg-query -W -f='\${Package}|\${Version}\n' | sort" > "$artifacts/image-$suffix-apt-packages.txt"
  docker run --rm --entrypoint python3 "$tag" -m pip freeze --all \
    | sort > "$artifacts/image-$suffix-python-packages.txt"
  docker run --rm --entrypoint sh "$tag" -c \
    '! command -v node && ! command -v npm && ! command -v lessc && ! command -v rtlcss && ! dpkg-query -W "node-*" "libnode*" 2>/dev/null'
  internal_frontend_sha="$(docker run --rm --entrypoint sh "$tag" -c 'cat /opt/sce/frontend/.build-sha256')"
  label_frontend_sha="$(docker image inspect "$tag" --format '{{index .Config.Labels "io.sce.frontend.sha256"}}')"
  label_source_sha="$(docker image inspect "$tag" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')"
  [[ "$internal_frontend_sha" == "$frontend_sha" && "$label_frontend_sha" == "$frontend_sha" ]]
  [[ "$label_source_sha" == "$source_sha" ]]
  docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    anchore/syft:v1.27.1 "$tag" -o json > "$artifacts/image-$suffix-sbom.json"
  jq -S '[.artifacts[] | {name, version, type, purl}] | sort_by(.type, .name, .version, .purl)' \
    "$artifacts/image-$suffix-sbom.json" > "$artifacts/image-$suffix-sbom-core.json"
done

cmp "$artifacts/image-a-apt-packages.txt" "$artifacts/image-b-apt-packages.txt"
cmp "$artifacts/image-a-python-packages.txt" "$artifacts/image-b-python-packages.txt"
cmp "$artifacts/image-a-sbom-core.json" "$artifacts/image-b-sbom-core.json"

docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$(realpath "$trivy_cache"):/root/.cache" aquasec/trivy:0.63.0 image \
  --format json --scanners vuln,secret --severity HIGH,CRITICAL \
  --ignore-unfixed=false --timeout 30m --skip-version-check "$image" \
  > "$artifacts/trivy.json"

jq -e '
  ([.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length) == 0 and
  ([.Results[]?.Vulnerabilities[]? | select(.Severity == "HIGH")] | length) == 0 and
  ([.Results[]?.Secrets[]?] | length) == 0
' "$artifacts/trivy.json" >/dev/null

before_save_id="$(docker image inspect "$image_a" --format '{{.Id}}')"
docker save "$image_a" -o "$artifacts/image-reload.tar"
docker image rm "$image_a" >/dev/null
docker load -i "$artifacts/image-reload.tar" > "$artifacts/image-reload.log"
after_load_id="$(docker image inspect "$image_a" --format '{{.Id}}')"
[[ "$before_save_id" == "$after_load_id" ]]

SOURCE_SHA="$source_sha" FRONTEND_SHA="$frontend_sha" IMAGE="$image" \
IMAGE_A="$image_a" IMAGE_B="$image_b" BEFORE_SAVE_ID="$before_save_id" \
AFTER_LOAD_ID="$after_load_id" ARTIFACTS="$artifacts" python3 - <<'PY'
import datetime
import hashlib
import json
import os
import subprocess
from pathlib import Path

artifacts = Path(os.environ["ARTIFACTS"])

def command(*args):
    return subprocess.check_output(args, text=True).strip()

def file_sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

scan = json.loads((artifacts / "trivy.json").read_text())
payload = {
    "schema_version": 1,
    "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "source_sha": os.environ["SOURCE_SHA"],
    "frontend_build_sha256": os.environ["FRONTEND_SHA"],
    "base_images": {
        "odoo": "odoo:17.0@sha256:f88f646a0f5fc0b225995ee28953d9ce7367cc731b1756765114691fb97d18e5",
        "node_builder": "node:22.17.0-bookworm-slim@sha256:b04ce4ae4e95b522112c2e5c52f781471a5cbc3b594527bcddedee9bc48c03a0",
    },
    "images": {
        "candidate": command("docker", "image", "inspect", os.environ["IMAGE"], "--format", "{{.Id}}"),
        "repro_a": command("docker", "image", "inspect", os.environ["IMAGE_A"], "--format", "{{.Id}}"),
        "repro_b": command("docker", "image", "inspect", os.environ["IMAGE_B"], "--format", "{{.Id}}"),
    },
    "reproducibility": {
        "binary_image_id_equal": command("docker", "image", "inspect", os.environ["IMAGE_A"], "--format", "{{.Id}}") == command("docker", "image", "inspect", os.environ["IMAGE_B"], "--format", "{{.Id}}"),
        "apt_manifest_equal": True,
        "python_manifest_equal": True,
        "sbom_core_equal": True,
    },
    "save_remove_load": {
        "before_image_id": os.environ["BEFORE_SAVE_ID"],
        "after_image_id": os.environ["AFTER_LOAD_ID"],
        "identity_preserved": os.environ["BEFORE_SAVE_ID"] == os.environ["AFTER_LOAD_ID"],
    },
    "runtime": {"node_present": False, "rtl_policy": "unsupported_ltr_only"},
    "scan": {
        "critical": sum(1 for r in scan.get("Results", []) for v in r.get("Vulnerabilities") or [] if v.get("Severity") == "CRITICAL"),
        "high": sum(1 for r in scan.get("Results", []) for v in r.get("Vulnerabilities") or [] if v.get("Severity") == "HIGH"),
        "secret": sum(1 for r in scan.get("Results", []) for _ in r.get("Secrets") or []),
    },
    "evidence_sha256": {
        "sbom": file_sha(artifacts / "image-b-sbom.json"),
        "trivy": file_sha(artifacts / "trivy.json"),
        "apt_manifest": file_sha(artifacts / "image-b-apt-packages.txt"),
        "python_manifest": file_sha(artifacts / "image-b-python-packages.txt"),
    },
}
(artifacts / "image-summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print("[production-blocker-image] " + json.dumps(payload, sort_keys=True))
if not all([
    payload["save_remove_load"]["identity_preserved"],
    payload["reproducibility"]["apt_manifest_equal"],
    payload["reproducibility"]["python_manifest_equal"],
    payload["reproducibility"]["sbom_core_equal"],
    payload["scan"] == {"critical": 0, "high": 0, "secret": 0},
]):
    raise SystemExit(1)
PY
