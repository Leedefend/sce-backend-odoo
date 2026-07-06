# -*- coding: utf-8 -*-
"""Mirror missing BASE_SYSTEM_FILE legacy files from online sources.

Run through ``odoo shell``. The script does not change business records or file
index rows; it only fills missing local files referenced by sc.legacy.file.index.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from odoo.addons.smart_core.handlers.file_download import (
    _legacy_file_roots,
    _resolve_legacy_file_path,
)


LIMIT = int(os.getenv("LEGACY_BASE_SYSTEM_FILE_MIRROR_LIMIT", "0") or "0")
APPLY = os.getenv("LEGACY_BASE_SYSTEM_FILE_MIRROR_APPLY", "1").strip().lower() in {"1", "true", "yes", "on"}
DOWNLOAD_TIMEOUT = int(os.getenv("LEGACY_BASE_SYSTEM_FILE_MIRROR_DOWNLOAD_TIMEOUT", "120") or "120")
EXAMPLE_LIMIT = int(os.getenv("LEGACY_BASE_SYSTEM_FILE_MIRROR_EXAMPLE_LIMIT", "30") or "30")
OUTPUT_JSON = Path(
    os.getenv(
        "LEGACY_BASE_SYSTEM_FILE_MIRROR_OUTPUT",
        "/tmp/legacy_base_system_file_missing_mirror_result_v1.json",
    )
)
BASE_URLS = [
    item.strip().rstrip("/")
    for item in os.getenv("LEGACY_BASE_SYSTEM_FILE_MIRROR_BASE_URLS", "https://www.builderp.cn/SCBS,https://www.builderp.cn/SCBSLY_V2").split(",")
    if item.strip()
]
PREFERRED_ROOT = Path(os.getenv("LEGACY_BASE_SYSTEM_FILE_MIRROR_ROOT", "/mnt/legacy-files"))


def clean(value):
    return str(value or "").strip()


def relative_candidates(item):
    values = [clean(item.file_path), clean(item.preview_path)]
    return [value.replace("\\", "/").lstrip("/") for value in values if value]


def is_local_ok(item):
    return any(_resolve_legacy_file_path(relative) for relative in relative_candidates(item))


def writable_root():
    roots = [PREFERRED_ROOT] + [root for root in _legacy_file_roots() if root != PREFERRED_ROOT]
    for root in roots:
        try:
            root.mkdir(parents=True, exist_ok=True)
            probe = root / ".legacy_base_system_file_mirror_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return root
        except Exception:
            continue
    raise RuntimeError("no writable legacy file root found")


def fetch_rows(bill_id):
    for base_url in BASE_URLS:
        url = f"{base_url}/api/System/FileApi/GetFileByBillId?BillId={bill_id}"
        try:
            with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=DOWNLOAD_TIMEOUT) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            yield base_url, None, str(exc)
            continue
        rows = payload.get("Data") if isinstance(payload, dict) else []
        if not isinstance(rows, list):
            rows = []
        yield base_url, [row for row in rows if isinstance(row, dict)], None


def select_row(rows, item):
    legacy_file_id = clean(item.legacy_file_id)
    if legacy_file_id:
        for row in rows:
            if clean(row.get("ID") or row.get("FileId")) == legacy_file_id:
                return row
    for row in rows:
        if clean(row.get("ATTR_PATH")):
            return row
    return None


def download(url, target):
    if not APPLY:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_target = target.with_suffix(target.suffix + ".part")
    with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=DOWNLOAD_TIMEOUT) as response:
        tmp_target.write_bytes(response.read())
    tmp_target.replace(target)


def add_example(examples, payload):
    if len(examples) < EXAMPLE_LIMIT:
        examples.append(payload)


def main():
    FileIndex = env["sc.legacy.file.index"].sudo().with_context(active_test=False)  # noqa: F821
    records = FileIndex.search(
        [
            ("active", "=", True),
            ("source_table", "=", "BASE_SYSTEM_FILE"),
            ("bill_id", "!=", False),
            "|",
            ("file_path", "!=", False),
            ("preview_path", "!=", False),
        ],
        order="id",
        limit=LIMIT or None,
    )
    root = writable_root()
    counts = Counter()
    examples = []
    for item in records:
        counts["records_checked"] += 1
        if is_local_ok(item):
            counts["already_local_ok"] += 1
            continue
        relative = clean(item.file_path) or clean(item.preview_path)
        if not relative:
            counts["missing_relative_path"] += 1
            continue
        target = (root / relative.replace("\\", "/").lstrip("/")).resolve()
        try:
            target.relative_to(root.resolve())
        except ValueError:
            counts["unsafe_relative_path"] += 1
            add_example(examples, {"kind": "unsafe_relative_path", "id": item.id, "relative": relative})
            continue

        selected = None
        selected_base_url = ""
        fetch_errors = []
        for base_url, rows, error in fetch_rows(clean(item.bill_id)):
            if error:
                fetch_errors.append({"base_url": base_url, "error": error})
                continue
            selected = select_row(rows or [], item)
            if selected:
                selected_base_url = base_url
                break
        if not selected:
            counts["online_missing"] += 1
            add_example(
                examples,
                {
                    "kind": "online_missing",
                    "id": item.id,
                    "bill_id": item.bill_id,
                    "legacy_file_id": item.legacy_file_id,
                    "errors": fetch_errors,
                },
            )
            continue
        url = clean(selected.get("ATTR_PATH"))
        if not url:
            counts["online_row_missing_url"] += 1
            continue
        try:
            download(url, target)
        except Exception as exc:
            counts["download_failed"] += 1
            add_example(
                examples,
                {
                    "kind": "download_failed",
                    "id": item.id,
                    "bill_id": item.bill_id,
                    "legacy_file_id": item.legacy_file_id,
                    "relative": relative,
                    "base_url": selected_base_url,
                    "error": str(exc),
                },
            )
            continue
        if APPLY and target.is_file() and target.stat().st_size > 0:
            counts["downloaded_local_ok"] += 1
        else:
            counts["dry_run_downloadable"] += 1
        add_example(
            examples,
            {
                "kind": "mirrored",
                "id": item.id,
                "bill_id": item.bill_id,
                "legacy_file_id": item.legacy_file_id,
                "relative": relative,
                "base_url": selected_base_url,
            },
        )

    result = {
        "status": "PASS" if counts.get("download_failed", 0) == 0 else "FAIL",
        "apply": APPLY,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_name": env.cr.dbname,  # noqa: F821
        "root": str(root),
        "base_urls": BASE_URLS,
        "counts": dict(counts),
        "examples": examples,
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit(1)


main()
