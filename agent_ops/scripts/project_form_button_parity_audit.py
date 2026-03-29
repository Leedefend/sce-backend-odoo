#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERIFY_DIR = ROOT / "scripts" / "verify"
if str(VERIFY_DIR) not in sys.path:
    sys.path.insert(0, str(VERIFY_DIR))

from intent_smoke_utils import require_ok  # type: ignore
from python_http_smoke_utils import get_base_url, http_post_json  # type: ignore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit live project form button parity chain")
    parser.add_argument("--db", required=True)
    parser.add_argument("--login", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--forbid-label", action="append", default=[])
    parser.add_argument("--expect-status", choices=["PASS"], default="PASS")
    return parser.parse_args()


def login(intent_url: str, db: str, login_name: str, password: str) -> str:
    status, resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db, "login": login_name, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, resp, f"login({login_name})")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    session = data.get("session") if isinstance(data.get("session"), dict) else {}
    token = str(session.get("token") or data.get("token") or "").strip()
    if not token:
        raise RuntimeError(f"login({login_name}) missing token")
    return token


def fetch_contract(intent_url: str, token: str) -> tuple[dict, dict]:
    status, resp = http_post_json(
        intent_url,
        {
            "intent": "ui.contract",
            "params": {"op": "model", "model": "project.project", "view_type": "form", "contract_mode": "user"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, "ui.contract(project.project.form)")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    meta = resp.get("meta") if isinstance(resp.get("meta"), dict) else {}
    return data, meta


def row_key(row: object) -> str:
    if not isinstance(row, dict):
        return ""
    return str(row.get("key") or "").strip()


def row_level(row: object) -> str:
    if not isinstance(row, dict):
        return ""
    return str(row.get("level") or "").strip().lower()


def row_label(row: object) -> str:
    if not isinstance(row, dict):
        return ""
    return str(row.get("label") or "").strip()


def main() -> int:
    args = parse_args()
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent?db={args.db}"

    token = login(intent_url, args.db, args.login, args.password)
    data, meta = fetch_contract(intent_url, token)

    buttons = data.get("buttons") if isinstance(data.get("buttons"), list) else []
    toolbar = data.get("toolbar") if isinstance(data.get("toolbar"), dict) else {}
    toolbar_header = toolbar.get("header") if isinstance(toolbar.get("header"), list) else []
    toolbar_sidebar = toolbar.get("sidebar") if isinstance(toolbar.get("sidebar"), list) else []
    toolbar_footer = toolbar.get("footer") if isinstance(toolbar.get("footer"), list) else []

    merged = []
    merged.extend(buttons)
    merged.extend(toolbar_header)
    merged.extend(toolbar_sidebar)
    merged.extend(toolbar_footer)

    dedup = []
    seen: set[str] = set()
    for row in merged:
      key = row_key(row)
      if not key or key in seen:
        continue
      seen.add(key)
      dedup.append(row)

    header_like = [
        row_key(row)
        for row in dedup
        if row_level(row) in {"header", "toolbar"}
    ]
    body_like = [
        row_key(row)
        for row in dedup
        if row_level(row) not in {"header", "toolbar"}
    ]
    rows = [
        {
            "key": row_key(row),
            "label": row_label(row),
            "level": row_level(row),
        }
        for row in dedup
    ]
    forbidden = {str(item or "").strip() for item in args.forbid_label if str(item or "").strip()}
    present_forbidden = sorted({row["label"] for row in rows if row["label"] in forbidden})
    if present_forbidden:
        raise RuntimeError("forbidden labels still present: %s" % ", ".join(present_forbidden))

    payload = {
        "status": "PASS",
        "base_url": base_url,
        "intent_url": intent_url,
        "trace_id": str(meta.get("trace_id") or ""),
        "contract_counts": {
            "buttons": len(buttons),
            "toolbar_header": len(toolbar_header),
            "toolbar_sidebar": len(toolbar_sidebar),
            "toolbar_footer": len(toolbar_footer),
        },
        "contract_keys_sample": {
            "buttons": [row_key(row) for row in buttons[:20] if row_key(row)],
            "toolbar_header": [row_key(row) for row in toolbar_header[:20] if row_key(row)],
            "toolbar_sidebar": [row_key(row) for row in toolbar_sidebar[:20] if row_key(row)],
            "toolbar_footer": [row_key(row) for row in toolbar_footer[:20] if row_key(row)],
        },
        "frontend_merge_projection": {
            "merged_count": len(merged),
            "dedup_count": len(dedup),
            "header_like_count": len(header_like),
            "body_like_count": len(body_like),
            "header_like_keys": header_like[:20],
            "body_like_keys": body_like[:20],
        },
        "rows": rows,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
