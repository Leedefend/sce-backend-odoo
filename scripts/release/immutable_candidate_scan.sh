#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"
artifacts="${CANDIDATE_ARTIFACTS:-artifacts/release/immutable-production-candidate-v1}"
manifest="$artifacts/image-manifest.json"
[[ -f "$manifest" ]] || { echo "[candidate.scan] image manifest missing" >&2; exit 2; }
image="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["image"])' "$manifest")"
mkdir -p "$artifacts/trivy-cache"

docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  anchore/syft:v1.27.1 "$image" -o cyclonedx-json > "$artifacts/sbom.cyclonedx.json"

set +e
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$root/$artifacts/trivy-cache:/root/.cache/" \
  aquasec/trivy:0.63.0 image --format json --scanners vuln,secret \
  --severity HIGH,CRITICAL --ignore-unfixed=false --timeout 30m --skip-version-check \
  "$image" > "$artifacts/trivy.json"
trivy_status=$?
set -e
[[ "$trivy_status" -eq 0 ]] || { echo "[candidate.scan] trivy execution failed" >&2; exit "$trivy_status"; }

TRIVY_REPORT="$artifacts/trivy.json" SCAN_SUMMARY="$artifacts/security-summary.json" python3 - <<'PY'
import json, os
from pathlib import Path

report = json.loads(Path(os.environ["TRIVY_REPORT"]).read_text())
counts = {"CRITICAL": 0, "HIGH": 0, "SECRET": 0}
for result in report.get("Results") or []:
    for vuln in result.get("Vulnerabilities") or []:
        severity = str(vuln.get("Severity") or "").upper()
        if severity in counts:
            counts[severity] += 1
    counts["SECRET"] += len(result.get("Secrets") or [])
payload = {"schema_version": 1, "counts": counts, "pass": all(value == 0 for value in counts.values())}
Path(os.environ["SCAN_SUMMARY"]).write_text(json.dumps(payload, indent=2) + "\n")
print("[candidate.scan] " + json.dumps(payload, separators=(",", ":")))
if not payload["pass"]:
    raise SystemExit(1)
PY
