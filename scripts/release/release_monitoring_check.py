#!/usr/bin/env python3
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

out = Path(os.environ.get("RELEASE_ARTIFACTS", "artifacts/release/frontend-pilot-readiness"))
url = os.environ.get("RELEASE_HEALTH_URL", "http://127.0.0.1:18087/web/health")
started = time.monotonic()
with urllib.request.urlopen(url, timeout=10) as response:
    status = response.status
latency_ms = round((time.monotonic() - started) * 1000)
manifest = out / "backup/manifest.json"
backup_age_seconds = None
if manifest.exists():
    payload = json.loads(manifest.read_text())
    backup_age_seconds = max(0, int(time.time() - datetime.fromisoformat(payload["finished_at"].replace("Z", "+00:00")).timestamp()))
report = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "checks": {
        "runtime_health": {"status": status, "latency_ms": latency_ms, "pass": status == 200},
        "backup_age": {"seconds": backup_age_seconds, "threshold_seconds": 86400, "pass": backup_age_seconds is not None and backup_age_seconds <= 86400},
    },
}
report["pass"] = all(item["pass"] for item in report["checks"].values())
out.mkdir(parents=True, exist_ok=True)
(out / "monitoring-check.json").write_text(json.dumps(report, indent=2) + "\n")
print(f"[release.monitoring] {'PASS' if report['pass'] else 'FAIL'} latency_ms={latency_ms} backup_age_seconds={backup_age_seconds}")
if not report["pass"]:
    raise SystemExit(1)
