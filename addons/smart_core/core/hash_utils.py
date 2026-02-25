# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json


def stable_fingerprint(obj: dict) -> str:
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.md5(payload.encode("utf-8")).hexdigest()
