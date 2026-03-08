#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROFILE_FILE = ROOT / "docs" / "product" / "role_navigation_profile_v1.json"


def main() -> int:
    if not PROFILE_FILE.is_file():
        raise SystemExit(f"[FAIL] missing file: {PROFILE_FILE}")
    payload = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    roles = payload.get("roles") if isinstance(payload.get("roles"), list) else []
    if not roles:
        raise SystemExit("[FAIL] role navigation profile has no roles")
    missing = []
    for row in roles:
        role_key = str((row or {}).get("role_key") or "").strip()
        for scene in (row or {}).get("missing_scenes") or []:
            s = str(scene or "").strip()
            if s:
                missing.append(f"{role_key}:{s}")
    if missing:
        raise SystemExit(f"[FAIL] role navigation missing scenes: {', '.join(sorted(set(missing))[:16])}")
    print(f"[PASS] role scene navigation guard roles={len(roles)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
