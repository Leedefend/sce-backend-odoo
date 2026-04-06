# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List


def build_capability_matrix_projection(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    list_rows: List[Dict[str, Any]] = []
    by_domain: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    by_tier: Dict[str, int] = {}
    for row in rows:
        identity = row.get("identity") if isinstance(row, dict) else {}
        if not isinstance(identity, dict):
            continue
        key = str(identity.get("key") or "").strip()
        if not key:
            continue
        domain = str(identity.get("domain") or "unknown").strip() or "unknown"
        lifecycle = row.get("lifecycle") if isinstance(row.get("lifecycle"), dict) else {}
        release = row.get("release") if isinstance(row.get("release"), dict) else {}
        status = str((lifecycle or {}).get("status") or "ga").strip() or "ga"
        tier = str((release or {}).get("tier") or "standard").strip() or "standard"
        by_domain[domain] = int(by_domain.get(domain) or 0) + 1
        by_status[status] = int(by_status.get(status) or 0) + 1
        by_tier[tier] = int(by_tier.get(tier) or 0) + 1
        list_rows.append({"key": key, "domain": domain, "status": status, "tier": tier})
    return {
        "total": len(list_rows),
        "by_domain": by_domain,
        "by_status": by_status,
        "by_tier": by_tier,
        "rows": list_rows,
    }
