#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
from pathlib import Path

# allow lower/upper variable names
VAR_PATTERN = re.compile(r"\$\{([A-Za-z0-9_]+)\}")
LEFTOVER_PATTERN = re.compile(r"\$\{[^}]+\}")

# keys we expect to be present and non-empty after render
REQUIRED_KEYS = {
    "db_host",
    "db_port",
    "db_user",
    "db_password",
    "admin_passwd",
}

def render(text: str) -> str:
    def repl(m: re.Match) -> str:
        key = m.group(1)
        val = os.getenv(key)
        if val is None:
            raise SystemExit(f"[render_odoo_conf] Missing env var: {key}")
        return val
    return VAR_PATTERN.sub(repl, text)

def parse_kv(rendered: str) -> dict:
    """
    Very small INI-ish parser for [options] key=value lines.
    Ignores comments and section headers.
    """
    kv = {}
    for line in rendered.splitlines():
        s = line.strip()
        if not s or s.startswith(("#", ";")):
            continue
        if s.startswith("[") and s.endswith("]"):
            continue
        if "=" in s:
            k, v = s.split("=", 1)
            kv[k.strip()] = v.strip()
    return kv

def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: render_odoo_conf.py <template_path> <output_path>")

    tpl = Path(sys.argv[1])
    out = Path(sys.argv[2])

    text = tpl.read_text(encoding="utf-8")
    rendered = render(text)

    # hard fail if any ${...} still exists
    if LEFTOVER_PATTERN.search(rendered):
        leftovers = sorted(set(LEFTOVER_PATTERN.findall(rendered)))
        raise SystemExit(f"[render_odoo_conf] Unresolved placeholders remain: {leftovers}")

    kv = parse_kv(rendered)

    # required keys must exist and be non-empty
    missing = [k for k in REQUIRED_KEYS if not kv.get(k)]
    if missing:
        raise SystemExit(f"[render_odoo_conf] Missing/empty required keys after render: {missing}")

    # extra guardrail: password cannot be empty or quoted empty
    pwd = kv.get("db_password", "")
    if pwd in {"", '""', "''"}:
        raise SystemExit("[render_odoo_conf] db_password is empty after render")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")

    # safe log (no secrets)
    dbfilter_line = ""
    for line in rendered.splitlines():
        if line.strip().startswith("dbfilter"):
            dbfilter_line = line.strip()
            break

    print(f"[render_odoo_conf] Rendered {tpl} -> {out}")
    if dbfilter_line:
        print(f"[render_odoo_conf] {dbfilter_line}")

if __name__ == "__main__":
    main()
