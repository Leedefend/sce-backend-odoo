# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json

SOURCE_KIND = "stable_hash_utility"
SOURCE_AUTHORITIES = ("json_payload", "hashlib.md5")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict:
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "rebuildable": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "runtime_carrier": "hash_utils",
    }


def stable_fingerprint(obj: dict) -> str:
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.md5(payload.encode("utf-8")).hexdigest()
