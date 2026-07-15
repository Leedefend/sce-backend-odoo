#!/usr/bin/env python3
"""Hide input-invoice attachment labels that have no accessible legacy file."""

from __future__ import annotations

import gzip
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


INPUT = Path(os.environ.get("INPUT") or "/tmp/scbs_55_old_live_full_rows_seq042_进项上报.json.gz")
APPLY = os.environ.get("APPLY") == "1"
ONLINE_CHECK = os.environ.get("ONLINE_CHECK") == "1"
ONLINE_WORKERS = int(os.environ.get("ONLINE_WORKERS") or "16")
ONLINE_LIMIT = int(os.environ.get("ONLINE_LIMIT") or "0")
sys.path.insert(0, str(Path.cwd()))
from scripts.verify.online_capture_security import require_online_capture  # noqa: E402

BASE_URL = os.environ.get("SC_ONLINE_LEGACY_BASE_URL") or os.environ.get("SCBSLY_BASE_URL", "")
EXISTING_FILE_PATHS = Path(os.environ["EXISTING_FILE_PATHS"]) if os.environ.get("EXISTING_FILE_PATHS") else None
MODEL = "sc.legacy.invoice.tax.fact"
ATTACHMENT_LABEL_RE = re.compile(r"^附件\([1-9]\d*\)$")


def clean(value: object) -> str:
    if value in (None, False):
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())
    return "" if text in {"False", "false", "None", "NULL"} else text


def load_raw_refs() -> dict[str, dict[str, Any]]:
    rows = json.load(gzip.open(INPUT, "rt", encoding="utf-8")).get("rows") or []
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        line_id = clean(row.get("Id$C_JXXP_ZYFPJJD_CB") or row.get("Id"))
        if not line_id:
            continue
        refs = [
            clean(row.get("FJ$C_JXXP_ZYFPJJD_CB")),
            clean(row.get("FJ")),
            clean(row.get("Id$C_JXXP_ZYFPJJD_CB")),
            clean(row.get("pid$C_JXXP_ZYFPJJD_CB")),
            clean(row.get("Id")),
            clean(row.get("pid")),
        ]
        result[line_id] = {
            "attachment_text": clean(row.get("f_FJ") or row.get("FJ$C_JXXP_ZYFPJJD_CB") or row.get("FJ")),
            "attachment_ref": " ".join(
                item
                for item in dict.fromkeys([clean(row.get("FJ$C_JXXP_ZYFPJJD_CB")), clean(row.get("FJ"))])
                if item
            ),
            "refs": [item for item in dict.fromkeys(refs) if item],
        }
    return result


def load_existing_file_paths() -> set[str]:
    if not EXISTING_FILE_PATHS:
        return set()
    paths = set()
    for line in EXISTING_FILE_PATHS.read_text(encoding="utf-8").splitlines():
        clean_path = clean(line)
        if clean_path:
            paths.add(clean_path)
    return paths


def has_online_file(ref: str) -> bool:
    url = f"{BASE_URL.rstrip()}/api/System/FileApi/GetFileByBillId?BillId={ref}"
    try:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, ValueError, json.JSONDecodeError):
        return False
    rows = payload.get("Data") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return False
    return any(isinstance(row, dict) and clean(row.get("ATTR_PATH")) for row in rows)


def online_hits(refs: set[str]) -> set[str]:
    if not ONLINE_CHECK or not refs:
        return set()
    require_online_capture(("scbsly",))
    candidates = sorted(refs)
    if ONLINE_LIMIT > 0:
        candidates = candidates[:ONLINE_LIMIT]
    hits: set[str] = set()
    with ThreadPoolExecutor(max_workers=ONLINE_WORKERS) as pool:
        future_refs = {pool.submit(has_online_file, ref): ref for ref in candidates}
        for future in as_completed(future_refs):
            ref = future_refs[future]
            if future.result():
                hits.add(ref)
    return hits


