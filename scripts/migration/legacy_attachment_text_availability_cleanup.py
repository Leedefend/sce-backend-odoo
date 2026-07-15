#!/usr/bin/env python3
"""Hide legacy attachment count labels when no downloadable file exists.

Run in Odoo shell. Set APPLY=1 to write.
"""

from __future__ import annotations

import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen

from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from scripts.verify.online_capture_security import require_online_capture  # noqa: E402


APPLY = os.environ.get("APPLY") == "1"
CHECK_ONLINE = os.environ.get("CHECK_ONLINE") == "1"
ONLINE_WORKERS = int(os.environ.get("ONLINE_WORKERS") or "32")
ONLINE_TIMEOUT = float(os.environ.get("ONLINE_TIMEOUT") or "5")
ONLINE_LIMIT = int(os.environ.get("ONLINE_LIMIT") or "0")
ONLINE_BASE = os.environ.get("SC_ONLINE_LEGACY_BASE_URL") or os.environ.get("SCBSLY_BASE_URL", "")
ATTACHMENT_LABEL_RE = re.compile(r"^附件\([1-9]\d*\)$")

SPECS = {
    "sc.legacy.self.funding.fact": {
        "table": "sc_legacy_self_funding_fact",
        "ref_fields": ("legacy_record_id", "legacy_header_id", "legacy_pid", "document_no"),
    },
    "sc.legacy.supplier.contract.pricing.fact": {
        "table": "sc_legacy_supplier_contract_pricing_fact",
        "ref_fields": ("legacy_contract_id", "contract_no", "document_no"),
    },
}


def clean(value):
    return str(value or "").strip()


def online_has_file(ref: str) -> bool:
    if not ref:
        return False
    url = f"{ONLINE_BASE.rstrip('/')}/api/System/FileApi/GetFileByBillId?BillId={ref}"
    try:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=ONLINE_TIMEOUT) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return False
    rows = payload.get("Data") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return False
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("DEL") or "0") not in ("0", "False", "false", ""):
            continue
        if clean(row.get("ATTR_PATH")):
            return True
    return False


def online_hits(refs: set[str]) -> set[str]:
    require_online_capture(("scbsly",))
    hits: set[str] = set()
    checked = 0
    failed = 0
    ref_values = sorted(refs)
    if ONLINE_LIMIT > 0:
        ref_values = ref_values[:ONLINE_LIMIT]
    with ThreadPoolExecutor(max_workers=ONLINE_WORKERS) as pool:
        future_map = {pool.submit(online_has_file, ref): ref for ref in ref_values}
        for future in as_completed(future_map):
            ref = future_map[future]
            checked += 1
            try:
                if future.result():
                    hits.add(ref)
            except Exception:
                failed += 1
                continue
    return hits, checked, failed


def file_index_hits(refs: set[str]) -> set[str]:
    if not refs or "sc.legacy.file.index" not in env:  # noqa: F821
        return set()
    FileIndex = env["sc.legacy.file.index"].sudo().with_context(active_test=False)  # noqa: F821
    hits: set[str] = set()
    ref_list = sorted(refs)
    for index in range(0, len(ref_list), 800):
        chunk = ref_list[index:index + 800]
        rows = FileIndex.search_read(
            [
                ("active", "=", True),
                "|",
                "|",
                "|",
                "|",
                ("bill_id", "in", chunk),
                ("legacy_pid", "in", chunk),
                ("business_id", "in", chunk),
                ("legacy_file_id", "in", chunk),
                ("legacy_file_key", "in", chunk),
            ],
            ["bill_id", "legacy_pid", "business_id", "legacy_file_id", "legacy_file_key"],
        )
        for row in rows:
            for field in ("bill_id", "legacy_pid", "business_id", "legacy_file_id", "legacy_file_key"):
                value = clean(row.get(field))
                if value in refs:
                    hits.add(value)
    return hits


report = {"apply": APPLY, "models": {}}

for model_name, spec in SPECS.items():
    if model_name not in env:  # noqa: F821
        continue
    Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
    records = Model.search([("attachment_text", "=like", "附件(%)")])
    rows = []
    all_refs: set[str] = set()
    for rec in records:
        if not ATTACHMENT_LABEL_RE.match(clean(rec.attachment_text)):
            continue
        refs = []
        for field in spec["ref_fields"]:
            value = clean(getattr(rec, field, ""))
            if value:
                refs.append(value)
                all_refs.add(value)
        rows.append((rec, list(dict.fromkeys(refs))))

    local_hits = file_index_hits(all_refs)
    if CHECK_ONLINE:
        remote_hits, online_checked, online_failed = online_hits(all_refs - local_hits)
    else:
        remote_hits, online_checked, online_failed = set(), 0, 0
    usable_refs = local_hits | remote_hits
    to_clear = [rec for rec, refs in rows if not any(ref in usable_refs for ref in refs)]
    clear_ids = {rec.id for rec in to_clear}

    if APPLY and to_clear:
        for index in range(0, len(to_clear), 500):
            Model.browse([rec.id for rec in to_clear[index:index + 500]]).write({"attachment_text": False})
        env.cr.commit()  # noqa: F821

    report["models"][model_name] = {
        "candidate_rows": len(rows),
        "candidate_refs": len(all_refs),
        "local_hit_refs": len(local_hits),
        "online_hit_refs": len(remote_hits),
        "online_check_enabled": CHECK_ONLINE,
        "online_checked_refs": online_checked,
        "online_failed_refs": online_failed,
        "online_limit_refs": ONLINE_LIMIT,
        "online_timeout_seconds": ONLINE_TIMEOUT,
        "kept_rows": len(rows) - len(to_clear),
        "cleared_rows": len(to_clear),
        "sample_cleared": [
            {
                "id": rec.id,
                "document_no": clean(getattr(rec, "document_no", "")),
                "refs": refs,
            }
            for rec, refs in [(rec, refs) for rec, refs in rows if rec.id in clear_ids][:20]
        ],
    }

print(json.dumps(report, ensure_ascii=False, indent=2))
