#!/usr/bin/env python3
"""Probe menu visibility boundaries for business, business-config, and system-config roles."""

from __future__ import annotations

import json
import os
from pathlib import Path


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


Menu = env["ir.ui.menu"].sudo()  # noqa: F821
IMD = env["ir.model.data"].sudo()  # noqa: F821
Users = env["res.users"].sudo()  # noqa: F821


def xmlid_for(rec) -> str:
    if not rec:
        return ""
    row = IMD.search([("model", "=", rec._name), ("res_id", "=", rec.id)], limit=1)
    return row.complete_name if row else ""


def menu_path(menu) -> str:
    names = []
    current = menu
    while current:
        names.append(current.name)
        current = current.parent_id
    return " / ".join(reversed(names))


def visible_sc_menus(user):
    visible_ids = Menu.with_user(user)._visible_menu_ids(debug=False)
    rows = []
    for menu in Menu.browse(visible_ids).sorted(lambda item: (menu_path(item), item.id)):
        path = menu_path(menu)
        if "智能施工" not in path:
            continue
        rows.append(
            {
                "xmlid": xmlid_for(menu),
                "path": path,
                "groups": sorted(menu.groups_id.mapped("display_name")),
            }
        )
    return rows


def user_row(login: str) -> dict[str, object]:
    user = Users.search([("login", "=", login)], limit=1)
    if not user:
        return {"login": login, "missing": True}
    menus = visible_sc_menus(user)
    return {
        "login": login,
        "user_id": user.id,
        "missing": False,
        "is_system": bool(user.has_group("base.group_system")),
        "has_business_config": bool(user.has_group("smart_construction_core.group_sc_cap_business_config_admin")),
        "has_platform_config": bool(user.has_group("smart_construction_core.group_sc_cap_config_admin")),
        "menu_count": len(menus),
        "top_menus": sorted({row["path"].split(" / ")[1] for row in menus if " / " in row["path"]}),
        "menus": menus,
    }


ordinary_logins = [
    "demo_role_project_read",
    "demo_role_project_user",
    "demo_role_project_manager",
    "demo_role_finance",
]
business_config_logins = ["demo_role_executive"]
platform_logins = ["admin"]
all_logins = ordinary_logins + business_config_logins + platform_logins

system_forbidden_fragments = [
    "系统配置",
    "场景与能力",
    "Scene Governance",
    "工作流",
    "订阅",
    "授权快照",
    "用量统计",
    "运营任务",
    "交付包",
]
business_config_fragments = [
    "业务配置",
    "数据字典",
    "定额库",
    "成本科目",
    "阶段要求配置",
]

users = {login: user_row(login) for login in all_logins}
errors: list[str] = []

business_full = env.ref("smart_construction_core.group_sc_business_full", raise_if_not_found=False)  # noqa: F821
executive_group = env.ref("smart_construction_custom.group_sc_role_executive", raise_if_not_found=False)  # noqa: F821
platform_group = env.ref("smart_construction_core.group_sc_cap_config_admin", raise_if_not_found=False)  # noqa: F821
business_config_group = env.ref(  # noqa: F821
    "smart_construction_core.group_sc_cap_business_config_admin",
    raise_if_not_found=False,
)
system_group = env.ref("base.group_system", raise_if_not_found=False)  # noqa: F821

group_boundary = {}
for xmlid, group in [
    ("smart_construction_core.group_sc_business_full", business_full),
    ("smart_construction_custom.group_sc_role_executive", executive_group),
]:
    if not group:
        group_boundary[xmlid] = {"missing": True}
        errors.append(f"{xmlid}: missing group")
        continue
    trans = group.trans_implied_ids
    group_boundary[xmlid] = {
        "missing": False,
        "has_system": bool(system_group and system_group in trans),
        "has_platform_config": bool(platform_group and platform_group in trans),
        "has_business_config": bool(business_config_group and business_config_group in trans),
        "trans_implied": sorted(trans.mapped("display_name")),
    }
    if system_group and system_group in trans:
        errors.append(f"{xmlid}: must not imply base.group_system")
    if platform_group and platform_group in trans:
        errors.append(f"{xmlid}: must not imply platform config group")

for login in all_logins:
    if users[login].get("missing"):
        errors.append(f"{login}: missing fixture user")

for login in ordinary_logins:
    row = users[login]
    paths = [item["path"] for item in row.get("menus", [])]
    leaked = [path for path in paths if any(fragment in path for fragment in system_forbidden_fragments)]
    business_config_seen = [path for path in paths if "业务配置" in path]
    if row.get("is_system"):
        errors.append(f"{login}: ordinary role must not be base.group_system")
    if row.get("has_platform_config"):
        errors.append(f"{login}: ordinary role must not have platform config group")
    if leaked:
        errors.append(f"{login}: ordinary role sees system config menus: {leaked[:8]}")
    if business_config_seen:
        errors.append(f"{login}: ordinary role sees business config root: {business_config_seen[:8]}")

for login in business_config_logins:
    row = users[login]
    paths = [item["path"] for item in row.get("menus", [])]
    leaked = [path for path in paths if any(fragment in path for fragment in system_forbidden_fragments)]
    if row.get("is_system"):
        errors.append(f"{login}: business config role must not be base.group_system")
    if row.get("has_platform_config"):
        errors.append(f"{login}: business config role must not have platform config group")
    if not row.get("has_business_config"):
        errors.append(f"{login}: business config role missing business config group")
    if not any(any(fragment in path for fragment in business_config_fragments) for path in paths):
        errors.append(f"{login}: business config role cannot see business config menus")
    if leaked:
        errors.append(f"{login}: business config role sees system config menus: {leaked[:8]}")

for login in platform_logins:
    row = users[login]
    paths = [item["path"] for item in row.get("menus", [])]
    if not row.get("is_system"):
        errors.append(f"{login}: platform role must be base.group_system")
    if not row.get("has_platform_config"):
        errors.append(f"{login}: platform role missing platform config group")
    if not any("系统配置" in path for path in paths):
        errors.append(f"{login}: platform role cannot see system config root")
    if not any("业务配置" in path for path in paths):
        errors.append(f"{login}: platform role cannot see business config root")

payload = {
    "status": "PASS" if not errors else "FAIL",
    "mode": "menu_role_visibility_governance_probe",
    "database": env.cr.dbname,  # noqa: F821
    "db_writes": 0,
    "errors": errors,
    "error_count": len(errors),
    "group_boundary": group_boundary,
    "users": users,
}
output_json = resolve_artifact_root() / "menu_role_visibility_governance_probe_result_v1.json"
write_json(output_json, payload)
print("MENU_ROLE_VISIBILITY_GOVERNANCE_PROBE=" + json.dumps(
    {
        "status": payload["status"],
        "database": payload["database"],
        "error_count": payload["error_count"],
        "errors": errors[:12],
        "summary": {
            login: {
                "is_system": users[login].get("is_system"),
                "has_business_config": users[login].get("has_business_config"),
                "has_platform_config": users[login].get("has_platform_config"),
                "top_menus": users[login].get("top_menus"),
            }
            for login in all_logins
        },
    },
    ensure_ascii=False,
    sort_keys=True,
))
if errors:
    raise RuntimeError({"menu_role_visibility_governance_errors": errors})
