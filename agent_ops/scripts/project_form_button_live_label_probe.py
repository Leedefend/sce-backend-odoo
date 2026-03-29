#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe live project form button labels from inside the Odoo container")
    parser.add_argument("--db", required=True)
    parser.add_argument("--login", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--container", required=True)
    parser.add_argument("--forbid-label", action="append", default=[])
    return parser.parse_args()


def build_probe_code(db: str, login: str, password: str, forbid_labels: list[str]) -> str:
    labels = [str(item or "").strip() for item in forbid_labels if str(item or "").strip()]
    return """
import json
import urllib.request

base = "http://127.0.0.1:8069/api/v1/intent?db=%(db)s"
req = urllib.request.Request(
    base,
    data=json.dumps({"intent": "login", "params": {"db": %(db_quoted)s, "login": %(login)s, "password": %(password)s}}).encode(),
    headers={"Content-Type": "application/json", "X-Anonymous-Intent": "1"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=20).read().decode())
token = ((resp.get("data") or {}).get("session") or {}).get("token") or ((resp.get("data") or {}).get("token"))
req2 = urllib.request.Request(
    base,
    data=json.dumps({"intent": "ui.contract", "params": {"op": "model", "model": "project.project", "view_type": "form", "contract_mode": "user"}}).encode(),
    headers={"Content-Type": "application/json", "Authorization": "Bearer " + str(token or "")},
)
resp2 = json.loads(urllib.request.urlopen(req2, timeout=20).read().decode())
rows = ((resp2.get("data") or {}).get("buttons") or [])
payload = [
    {
        "key": row.get("key"),
        "label": row.get("label"),
        "level": row.get("level"),
        "selection": row.get("selection"),
        "method": ((row.get("payload") or {}).get("method")),
    }
    for row in rows
]
print(json.dumps(payload, ensure_ascii=False, indent=2))
forbidden = %(labels)s
present = []
for row in payload:
    label = str((row or {}).get("label") or "").strip()
    if label and label in forbidden and label not in present:
        present.append(label)
if present:
    raise SystemExit("forbidden labels still present: " + ", ".join(present))
""" % {
        "db": db,
        "db_quoted": repr(db),
        "login": repr(login),
        "password": repr(password),
        "labels": repr(labels),
    }


def main() -> int:
    args = parse_args()
    code = build_probe_code(args.db, args.login, args.password, args.forbid_label)
    result = subprocess.run(
        ["docker", "exec", "-i", args.container, "python3", "-c", code],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout or "docker exec failed\n")
        return result.returncode or 1
    sys.stdout.write(result.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
