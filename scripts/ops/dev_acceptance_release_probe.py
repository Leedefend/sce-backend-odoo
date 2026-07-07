#!/usr/bin/env python3
"""Read-only probe for the dev acceptance release surface."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT = ROOT / "artifacts" / "backend" / "dev_acceptance_release_probe.json"


def run_cmd(args: list[str], cwd: Path | None = None, timeout: int = 120) -> tuple[int, str]:
    proc = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    return proc.returncode, proc.stdout


def http_request(
    url: str,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    cookie_jar: CookieJar | None = None,
    timeout: int = 20,
) -> tuple[int, str, dict[str, str]]:
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar)) if cookie_jar else None
    try:
        with (opener.open(req, timeout=timeout) if opener else urllib.request.urlopen(req, timeout=timeout)) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace"), dict(resp.headers)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace"), dict(exc.headers)


def find_one(directory: Path, patterns: list[str]) -> Path | None:
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(directory.glob(pattern))
    matches = [p for p in matches if p.is_file()]
    return max(matches, key=lambda p: p.stat().st_mtime) if matches else None


def probe_backup(directory: Path | None, db_name: str) -> dict[str, Any]:
    if not directory:
        return {"enabled": False}
    result: dict[str, Any] = {"enabled": True, "dir": str(directory), "status": "PASS", "checks": {}}
    errors: list[str] = []
    if not directory.is_dir():
        return {"enabled": True, "dir": str(directory), "status": "FAIL", "errors": ["backup_dir_missing"]}

    checksum = directory / "SHA256SUMS"
    if checksum.exists():
        rc, out = run_cmd(["sha256sum", "-c", str(checksum.name)], cwd=directory)
        result["checks"]["sha256"] = {"rc": rc, "output": out.strip()}
        if rc != 0:
            errors.append("sha256_check_failed")
    else:
        errors.append("sha256sums_missing")

    dump = find_one(directory, [f"{db_name}_*.dump", "*.dump"])
    filestore = find_one(directory, [f"{db_name}_filestore_*.tgz", "*filestore*.tgz", "*.tar.gz"])
    result["dump"] = str(dump) if dump else None
    result["filestore"] = str(filestore) if filestore else None
    if not dump:
        errors.append("dump_missing")
    if not filestore:
        errors.append("filestore_archive_missing")

    if dump:
        rc, out = run_cmd(["pg_restore", "-l", str(dump)])
        db_match = re.search(r"dbname:\s*(\S+)", out)
        result["checks"]["pg_restore_list"] = {
            "rc": rc,
            "dbname": db_match.group(1) if db_match else None,
            "toc_entries": len(out.splitlines()),
        }
        if rc != 0:
            errors.append("pg_restore_list_failed")
        if db_match and db_match.group(1) != db_name:
            errors.append("dump_db_mismatch")

        rc, out = run_cmd(["pg_restore", "-f", "-", "--data-only", "-t", "ir_config_parameter", str(dump)])
        uuid_match = re.search(r"\tdatabase\.uuid\t([^\t\n]+)", out)
        result["checks"]["dump_database_uuid"] = uuid_match.group(1) if uuid_match else None
        if rc != 0:
            errors.append("dump_config_extract_failed")

    if filestore:
        try:
            with tarfile.open(filestore, "r:*") as archive:
                names = archive.getnames()[:2000]
            result["checks"]["filestore_prefix_present"] = any(name == db_name or name.startswith(f"{db_name}/") for name in names)
            result["checks"]["filestore_sample_entries"] = len(names)
            if not result["checks"]["filestore_prefix_present"]:
                errors.append("filestore_db_prefix_missing")
        except tarfile.TarError as exc:
            result["checks"]["filestore_error"] = str(exc)
            errors.append("filestore_archive_invalid")

    if errors:
        result["status"] = "FAIL"
        result["errors"] = errors
    return result


def probe_frontend(base_url: str, db_name: str, app_env: str, forbidden_db: str) -> dict[str, Any]:
    result: dict[str, Any] = {"status": "PASS", "base_url": base_url, "checks": {}}
    errors: list[str] = []
    status, body, headers = http_request(base_url.rstrip("/") + "/")
    result["checks"]["root_status"] = status
    result["checks"]["root_content_type"] = headers.get("Content-Type")
    if status != 200:
        errors.append("root_not_200")
    asset_match = re.search(r'<script[^>]+src="([^"]+index-[^"]+\.js)"', body)
    asset_path = asset_match.group(1) if asset_match else None
    result["checks"]["asset_path"] = asset_path
    if not asset_path:
        errors.append("frontend_asset_missing")
    else:
        asset_url = base_url.rstrip("/") + asset_path
        asset_status, asset_body, _asset_headers = http_request(asset_url)
        default_env_match = re.search(r'const\s+\w+="([^"]+)"\.trim\(\)\|\|"default"', asset_body)
        forbidden_default_db = (
            re.search(rf'const\s+\w+="{re.escape(forbidden_db)}"', asset_body) is not None if forbidden_db else False
        )
        result["checks"]["asset_status"] = asset_status
        result["checks"]["asset_has_db"] = db_name in asset_body
        result["checks"]["asset_has_app_env"] = f'"{app_env}"' in asset_body or app_env in asset_body
        result["checks"]["asset_default_app_env"] = default_env_match.group(1) if default_env_match else None
        result["checks"]["asset_has_forbidden_db_token"] = forbidden_db in asset_body if forbidden_db else False
        result["checks"]["asset_forbidden_db_is_default"] = forbidden_default_db
        if asset_status != 200:
            errors.append("frontend_asset_not_200")
        if db_name not in asset_body:
            errors.append("frontend_db_token_missing")
        if default_env_match and default_env_match.group(1) != app_env:
            errors.append("frontend_default_app_env_mismatch")
        if forbidden_default_db:
            errors.append("frontend_forbidden_db_is_default")

    options_status, _options_body, _options_headers = http_request(
        base_url.rstrip("/") + f"/api/v1/intent?db={db_name}",
        method="OPTIONS",
        headers={"X-Odoo-DB": db_name, "X-DB": db_name},
    )
    get_status, _get_body, _get_headers = http_request(
        base_url.rstrip("/") + f"/api/v1/intent?db={db_name}",
        headers={"X-Odoo-DB": db_name, "X-DB": db_name},
    )
    result["checks"]["intent_options_status"] = options_status
    result["checks"]["intent_get_status"] = get_status
    if options_status != 204:
        errors.append("intent_options_not_204")
    if get_status != 405:
        errors.append("intent_get_not_405")

    if errors:
        result["status"] = "FAIL"
        result["errors"] = errors
    return result


def _node_label(node: dict[str, Any]) -> str:
    return str(node.get("label") or node.get("title") or node.get("name") or node.get("display_name") or "").strip()


def _node_action_id(node: dict[str, Any]) -> Any:
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    target = node.get("target") if isinstance(node.get("target"), dict) else {}
    action = node.get("action") if isinstance(node.get("action"), dict) else {}
    return node.get("action_id") or meta.get("action_id") or target.get("action_id") or action.get("id") or action.get("action_id")


def _walk_nav(nodes: Any, path: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not isinstance(nodes, list):
        return rows
    for node in nodes:
        if not isinstance(node, dict):
            continue
        label = _node_label(node)
        current = path + ((label,) if label else ())
        children = node.get("children") if isinstance(node.get("children"), list) else []
        rows.append(
            {
                "path": " / ".join(current),
                "label": label,
                "action_id": _node_action_id(node),
                "child_count": len(children),
            }
        )
        rows.extend(_walk_nav(children, current))
    return rows


def _int_env(value: str) -> int | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _split_labels(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def probe_login(
    base_url: str,
    db_name: str,
    login: str,
    password: str,
    nav_min_actions: int | None = None,
    nav_max_actions: int | None = None,
    nav_forbidden_labels: list[str] | None = None,
) -> dict[str, Any]:
    if not login or not password:
        return {"enabled": False}
    cookie_jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    headers = {"Content-Type": "application/json", "X-Odoo-DB": db_name, "X-DB": db_name}
    payload = json.dumps(
        {"jsonrpc": "2.0", "params": {"db": db_name, "login": login, "password": password}}
    ).encode("utf-8")
    auth_req = urllib.request.Request(
        base_url.rstrip("/") + "/web/session/authenticate",
        data=payload,
        headers=headers,
        method="POST",
    )
    try:
        with opener.open(auth_req, timeout=20) as resp:
            status = resp.status
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read().decode("utf-8", errors="replace")
    result: dict[str, Any] = {"enabled": True, "status": "PASS", "login": login, "checks": {"auth_status": status}}
    errors: list[str] = []
    try:
        auth = json.loads(body)
    except json.JSONDecodeError:
        auth = {"error": "invalid_json", "raw": body[:300]}
    auth_result = auth.get("result") if isinstance(auth, dict) else None
    result["checks"]["auth_uid"] = auth_result.get("uid") if isinstance(auth_result, dict) else None
    result["checks"]["auth_name"] = auth_result.get("name") if isinstance(auth_result, dict) else None
    if status != 200 or not result["checks"]["auth_uid"]:
        errors.append("auth_failed")

    init_payload = json.dumps({"intent": "system.init", "params": {}}).encode("utf-8")
    init_req = urllib.request.Request(
        base_url.rstrip("/") + f"/api/v1/intent?db={db_name}",
        data=init_payload,
        headers=headers,
        method="POST",
    )
    try:
        with opener.open(init_req, timeout=20) as resp:
            init_status = resp.status
            init_body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        init_status = exc.code
        init_body = exc.read().decode("utf-8", errors="replace")
    result["checks"]["system_init_status"] = init_status
    try:
        init = json.loads(init_body)
    except json.JSONDecodeError:
        init = {"error": "invalid_json", "raw": init_body[:300]}
    result["checks"]["system_init_ok"] = bool(init.get("ok")) if isinstance(init, dict) else False
    data = init.get("data") if isinstance(init, dict) else None
    if isinstance(data, dict):
        role = data.get("role_surface") or {}
        result["checks"]["role_code"] = role.get("role_code") if isinstance(role, dict) else data.get("role_code")
        nav = data.get("nav") or data.get("menus") or []
        result["checks"]["nav_count"] = len(nav) if isinstance(nav, list) else None
        nav_rows = _walk_nav(nav)
        forbidden_labels = nav_forbidden_labels or []
        forbidden_hits = [
            row["path"]
            for row in nav_rows
            if any(token in row["path"] for token in forbidden_labels)
        ]
        result["checks"]["nav_node_count"] = len(nav_rows)
        result["checks"]["nav_action_count"] = sum(1 for row in nav_rows if row.get("action_id"))
        result["checks"]["nav_leaf_count"] = sum(1 for row in nav_rows if row.get("child_count") == 0)
        result["checks"]["nav_forbidden_label_hits"] = forbidden_hits[:50]
        result["checks"]["nav_paths_sample"] = [row["path"] for row in nav_rows[:80]]
        if not result["checks"]["role_code"]:
            errors.append("role_code_missing")
        if result["checks"]["nav_node_count"] <= 0:
            errors.append("nav_empty")
        if result["checks"]["nav_action_count"] <= 0:
            errors.append("nav_action_empty")
        if nav_min_actions is not None and result["checks"]["nav_action_count"] < nav_min_actions:
            errors.append("nav_action_count_below_min")
        if nav_max_actions is not None and result["checks"]["nav_action_count"] > nav_max_actions:
            errors.append("nav_action_count_above_max")
        if forbidden_hits:
            errors.append("nav_forbidden_label_hits")
    if init_status != 200 or not result["checks"]["system_init_ok"]:
        errors.append("system_init_failed")

    if errors:
        result["status"] = "FAIL"
        result["errors"] = errors
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup-dir", default=os.getenv("ACCEPTANCE_BACKUP_DIR", ""))
    parser.add_argument("--base-url", default=os.getenv("ACCEPTANCE_BASE_URL", "http://127.0.0.1:18081"))
    parser.add_argument("--db-name", default=os.getenv("DB_NAME", "sc_demo"))
    parser.add_argument("--app-env", default=os.getenv("VITE_APP_ENV", os.getenv("ENV", "dev")))
    parser.add_argument("--forbidden-db", default=os.getenv("ACCEPTANCE_FORBIDDEN_DB", "sc_prod_sim"))
    parser.add_argument("--login", default=os.getenv("ACCEPTANCE_LOGIN", ""))
    parser.add_argument("--password", default=os.getenv("ACCEPTANCE_PASSWORD", ""))
    parser.add_argument("--nav-min-actions", default=os.getenv("ACCEPTANCE_NAV_MIN_ACTIONS", ""))
    parser.add_argument("--nav-max-actions", default=os.getenv("ACCEPTANCE_NAV_MAX_ACTIONS", ""))
    parser.add_argument("--nav-forbidden-labels", default=os.getenv("ACCEPTANCE_NAV_FORBIDDEN_LABELS", ""))
    parser.add_argument("--output", default=os.getenv("ACCEPTANCE_PROBE_OUTPUT", str(DEFAULT_ARTIFACT)))
    args = parser.parse_args()

    backup_dir = Path(args.backup_dir).resolve() if args.backup_dir else None
    report = {
        "mode": "dev_acceptance_release_probe",
        "db_name": args.db_name,
        "base_url": args.base_url,
        "app_env": args.app_env,
        "backup": probe_backup(backup_dir, args.db_name),
        "frontend": probe_frontend(args.base_url, args.db_name, args.app_env, args.forbidden_db),
        "login": probe_login(
            args.base_url,
            args.db_name,
            args.login,
            args.password,
            nav_min_actions=_int_env(args.nav_min_actions),
            nav_max_actions=_int_env(args.nav_max_actions),
            nav_forbidden_labels=_split_labels(args.nav_forbidden_labels),
        ),
    }
    statuses = [
        report["backup"].get("status", "PASS"),
        report["frontend"].get("status", "PASS"),
        report["login"].get("status", "PASS"),
    ]
    report["status"] = "PASS" if all(status == "PASS" for status in statuses) else "FAIL"

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("DEV_ACCEPTANCE_RELEASE_PROBE=" + json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
