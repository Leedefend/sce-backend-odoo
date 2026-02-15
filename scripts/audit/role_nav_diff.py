#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from itertools import combinations
from pathlib import Path
from typing import Any
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "audit" / "role_nav_diff.latest.json"
OUT_MD = ROOT / "artifacts" / "audit" / "role_nav_diff.latest.md"

BASE_URL = (os.getenv("BASE_URL") or "http://localhost:8069").rstrip("/")
DB_NAME = (os.getenv("DB_NAME") or os.getenv("DB") or "sc_demo").strip()
ROOT_XMLID = (os.getenv("ROOT_XMLID") or "smart_construction_core.menu_sc_root").strip()

ROLE_USERS = [
    ("owner", os.getenv("ROLE_OWNER_LOGIN", "demo_role_owner"), os.getenv("ROLE_OWNER_PASSWORD", "demo")),
    ("pm", os.getenv("ROLE_PM_LOGIN", "demo_role_pm"), os.getenv("ROLE_PM_PASSWORD", "demo")),
    ("finance", os.getenv("ROLE_FINANCE_LOGIN", "demo_role_finance"), os.getenv("ROLE_FINANCE_PASSWORD", "demo")),
    ("executive", os.getenv("ROLE_EXECUTIVE_LOGIN", "demo_role_executive"), os.getenv("ROLE_EXECUTIVE_PASSWORD", "demo")),
]


def http_post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    req = urlrequest.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8") or "{}"
            return resp.status, json.loads(body)
    except HTTPError as e:
        body = e.read().decode("utf-8") if hasattr(e, "read") else ""
        try:
            return e.code, json.loads(body or "{}")
        except Exception:
            return e.code, {"raw": body}
    except URLError as e:
        raise RuntimeError(f"HTTP request failed: {e}") from e


def flatten_nav(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    stack = list(nodes or [])
    while stack:
        node = stack.pop(0)
        if not isinstance(node, dict):
            continue
        out.append(node)
        children = node.get("children") if isinstance(node.get("children"), list) else []
        stack[:0] = children
    return out


def node_key(node: dict[str, Any]) -> str:
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    for candidate in (
        meta.get("menu_xmlid"),
        node.get("xmlid"),
        node.get("menu_xmlid"),
    ):
        val = str(candidate or "").strip()
        if val:
            return val
    menu_id = node.get("menu_id") or node.get("id")
    if menu_id not in (None, ""):
        return f"id:{menu_id}"
    name = str(node.get("name") or "").strip()
    return f"name:{name}" if name else "unknown"


def run_for_role(role_code: str, login: str, password: str) -> dict[str, Any]:
    intent_url = f"{BASE_URL}/api/v1/intent"
    status, login_resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": DB_NAME, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    if status >= 400 or not login_resp.get("ok"):
        return {"role": role_code, "login": login, "error": f"login_failed:{status}", "detail": login_resp}
    token = str(((login_resp.get("data") or {}).get("token") or "")).strip()
    if not token:
        return {"role": role_code, "login": login, "error": "token_missing"}

    status, init_resp = http_post_json(
        intent_url,
        {"intent": "app.init", "params": {"scene": "web", "with_preload": False, "root_xmlid": ROOT_XMLID}},
        headers={"Authorization": f"Bearer {token}"},
    )
    if status >= 400 or not init_resp.get("ok"):
        return {"role": role_code, "login": login, "error": f"app_init_failed:{status}", "detail": init_resp}

    data = init_resp.get("data") if isinstance(init_resp.get("data"), dict) else {}
    role_surface = data.get("role_surface") if isinstance(data.get("role_surface"), dict) else {}
    nav = data.get("nav") if isinstance(data.get("nav"), list) else []
    flat = flatten_nav(nav)
    keys = sorted({node_key(n) for n in flat})
    scene_bound = 0
    for n in flat:
        meta = n.get("meta") if isinstance(n.get("meta"), dict) else {}
        scene_key = (n.get("scene_key") or meta.get("scene_key") or meta.get("sceneKey") or "").strip() if isinstance((n.get("scene_key") or meta.get("scene_key") or meta.get("sceneKey") or ""), str) else ""
        if scene_key:
            scene_bound += 1

    return {
        "role": role_code,
        "login": login,
        "actual_role": str(role_surface.get("role_code") or ""),
        "landing_scene_key": str(role_surface.get("landing_scene_key") or ""),
        "landing_path": str(role_surface.get("landing_path") or ""),
        "nav_count": len(flat),
        "scene_bound_count": scene_bound,
        "menu_keys": keys,
    }


def build_report() -> dict[str, Any]:
    role_results = [run_for_role(role, login, pwd) for role, login, pwd in ROLE_USERS]
    errors = [r for r in role_results if r.get("error")]
    role_map = {r.get("role"): r for r in role_results if not r.get("error")}

    pairwise: list[dict[str, Any]] = []
    for left, right in combinations(sorted(role_map.keys()), 2):
        a = set(role_map[left].get("menu_keys") or [])
        b = set(role_map[right].get("menu_keys") or [])
        pairwise.append(
            {
                "left": left,
                "right": right,
                "left_only_count": len(a - b),
                "right_only_count": len(b - a),
                "left_only_sample": sorted(list(a - b))[:12],
                "right_only_sample": sorted(list(b - a))[:12],
            }
        )

    blockers: list[str] = []
    if errors:
        blockers.append("role_login_or_init_failed")
    for role, payload in role_map.items():
        if int(payload.get("nav_count", 0)) <= 0:
            blockers.append(f"nav_empty:{role}")

    status = "pass" if not blockers else "block"
    return {
        "status": status,
        "blockers": blockers,
        "base_url": BASE_URL,
        "db": DB_NAME,
        "root_xmlid": ROOT_XMLID,
        "roles": role_results,
        "pairwise_diff": pairwise,
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# Role Navigation Diff",
        "",
        f"- status: `{report.get('status', 'n/a')}`",
        f"- blockers: `{', '.join(report.get('blockers') or []) or '-'}`",
        f"- db: `{report.get('db', '')}`",
        f"- root_xmlid: `{report.get('root_xmlid', '')}`",
        "",
        "## Role Summary",
    ]
    for row in report.get("roles") or []:
        if row.get("error"):
            lines.append(f"- {row.get('role')}: error=`{row.get('error')}` login=`{row.get('login')}`")
            continue
        lines.append(
            "- "
            + f"{row.get('role')}: nav_count=`{row.get('nav_count', 0)}` "
            + f"scene_bound=`{row.get('scene_bound_count', 0)}` "
            + f"landing=`{row.get('landing_scene_key', '')}`"
        )
    lines.append("")
    lines.append("## Pairwise Diff")
    for row in report.get("pairwise_diff") or []:
        lines.append(
            "- "
            + f"{row.get('left')} vs {row.get('right')}: "
            + f"left_only=`{row.get('left_only_count', 0)}` "
            + f"right_only=`{row.get('right_only_count', 0)}`"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    report = build_report()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_md(report), encoding="utf-8")
    print(str(OUT_JSON.relative_to(ROOT)))
    print(str(OUT_MD.relative_to(ROOT)))
    print(f"[role_nav_diff] status={report.get('status')} blockers={len(report.get('blockers') or [])}")
    if report.get("status") != "pass":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
