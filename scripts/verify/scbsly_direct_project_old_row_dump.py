#!/usr/bin/env python3
"""Dump SCBSLY direct-project historical-source list rows for replay asset locking."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from scbsly_direct_project_acceptance_menu_probe import (
    BASE_URL,
    OUTPUT as MENU_EVIDENCE,
    api_get,
    list_payload,
    login,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DUMP_DIR = Path(os.getenv("SCBSLY_OLD_ROWS_DIR", "/tmp/scbsly_direct_project_old_pages_20260530"))
DUMP_DIR = DEFAULT_DUMP_DIR
PAGE_SIZE = int(os.getenv("SCBSLY_OLD_ROW_DUMP_PAGE_SIZE", "250"))
OVERWRITE = os.getenv("SCBSLY_OLD_ROW_DUMP_OVERWRITE", "0") == "1"
SUMMARY_ONLY = os.getenv("SCBSLY_OLD_ROW_DUMP_SUMMARY_ONLY", "0") == "1"
OUTPUT = ROOT / "artifacts/migration/scbsly_direct_project_old_row_dump_summary_v1.json"
OUTPUT_MD = ROOT / "artifacts/migration/scbsly_direct_project_old_row_dump_summary_v1.md"


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


LABEL_FILTER = {
    clean(item)
    for item in re.split(r"[,，]", os.getenv("SCBSLY_OLD_ROW_DUMP_LABELS", ""))
    if clean(item)
}


def slug(value: str) -> str:
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "_", value, flags=re.UNICODE).strip("_")
    return text or "unnamed"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def data_rows(body: dict[str, Any]) -> list[Any]:
    data = body.get("Data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("Data", "Rows", "rows", "List"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def post_list_page(
    session: requests.Session,
    token: str,
    path: str,
    payload: dict[str, Any],
    *,
    retries: int = 3,
) -> dict[str, Any]:
    last_error = ""
    url = f"{BASE_URL}/api/{path}"
    for attempt in range(1, retries + 1):
        response = session.post(url, json=payload, headers={"Token": token}, timeout=180)
        response.raise_for_status()
        try:
            body = response.json()
        except ValueError as exc:
            last_error = f"invalid_json attempt={attempt} bytes={len(response.text)} error={exc}"
            continue
        if str(body.get("Code")) != "10000":
            last_error = f"api_error attempt={attempt} code={body.get('Code')} msg={body.get('Msg')}"
            continue
        return body
    raise RuntimeError(last_error or f"POST {path} failed")


def dump_one(session: requests.Session, token: str, evidence_row: dict[str, Any]) -> dict[str, Any]:
    label = clean(evidence_row.get("label"))
    config_id = clean(evidence_row.get("config_id"))
    expected_count = int((evidence_row.get("count_probe") or {}).get("data_count") or 0)
    file_name = f"{slug(label)}__{config_id}.json"
    out_path = DUMP_DIR / file_name
    if out_path.exists() and not OVERWRITE:
        existing = load_json(out_path)
        actual_count = int(existing.get("actual_count") or len(existing.get("rows") or []))
        if actual_count == expected_count:
            return {
                "category": evidence_row.get("category"),
                "label": label,
                "config_id": config_id,
                "api": existing.get("api"),
                "payload_policy": existing.get("payload_policy"),
                "expected_count": expected_count,
                "actual_count": actual_count,
                "status": "PASS",
                "path": str(out_path),
                "sha256": sha256_file(out_path),
                "size_bytes": out_path.stat().st_size,
                "reused_existing": True,
            }
    config = api_get(session, token, f"LowCode/FormApi/GetConfigById?Id={config_id}&LoadInitData=true")["Data"]
    path, base_payload, policy = list_payload(config)

    rows: list[Any] = []
    page_index = 1
    page_dir = DUMP_DIR / "_pages" / f"{slug(label)}__{config_id}"
    page_dir.mkdir(parents=True, exist_ok=True)
    while True:
        payload = deepcopy(base_payload)
        payload["PageIndex"] = page_index
        payload["PageSize"] = PAGE_SIZE
        page_path = page_dir / f"page_{page_index:05d}.json"
        if page_path.exists() and not OVERWRITE:
            page_payload = load_json(page_path)
            body = {
                "Data": page_payload.get("rows") if isinstance(page_payload, dict) else [],
                "DataCount": page_payload.get("data_count") if isinstance(page_payload, dict) else expected_count,
            }
            source = "cached"
        else:
            body = post_list_page(session, token, path, payload)
            source = "online"
        page_rows = data_rows(body)
        data_count = int(body.get("DataCount") or expected_count or len(rows) + len(page_rows))
        if source == "online":
            write_json(
                page_path,
                {
                    "source_system": BASE_URL,
                    "label": label,
                    "config_id": config_id,
                    "api": path,
                    "page_index": page_index,
                    "page_size": PAGE_SIZE,
                    "data_count": data_count,
                    "rows": page_rows,
                },
            )
        rows.extend(page_rows)
        print(
            "[scbsly-row-dump-page] {label} page={page} source={source} rows={page_rows} total={total}/{expected}".format(
                label=label,
                page=page_index,
                source=source,
                page_rows=len(page_rows),
                total=len(rows),
                expected=data_count,
            ),
            flush=True,
        )
        if not page_rows or len(rows) >= data_count:
            break
        page_index += 1

    payload = {
        "source_system": BASE_URL,
        "label": label,
        "category": evidence_row.get("category"),
        "config_id": config_id,
        "api": path,
        "payload_policy": policy,
        "expected_count": expected_count,
        "actual_count": len(rows),
        "rows": rows,
    }
    write_json(out_path, payload)
    return {
        "category": evidence_row.get("category"),
        "label": label,
        "config_id": config_id,
        "api": path,
        "payload_policy": policy,
        "expected_count": expected_count,
        "actual_count": len(rows),
        "status": "PASS" if len(rows) == expected_count else "FAIL",
        "path": str(out_path),
        "sha256": sha256_file(out_path),
        "size_bytes": out_path.stat().st_size,
    }


def markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# SCBSLY Direct Project Old Row Dump Summary v1",
        "",
        f"Status: `{summary['status']}`",
        f"Dump Dir: `{summary['dump_dir']}`",
        f"Generated At: `{summary['generated_at']}`",
        "",
        "| 分类 | 菜单 | ConfigId | Expected | Actual | Status |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in summary["rows"]:
        lines.append(
            "| {category} | {label} | `{config_id}` | {expected_count} | {actual_count} | {status} |".format(
                **row
            )
        )
    return "\n".join(lines) + "\n"


def existing_file_for(row: dict[str, Any]) -> Path:
    label = clean(row.get("label"))
    config_id = clean(row.get("config_id"))
    return DUMP_DIR / f"{slug(label)}__{config_id}.json"


def existing_summary_row(evidence_row: dict[str, Any]) -> dict[str, Any] | None:
    out_path = existing_file_for(evidence_row)
    if not out_path.exists():
        return None
    payload = load_json(out_path)
    expected_count = int((evidence_row.get("count_probe") or {}).get("data_count") or payload.get("expected_count") or 0)
    actual_count = int(payload.get("actual_count") or len(payload.get("rows") or []))
    return {
        "category": evidence_row.get("category") or payload.get("category"),
        "label": clean(evidence_row.get("label")) or payload.get("label"),
        "config_id": clean(evidence_row.get("config_id")) or payload.get("config_id"),
        "api": payload.get("api"),
        "payload_policy": payload.get("payload_policy"),
        "expected_count": expected_count,
        "actual_count": actual_count,
        "status": "PASS" if actual_count == expected_count else "FAIL",
        "path": str(out_path),
        "sha256": sha256_file(out_path),
        "size_bytes": out_path.stat().st_size,
        "reused_existing": True,
    }


def write_summary(user: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [row for row in rows if row["status"] != "PASS"]
    summary = {
        "status": "PASS" if not failures else "FAIL",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_system": BASE_URL,
        "menu_evidence": str(MENU_EVIDENCE.relative_to(ROOT)),
        "dump_dir": str(DUMP_DIR),
        "page_size": PAGE_SIZE,
        "old_user": {
            key: user.get(key)
            for key in ("UserId", "UserName", "PersonName", "ProjectId", "ProjectName", "CompanyId", "CompanyName")
        },
        "dumped_count": len(rows),
        "total_expected_rows": sum(int(row["expected_count"]) for row in rows),
        "total_actual_rows": sum(int(row["actual_count"]) for row in rows),
        "failure_count": len(failures),
        "failures": failures,
        "rows": rows,
    }
    write_json(OUTPUT, summary)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(markdown(summary), encoding="utf-8")
    return summary


def main() -> int:
    if not MENU_EVIDENCE.exists():
        raise SystemExit(f"missing menu evidence: {MENU_EVIDENCE.relative_to(ROOT)}")
    evidence = load_json(MENU_EVIDENCE)
    rows = [
        row
        for row in evidence.get("rows", [])
        if isinstance(row, dict)
        and row.get("route_kind") == "lowcode_form_list"
        and (row.get("count_probe") or {}).get("status") == "PASS"
        and (not LABEL_FILTER or clean(row.get("label")) in LABEL_FILTER)
    ]
    session = requests.Session()
    user = login(session)
    token = user["Token"]
    DUMP_DIR.mkdir(parents=True, exist_ok=True)

    if SUMMARY_ONLY:
        dumped = [summary_row for row in rows if (summary_row := existing_summary_row(row))]
        summary = write_summary(user, dumped)
        print(f"SCBSLY_DIRECT_PROJECT_OLD_ROW_DUMP={summary['status']} output={OUTPUT}")
        return 0 if not summary["failures"] else 2

    dumped: list[dict[str, Any]] = []
    for row in rows:
        result = dump_one(session, token, row)
        dumped.append(result)
        print(
            "[scbsly-row-dump] {status} {label} {actual}/{expected} -> {path}".format(
                status=result["status"],
                label=result["label"],
                actual=result["actual_count"],
                expected=result["expected_count"],
                path=result["path"],
            ),
            flush=True,
        )

    summary = write_summary(user, dumped)
    print(f"SCBSLY_DIRECT_PROJECT_OLD_ROW_DUMP={summary['status']} output={OUTPUT}")
    return 0 if not summary["failures"] else 2


if __name__ == "__main__":
    sys.exit(main())
