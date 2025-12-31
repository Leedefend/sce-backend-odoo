#!/usr/bin/env python3
import os
import re
import sys
import tempfile
from pathlib import Path

VAR_PATTERN = re.compile(r"\$\{?([A-Z0-9_]+)\}?")
LEFTOVER_PATTERN = re.compile(r"\$\{[^}]+\}")

REQUIRED_KEYS = {
    "db_host",
    "db_port",
    "db_user",
    "db_password",
    "db_name",
    "admin_passwd",
}

DEFAULT_OUT = "/var/lib/odoo/odoo.conf"


def render(text: str) -> str:
    def repl(m: re.Match) -> str:
        key = m.group(1)
        val = os.environ.get(key)
        if val is None:
            raise SystemExit(f"[render_odoo_conf] Missing env var: {key}")
        return val

    return VAR_PATTERN.sub(repl, text)


def parse_kv(rendered: str) -> dict:
    kv = {}
    for line in rendered.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        kv[k.strip()] = v.strip()
    return kv


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".odoo_conf_", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        Path(tmp).replace(path)
    finally:
        try:
            if Path(tmp).exists():
                Path(tmp).unlink()
        except Exception:
            pass


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: render_odoo_conf.py <template_path> <output_path>")

    tpl = Path(sys.argv[1])
    out_arg = (sys.argv[2] or "").strip()
    if out_arg in {"", "-", "auto"}:
        out_arg = os.environ.get("ODOO_CONF_OUT", DEFAULT_OUT)

    out = Path(out_arg)

    rendered = render(tpl.read_text(encoding="utf-8"))
    if LEFTOVER_PATTERN.search(rendered):
        leftovers = sorted(set(LEFTOVER_PATTERN.findall(rendered)))
        raise SystemExit(f"[render_odoo_conf] Unresolved placeholders remain: {leftovers}")
    kv = parse_kv(rendered)

    missing = REQUIRED_KEYS - kv.keys()
    if missing:
        raise SystemExit(f"[render_odoo_conf] Missing keys after render: {sorted(missing)}")

    if kv.get("db_password", "") in {"", "''", '""'}:
        raise SystemExit("[render_odoo_conf] db_password is empty after render")

    try:
        atomic_write_text(out, rendered)
    except PermissionError as e:
        raise SystemExit(
            "[render_odoo_conf] Permission denied writing config.\n"
            f"  target: {out}\n"
            "Fix options:\n"
            "  1) Set ODOO_CONF_OUT=/var/lib/odoo/odoo.conf (recommended)\n"
            "  2) Or change docker-compose volume/permissions\n"
            f"Original error: {e}"
        )

    dbfilter = kv.get("dbfilter")
    if dbfilter:
        print(f"[render_odoo_conf] dbfilter={dbfilter}")


if __name__ == "__main__":
    main()
