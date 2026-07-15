#!/usr/bin/env python3
import json
from pathlib import Path

root = Path("artifacts/release/frontend-pilot-readiness/fingerprints")
before = json.loads((root / "pre.json").read_text())
after = json.loads((root / "post.json").read_text())
for value in (before, after):
    value.pop("generated_at", None)
if before != after:
    raise SystemExit("[release.fingerprint] FAIL unexpected upgrade drift")
print("[release.fingerprint] PASS pre/post counts, modules and filestore are identical")
