# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json

from .source_authority import build_source_authority_contract

SOURCE_KIND = "stable_hash_utility"
SOURCE_AUTHORITIES = ("json_payload", "hashlib.md5")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        runtime_carrier="hash_utils",
    )


def stable_fingerprint(obj: dict) -> str:
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.md5(payload.encode("utf-8")).hexdigest()