def file_index_hits(refs: set[str], existing_file_paths: set[str] | None = None) -> set[str]:
    if not refs or "sc.legacy.file.index" not in env:  # noqa: F821
        return set()
    FileIndex = env["sc.legacy.file.index"].sudo().with_context(active_test=False)  # noqa: F821
    hits: set[str] = set()
    ref_list = sorted(refs)
    for start in range(0, len(ref_list), 500):
        chunk = ref_list[start:start + 500]
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
            ["bill_id", "legacy_pid", "business_id", "legacy_file_id", "legacy_file_key", "file_path", "preview_path"],
        )
        for row in rows:
            if existing_file_paths:
                file_path = clean(row.get("file_path"))
                preview_path = clean(row.get("preview_path"))
                if file_path not in existing_file_paths and preview_path not in existing_file_paths:
                    continue
            for field in ("bill_id", "legacy_pid", "business_id", "legacy_file_id", "legacy_file_key"):
                value = clean(row.get(field))
                if value and value in refs:
                    hits.add(value)
    return hits


raw_by_line_id = load_raw_refs()
existing_file_paths = load_existing_file_paths()
env.cr.execute("ALTER TABLE sc_legacy_invoice_tax_fact ADD COLUMN IF NOT EXISTS attachment_ref varchar")  # noqa: F821
Model = env[MODEL].sudo().with_context(active_test=False)  # noqa: F821
env.cr.execute(  # noqa: F821
    """
    SELECT p.res_id, f.legacy_record_id, p.payload
      FROM sc_p1_legacy_visible_alias_payload p
      JOIN sc_legacy_invoice_tax_fact f ON f.id = p.res_id
     WHERE p.model = %s
       AND COALESCE(p.payload->>'附件', '') <> ''
    """,
    [MODEL],
)
payload_rows = env.cr.fetchall()  # noqa: F821

all_refs: set[str] = set()
for _res_id, legacy_record_id, _payload in payload_rows:
    all_refs.update(raw_by_line_id.get(clean(legacy_record_id), {}).get("refs") or [])
local_hits = file_index_hits(all_refs, existing_file_paths or None)
remote_hits = online_hits(all_refs - local_hits)
usable_refs = local_hits | remote_hits

to_clear: list[int] = []
to_keep: list[int] = []
backfilled = 0
for res_id, legacy_record_id, payload in payload_rows:
    raw = raw_by_line_id.get(clean(legacy_record_id), {})
    attachment_ref = clean(raw.get("attachment_ref"))
    if APPLY and attachment_ref and "attachment_ref" in Model._fields:
        rec = Model.browse(res_id)
        if clean(rec.attachment_ref) != attachment_ref:
            rec.write({"attachment_ref": attachment_ref})
            backfilled += 1
    attachment_text = clean((payload or {}).get("附件") if isinstance(payload, dict) else "")
    refs = set(raw.get("refs") or [])
    if ATTACHMENT_LABEL_RE.match(attachment_text) and not (refs & usable_refs):
        to_clear.append(res_id)
    elif attachment_text:
        to_keep.append(res_id)

if APPLY and to_clear:
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_p1_legacy_visible_alias_payload
           SET payload = jsonb_set(payload, '{附件}', '""'::jsonb, true),
               write_date = now()
         WHERE model = %s
           AND res_id = ANY(%s)
        """,
        [MODEL, to_clear],
    )

if APPLY and (to_clear or backfilled):
    env.cr.commit()  # noqa: F821

report = {
    "apply": APPLY,
    "online_check": ONLINE_CHECK,
    "raw_rows": len(raw_by_line_id),
    "payload_rows_with_attachment": len(payload_rows),
    "candidate_refs": len(all_refs),
    "existing_file_path_check": bool(existing_file_paths),
    "existing_file_paths": len(existing_file_paths),
    "local_hit_refs": len(local_hits),
    "online_hit_refs": len(remote_hits),
    "kept_rows": len(to_keep),
    "cleared_rows": len(to_clear),
    "backfilled_attachment_ref_rows": backfilled,
    "sample_cleared": to_clear[:20],
}
print(json.dumps(report, ensure_ascii=False, indent=2))
