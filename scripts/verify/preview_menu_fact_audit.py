#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = REPO_ROOT / "artifacts" / "codex" / "preview-menu-fact-audit"
DB_NAME = os.environ.get("DB_NAME", "sc_demo").strip() or "sc_demo"
LOGIN = os.environ.get("E2E_LOGIN", "demo_pm").strip() or "demo_pm"
PASSWORD = os.environ.get("E2E_PASSWORD", "demo").strip() or "demo"
API_BASE = os.environ.get("API_BASE_URL", "http://127.0.0.1:8070").rstrip("/")


def post_intent(intent: str, params: dict, token: str | None = None) -> dict:
    url = f"{API_BASE}/api/v1/intent?db={DB_NAME}"
    payload = json.dumps({"intent": intent, "params": params}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["X-Anonymous-Intent"] = "true"
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def login() -> str:
    payload = post_intent(
        "login",
        {
            "login": LOGIN,
            "password": PASSWORD,
            "contract_mode": "default",
            "db": DB_NAME,
        },
    )
    token = (
        payload.get("data", {}).get("session", {}).get("token")
        or payload.get("data", {}).get("token")
        or payload.get("session", {}).get("token")
        or payload.get("token")
    )
    token = str(token or "").strip()
    if not token:
      raise RuntimeError("login response missing token")
    return token


def fetch_system_init(token: str) -> dict:
    payload = post_intent(
        "system.init",
        {
            "scene": "web",
            "root_xmlid": "smart_construction_core.menu_sc_root",
            "edition_key": "standard",
        },
        token=token,
    )
    return payload.get("data") or {}


def flatten_preview_leaves(nodes: list[dict]) -> list[dict]:
    out: list[dict] = []

    def walk(items: list[dict]):
        for item in items or []:
            children = item.get("children") if isinstance(item.get("children"), list) else []
            if children:
                walk(children)
                continue
            meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
            if str(meta.get("release_state") or "").strip() != "preview":
                continue
            out.append(
                {
                    "label": str(item.get("label") or item.get("title") or "").strip(),
                    "menu_id": int(item.get("menu_id") or 0),
                    "menu_xmlid": str(meta.get("menu_xmlid") or "").strip(),
                    "action_id": int(meta.get("action_id") or 0),
                    "action_xmlid": str(meta.get("action_xmlid") or "").strip(),
                    "model": str(meta.get("model") or "").strip(),
                    "route": str(meta.get("route") or "").strip(),
                    "scene_key": str(meta.get("scene_key") or "").strip(),
                }
            )

    walk(nodes)
    return out


def text_of_field(node: ET.Element, field_name: str) -> str:
    for child in node.findall("field"):
        if child.get("name") == field_name:
            ref = child.get("ref")
            if ref:
                return ref.strip()
            text = "".join(child.itertext()).strip()
            if text:
                return text
    return ""


def parse_xml_indexes() -> tuple[dict, dict, dict]:
    menu_index: dict[str, dict] = {}
    action_index: dict[str, dict] = {}
    view_index: dict[str, dict] = {}
    xml_files = list(REPO_ROOT.glob("addons/**/*.xml"))
    for file_path in xml_files:
        try:
            root = ET.parse(file_path).getroot()
        except Exception:
            continue
        for elem in root.iter():
            tag = elem.tag.split("}")[-1]
            if tag == "menuitem":
                xmlid = str(elem.get("id") or "").strip()
                if not xmlid:
                    continue
                menu_index[xmlid] = {
                    "xmlid": xmlid,
                    "file": str(file_path.relative_to(REPO_ROOT)),
                    "name": str(elem.get("name") or "").strip(),
                    "action_ref": str(elem.get("action") or "").strip(),
                    "parent": str(elem.get("parent") or "").strip(),
                    "groups": [item.strip() for item in str(elem.get("groups") or "").split(",") if item.strip()],
                    "sequence": str(elem.get("sequence") or "").strip(),
                }
            elif tag == "record":
                xmlid = str(elem.get("id") or "").strip()
                model = str(elem.get("model") or "").strip()
                if not xmlid or not model:
                    continue
                entry = {
                    "xmlid": xmlid,
                    "file": str(file_path.relative_to(REPO_ROOT)),
                    "model": model,
                    "name": text_of_field(elem, "name"),
                }
                if model.startswith("ir.actions."):
                    entry.update(
                        {
                            "res_model": text_of_field(elem, "res_model"),
                            "view_mode": text_of_field(elem, "view_mode"),
                            "view_id": text_of_field(elem, "view_id"),
                            "search_view_id": text_of_field(elem, "search_view_id"),
                            "target": text_of_field(elem, "target"),
                            "url": text_of_field(elem, "url"),
                            "context": text_of_field(elem, "context"),
                            "domain": text_of_field(elem, "domain"),
                            "groups_id_eval": next(
                                (
                                    str(field.get("eval") or "").strip()
                                    for field in elem.findall("field")
                                    if field.get("name") == "groups_id"
                                ),
                                "",
                            ),
                        }
                    )
                    action_index[xmlid] = entry
                elif model == "ir.ui.menu":
                    entry["groups_id_eval"] = next(
                        (
                            str(field.get("eval") or "").strip()
                            for field in elem.findall("field")
                            if field.get("name") == "groups_id"
                        ),
                        "",
                    )
                    menu_index.setdefault(xmlid, {"xmlid": xmlid, "file": str(file_path.relative_to(REPO_ROOT))}).update(entry)
                elif model == "ir.ui.view":
                    entry.update(
                        {
                            "view_model": text_of_field(elem, "model"),
                            "inherit_id": text_of_field(elem, "inherit_id"),
                        }
                    )
                    view_index[xmlid] = entry
    return menu_index, action_index, view_index


def lookup_xmlid(index: dict[str, dict], xmlid: str) -> dict:
    raw = str(xmlid or "").strip()
    if not raw:
        return {}
    if raw in index:
        return index[raw]
    bare = raw.split(".")[-1]
    return index.get(bare, {})


def parse_acl_index() -> dict[str, list[dict]]:
    acl_index: dict[str, list[dict]] = {}
    for csv_path in REPO_ROOT.glob("addons/**/ir.model.access.csv"):
        try:
            with csv_path.open("r", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    model_ref = str(row.get("model_id:id") or "").strip()
                    if not model_ref:
                        continue
                    acl_index.setdefault(model_ref, []).append(
                        {
                            "file": str(csv_path.relative_to(REPO_ROOT)),
                            "id": str(row.get("id") or "").strip(),
                            "group": str(row.get("group_id:id") or "").strip(),
                            "perm_read": str(row.get("perm_read") or "").strip(),
                            "perm_write": str(row.get("perm_write") or "").strip(),
                            "perm_create": str(row.get("perm_create") or "").strip(),
                            "perm_unlink": str(row.get("perm_unlink") or "").strip(),
                        }
                    )
        except Exception:
            continue
    return acl_index


def model_to_ref(model_name: str) -> str:
    if not model_name:
        return ""
    return f"model_{model_name.replace('.', '_')}"


def classify(menu: dict, action_fact: dict | None) -> str:
    if menu.get("route") and not menu.get("action_id"):
        return "scene_route_only"
    if action_fact and action_fact.get("model") == "ir.actions.act_url":
        return "url_action"
    if action_fact and action_fact.get("model") == "ir.actions.act_window":
        return "window_action"
    if menu.get("action_id"):
        return "runtime_action_only"
    return "manual_followup"


def audit() -> dict:
    token = login()
    init_data = fetch_system_init(token)
    user_groups = set(init_data.get("user", {}).get("groups_xmlids") or [])
    preview_menus = flatten_preview_leaves((init_data.get("release_navigation_v1") or {}).get("nav") or [])
    menu_index, action_index, view_index = parse_xml_indexes()
    acl_index = parse_acl_index()
    rows = []
    for menu in preview_menus:
        menu_fact = menu_index.get(menu["menu_xmlid"], {})
        if not menu_fact:
            menu_fact = lookup_xmlid(menu_index, menu["menu_xmlid"])
        action_xmlid = menu.get("action_xmlid") or menu_fact.get("action_ref") or ""
        action_fact = lookup_xmlid(action_index, action_xmlid)
        view_id = action_fact.get("view_id") or ""
        search_view_id = action_fact.get("search_view_id") or ""
        view_fact = lookup_xmlid(view_index, view_id) if view_id else {}
        search_view_fact = lookup_xmlid(view_index, search_view_id) if search_view_id else {}
        menu_groups = menu_fact.get("groups") or []
        menu_group_override = menu_fact.get("groups_id_eval") or ""
        pm_menu_group_match = [group for group in menu_groups if group in user_groups]
        model_name = menu.get("model") or action_fact.get("res_model") or ""
        model_ref = model_to_ref(model_name)
        acl_rows = acl_index.get(model_ref, [])
        pm_acl_match = [
            row for row in acl_rows
            if not row.get("group") or row.get("group") in user_groups
        ]
        rows.append(
            {
                "label": menu["label"],
                "menu_id": menu["menu_id"],
                "menu_xmlid": menu["menu_xmlid"],
                "menu_file": menu_fact.get("file", ""),
                "menu_groups": menu_groups,
                "menu_group_override": menu_group_override,
                "pm_menu_group_match": pm_menu_group_match,
                "scene_key": menu["scene_key"],
                "runtime_route": menu["route"],
                "runtime_action_id": menu["action_id"],
                "action_xmlid": action_xmlid,
                "action_type": action_fact.get("model", ""),
                "action_file": action_fact.get("file", ""),
                "res_model": model_name,
                "view_mode": action_fact.get("view_mode", ""),
                "view_id": view_id,
                "view_file": view_fact.get("file", ""),
                "search_view_id": search_view_id,
                "search_view_file": search_view_fact.get("file", ""),
                "action_url": action_fact.get("url", ""),
                "model_acl_ref": model_ref,
                "acl_rows": acl_rows,
                "pm_acl_match": pm_acl_match,
                "classification": classify(menu, action_fact if action_fact else None),
            }
        )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_base": API_BASE,
        "db_name": DB_NAME,
        "login": LOGIN,
        "pm_groups": sorted(user_groups),
        "preview_menu_count": len(rows),
        "rows": rows,
    }


def write_markdown(report: dict, out_dir: Path) -> None:
    lines = [
        "# Preview Menu Fact Audit",
        "",
        f"- db: `{report['db_name']}`",
        f"- login: `{report['login']}`",
        f"- preview_menu_count: `{report['preview_menu_count']}`",
        "",
        "## Classification Summary",
    ]
    counts: dict[str, int] = {}
    for row in report["rows"]:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    for key in sorted(counts):
        lines.append(f"- `{key}`: `{counts[key]}`")
    lines.extend(
        [
            "",
            "## Rows",
            "| 菜单 | menu_xmlid | action_xmlid | 模型 | 动作类型 | 视图模式 | 菜单组命中 | ACL命中 | 分类 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report["rows"]:
        lines.append(
            "| {label} | `{menu_xmlid}` | `{action_xmlid}` | `{res_model}` | `{action_type}` | `{view_mode}` | `{menu_hit}` | `{acl_hit}` | `{classification}` |".format(
                label=row["label"],
                menu_xmlid=row["menu_xmlid"] or "-",
                action_xmlid=row["action_xmlid"] or "-",
                res_model=row["res_model"] or "-",
                action_type=row["action_type"] or "-",
                view_mode=row["view_mode"] or "-",
                menu_hit="yes" if row["pm_menu_group_match"] or not row["menu_groups"] else "no",
                acl_hit="yes" if row["pm_acl_match"] or not row["acl_rows"] else "no",
                classification=row["classification"],
            )
        )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ARTIFACT_ROOT / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        report = audit()
    except (RuntimeError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        print(f"[preview_menu_fact_audit] FAIL {exc}", file=sys.stderr)
        return 1
    (out_dir / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, out_dir)
    print(f"[preview_menu_fact_audit] PASS artifacts={out_dir.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
