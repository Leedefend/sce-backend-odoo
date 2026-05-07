#!/usr/bin/env python3
"""Apply user-maintenance visible-surface exports onto legacy user profiles."""

from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile


NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
DEFAULT_FILES = (
    "/mnt/artifacts/migration/user_visible_surface/user_maintenance_page1.xlsx,"
    "/mnt/artifacts/migration/user_visible_surface/user_maintenance_page2.xlsx"
)


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core/__manifest__.py").exists():
            return candidate
    return Path.cwd()


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(repo_root() / "artifacts/migration")))
    root.mkdir(parents=True, exist_ok=True)
    return root


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_visible_surface_overlay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def col_to_idx(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    value = 0
    for ch in letters:
        value = value * 26 + ord(ch.upper()) - 64
    return value


def shared_strings(zip_file: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zip_file.namelist():
        return []
    root = ET.fromstring(zip_file.read("xl/sharedStrings.xml"))
    return [
        "".join((text.text or "") for text in item.findall(".//a:t", NS))
        for item in root.findall("a:si", NS)
    ]


def cell_value(cell, shared: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join((text.text or "") for text in cell.findall(".//a:t", NS)).strip()
    value = cell.find("a:v", NS)
    if value is None:
        return ""
    raw = value.text or ""
    if cell_type == "s":
        try:
            return shared[int(raw)].strip()
        except Exception:
            return raw.strip()
    return raw.strip()


def read_sheet_rows(path: Path) -> list[dict[str, str]]:
    with ZipFile(path) as zip_file:
        shared = shared_strings(zip_file)
        root = ET.fromstring(zip_file.read("xl/worksheets/sheet1.xml"))
        rows: list[list[str]] = []
        for row in root.findall("a:sheetData/a:row", NS):
            values: dict[int, str] = {}
            for cell in row.findall("a:c", NS):
                values[col_to_idx(cell.attrib.get("r", "A1"))] = cell_value(cell, shared)
            if any(values.values()):
                rows.append([values.get(index, "") for index in range(1, 10)])
    if not rows:
        return []
    headers = rows[0]
    return [dict(zip(headers, row)) for row in rows[1:]]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def int_from(value: object) -> int:
    text = clean(value)
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


ensure_allowed_db()

source_files = [
    Path(item.strip())
    for item in os.getenv("LEGACY_USER_VISIBLE_SURFACE_FILES", DEFAULT_FILES).split(",")
    if item.strip()
]
rows: list[dict[str, str]] = []
missing_files = []
for source_file in source_files:
    if not source_file.exists():
        missing_files.append(str(source_file))
        continue
    rows.extend(read_sheet_rows(source_file))

if missing_files:
    raise RuntimeError({"missing_visible_surface_files": missing_files})

Profile = env["sc.legacy.user.profile"].sudo().with_context(active_test=False)  # noqa: F821
updated = []
blocked = []
seen = set()
for row in rows:
    login = clean(row.get("用户名"))
    if not login:
        blocked.append({"row": row, "reason": "missing_login"})
        continue
    if login in seen:
        blocked.append({"login": login, "reason": "duplicate_login_in_visible_surface"})
        continue
    seen.add(login)
    profile = Profile.search([("source_login", "=", login), ("active", "=", True)], limit=1, order="legacy_created_at desc, id desc")
    if not profile:
        profile = Profile.search([("source_login", "=", login)], limit=1, order="legacy_created_at desc, id desc")
    if not profile:
        blocked.append({"login": login, "reason": "missing_profile"})
        continue
    vals = {
        "source_login": login,
        "display_name": clean(row.get("姓名")) or profile.display_name,
        "phone": clean(row.get("手机号")) or False,
        "legacy_created_at": clean(row.get("建立时间")) or False,
        "department_scope_summary": clean(row.get("所属部门")) or False,
        "department_scope_count": 0 if not clean(row.get("所属部门")) else len([item for item in clean(row.get("所属部门")).split(",") if item.strip()]),
        "role_summary": clean(row.get("角色")) or False,
        "account_state_label": clean(row.get("状态")) or False,
        "login_count": int_from(row.get("登录次数")),
        "last_login_at": clean(row.get("最近登录时间")) or False,
    }
    profile.write(vals)
    updated.append(
        {
            "login": login,
            "profile_id": profile.id,
            "legacy_user_id": profile.legacy_user_id,
            "login_count": vals["login_count"],
            "last_login_at": vals["last_login_at"] or "",
            "department_scope_length": len(vals["department_scope_summary"] or ""),
            "role_summary": vals["role_summary"] or "",
        }
    )

env.cr.commit()  # noqa: F821
payload = {
    "status": "PASS" if not blocked else "PASS_WITH_BLOCKED",
    "mode": "legacy_user_visible_surface_overlay_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_files": [str(path) for path in source_files],
    "input_rows": len(rows),
    "unique_logins": len(seen),
    "updated_profiles": len(updated),
    "blocked": len(blocked),
    "blocked_samples": blocked[:20],
    "updated_samples": updated[:20],
    "decision": "legacy_user_visible_surface_overlay_applied" if not blocked else "legacy_user_visible_surface_overlay_with_blocked_rows",
}
output = artifact_root() / "legacy_user_visible_surface_overlay_write_result_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("LEGACY_USER_VISIBLE_SURFACE_OVERLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
