#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MARKER = "__SMART_CORE_CONFIG_FIXTURE__"


def _run_shell(code: str) -> dict:
    env = dict(os.environ)
    if not str(env.get("DB_NAME") or env.get("ODOO_DB") or "").strip():
        env["DB_NAME"] = str(env.get("ODOO_DB") or "sc_dev").strip()
    proc = None
    for attempt in range(3):
        proc = subprocess.run(
            ["bash", "scripts/ops/odoo_shell_exec.sh"],
            cwd=str(ROOT),
            env=env,
            input=code,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        combined = f"{proc.stdout or ''}\n{proc.stderr or ''}"
        if proc.returncode == 0 or "could not serialize access due to concurrent update" not in combined:
            break
        time.sleep(0.5 * (attempt + 1))
    assert proc is not None
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "").strip() or "odoo shell config fixture failed")
    for line in reversed((proc.stdout or "").splitlines()):
        if line.startswith(MARKER):
            payload = line[len(MARKER):].strip()
            try:
                data = json.loads(payload)
            except Exception as exc:
                raise RuntimeError(f"invalid config fixture payload: {payload}") from exc
            return data if isinstance(data, dict) else {}
    raise RuntimeError("config fixture marker missing from odoo shell output")


def read_config_parameter(key: str) -> dict:
    key_json = json.dumps(str(key or ""))
    code = f"""
import json
key = {key_json}
Param = env["ir.config_parameter"].sudo()
rec = Param.search([("key", "=", key)], limit=1)
payload = {{"exists": bool(rec), "value": str(rec.value or "") if rec else ""}}
print("{MARKER}" + json.dumps(payload, ensure_ascii=False))
"""
    return _run_shell(code)


def write_config_parameter(key: str, value: str) -> None:
    key_json = json.dumps(str(key or ""))
    value_json = json.dumps(str(value or ""))
    code = f"""
key = {key_json}
value = {value_json}
env["ir.config_parameter"].sudo().set_param(key, value)
env.cr.commit()
print("{MARKER}" + '{{"ok": true}}')
"""
    _run_shell(code)


def restore_config_parameter(key: str, *, existed: bool, value: str) -> None:
    key_json = json.dumps(str(key or ""))
    value_json = json.dumps(str(value or ""))
    existed_json = "True" if existed else "False"
    code = f"""
key = {key_json}
value = {value_json}
existed = {existed_json}
Param = env["ir.config_parameter"].sudo()
if existed:
    Param.set_param(key, value)
else:
    Param.search([("key", "=", key)]).unlink()
env.cr.commit()
print("{MARKER}" + '{{"ok": true}}')
"""
    _run_shell(code)
