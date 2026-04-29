#!/usr/bin/env python3
"""Normalize migrated real users for prod-sim business usability validation."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path


INITIAL_PASSWORD = os.getenv("REAL_USER_INITIAL_PASSWORD", "123456")
BUSINESS_CONFIG_ADMIN_LOGINS = {
    item.strip().lower()
    for item in os.getenv("REAL_USER_BUSINESS_CONFIG_ADMIN_LOGINS", "wutao").split(",")
    if item.strip()
}
EXCLUDED_LEGACY_USER_IDS = {
    item.strip()
    for item in os.getenv("REAL_USER_EXCLUDED_LEGACY_IDS", "10000000").split(",")
    if item.strip()
}
EXCLUDED_USER_NAME_BY_LEGACY_ID = {
    "10000000": "历史系统账号（不启用）",
}
ALLOWED_DBS = {
    item.strip()
    for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_prod_sim").split(",")
    if item.strip()
}
PINYIN = {
    "维": "wei", "护": "hu", "管": "guan", "理": "li", "员": "yuan",
    "段": "duan", "奕": "yi", "俊": "jun", "邓": "deng", "洪": "hong", "英": "ying",
    "陈": "chen", "帅": "shuai", "吴": "wu", "涛": "tao", "胡": "hu", "江": "jiang",
    "一": "yi", "娇": "jiao", "文": "wen", "楠": "nan", "尹": "yin", "佳": "jia",
    "梅": "mei", "杨": "yang", "德": "de", "胜": "sheng", "永": "yong", "田": "tian",
    "郑": "zheng", "建": "jian", "华": "hua", "世": "shi", "陈": "chen", "天": "tian",
    "友": "you", "钱": "qian", "光": "guang", "海": "hai", "魏": "wei", "玲": "ling",
    "李": "li", "林": "lin", "旭": "xu", "刘": "liu", "应": "ying", "木": "mu",
    "何": "he", "翔": "xiang", "宇": "yu", "汉": "han", "丹": "dan", "张": "zhang",
    "龙": "long", "根": "gen", "王": "wang", "浩": "hao", "辰": "chen", "雷": "lei", "蒋": "jiang",
    "毅": "yi", "卢": "lu", "燕": "yan", "赖": "lai", "轩": "xuan", "曾": "zeng",
    "小": "xiao", "东": "dong", "谭": "tan", "信": "xin", "坤": "kun", "严": "yan",
    "宗": "zong", "波": "bo", "叶": "ye", "凌": "ling", "越": "yue", "俭": "jian",
    "锋": "feng", "肖": "xiao", "辉": "hui", "玖": "jiu", "翠": "cui", "汶": "wen",
    "衔": "xian", "丽": "li", "测": "ce", "试": "shi", "向": "xiang", "赵": "zhao",
    "伟": "wei", "梁": "liang", "兵": "bing", "侯": "hou", "忠": "zhong", "磊": "lei",
    "加": "jia", "国": "guo", "倪": "ni", "模": "mo", "徐": "xu", "溪": "xi",
    "婷": "ting", "蔡": "cai", "思": "si", "琪": "qi", "康": "kang", "晓": "xiao",
    "临": "lin", "时": "shi", "账": "zhang", "号": "hao", "略": "lue", "潘": "pan",
    "唐": "tang", "明": "ming", "亭": "ting", "秦": "qin", "军": "jun", "钧": "jun", "茂": "mao",
    "易": "yi", "富": "fu", "廖": "liao", "中": "zhong", "行": "hang", "谢": "xie",
    "勤": "qin", "学": "xue", "银": "yin", "珍": "zhen", "娜": "na", "雨": "yu", "雪": "xue", "罗": "luo",
    "萌": "meng", "技": "ji", "术": "shu", "税": "shui", "务": "wu", "经": "jing",
    "办": "ban", "人": "ren", "阳": "yang",
}


def repo_root() -> Path:
    for candidate in (Path(os.getenv("MIGRATION_REPO_ROOT", "")), Path("/mnt"), Path.cwd()):
        if candidate and (candidate / "addons/smart_construction_core/__manifest__.py").exists():
            return candidate
    return Path.cwd()


def artifact_root() -> Path:
    candidates = []
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend(
        [
            Path("/mnt/artifacts/migration"),
            repo_root() / "artifacts/migration",
            Path(f"/tmp/history_real_user_normalize/{env.cr.dbname}"),  # noqa: F821
        ]
    )
    for root in candidates:
        try:
            root.mkdir(parents=True, exist_ok=True)
            probe = root / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return root
        except Exception:
            continue
    raise RuntimeError({"artifact_root_unavailable": [str(path) for path in candidates]})


def normalize_name_to_login(name: str) -> tuple[str, list[str]]:
    tokens: list[str] = []
    unknown: list[str] = []
    for char in (name or "").strip():
        if char in PINYIN:
            tokens.append(PINYIN[char])
        elif char.isascii() and char.isalnum():
            tokens.append(char.lower())
        elif char in {" ", "-", "_", "(", ")", "（", "）", "·", ".", "。"}:
            continue
        else:
            unknown.append(char)
    base = "".join(tokens)
    base = re.sub(r"[^a-z0-9_]+", "", base).strip("_")
    return base, unknown


def legacy_id_for(user) -> str:
    xml = env["ir.model.data"].sudo().search(  # noqa: F821
        [("module", "=", "migration_assets"), ("model", "=", "res.users"), ("res_id", "=", user.id)],
        limit=1,
    )
    if xml and xml.name.startswith("legacy_user_sc_"):
        return xml.name.removeprefix("legacy_user_sc_")
    if (user.login or "").startswith("legacy_"):
        return user.login.removeprefix("legacy_")
    return str(user.id)


def target_login(base: str, legacy_id: str, occupied: set[str], assigned: set[str]) -> tuple[str, bool]:
    candidate = base or f"user{legacy_id}"
    if candidate not in occupied and candidate not in assigned:
        assigned.add(candidate)
        return candidate, False
    suffix = re.sub(r"[^a-z0-9_]+", "", legacy_id.lower()) or "legacy"
    candidate = f"{base or 'user'}_{suffix}"
    index = 2
    while candidate in occupied or candidate in assigned:
        candidate = f"{base or 'user'}_{suffix}_{index}"
        index += 1
    assigned.add(candidate)
    return candidate, True


def profile_for(user, legacy_id: str):
    Profile = env["sc.legacy.user.profile"].sudo().with_context(active_test=False)  # noqa: F821
    return Profile.search(["|", ("user_id", "=", user.id), ("legacy_user_id", "=", legacy_id)], limit=1)


if env.cr.dbname not in ALLOWED_DBS:  # noqa: F821
    raise RuntimeError({"db_name_not_allowed_for_real_user_normalize": env.cr.dbname, "allowlist": sorted(ALLOWED_DBS)})  # noqa: F821

Users = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821
all_users = Users.search([])
real_user_ids = env["ir.model.data"].sudo().search(  # noqa: F821
    [
        ("module", "=", "migration_assets"),
        ("model", "=", "res.users"),
        ("name", "like", "legacy_user_sc_%"),
    ]
).mapped("res_id")
all_real_users = Users.browse(real_user_ids).exists()
excluded = []
for user in all_real_users.sorted("id"):
    legacy_id = legacy_id_for(user)
    if legacy_id not in EXCLUDED_LEGACY_USER_IDS:
        continue
    target_name = EXCLUDED_USER_NAME_BY_LEGACY_ID.get(legacy_id, f"历史系统账号（{legacy_id}，不启用）")
    vals = {
        "active": False,
        "name": target_name,
        "login": f"history_system_user_{legacy_id}",
    }
    before = {"login": user.login, "name": user.name, "active": bool(user.active)}
    user.write(vals)
    excluded.append(
        {
            "id": user.id,
            "legacy_id": legacy_id,
            "old_login": before["login"],
            "login": vals["login"],
            "old_name": before["name"],
            "name": vals["name"],
            "old_active": before["active"],
            "active": False,
            "decision": "excluded_from_real_business_user_matrix",
        }
    )

real_users = all_real_users.filtered(
    lambda u: bool(u.active and u.has_group("base.group_user") and legacy_id_for(u) not in EXCLUDED_LEGACY_USER_IDS)
)
internal_group = env.ref("smart_construction_core.group_sc_internal_user", raise_if_not_found=False)  # noqa: F821
business_initiator_group = env.ref(  # noqa: F821
    "smart_construction_core.group_sc_cap_business_initiator",
    raise_if_not_found=False,
)
business_config_group = env.ref(  # noqa: F821
    "smart_construction_core.group_sc_cap_business_config_admin",
    raise_if_not_found=False,
)
occupied_logins = set(all_users.mapped("login")) - set(real_users.mapped("login"))
assigned_logins: set[str] = set()
updated = []
blocked = []

for user in real_users.sorted("id"):
    legacy_id = legacy_id_for(user)
    profile = profile_for(user, legacy_id)
    source_name = (profile.display_name if profile and profile.display_name else user.name or "").strip()
    base_login, unknown_chars = normalize_name_to_login(source_name)
    if unknown_chars:
        blocked.append({"id": user.id, "name": user.name, "legacy_id": legacy_id, "unknown_chars": unknown_chars})
        continue
    login, suffix_used = target_login(base_login, legacy_id, occupied_logins, assigned_logins)
    vals = {
        "login": login,
        "password": INITIAL_PASSWORD,
    }
    internal_group_applied = bool(internal_group and internal_group not in user.groups_id)
    business_initiator_group_applied = bool(
        business_initiator_group and business_initiator_group not in user.groups_id
    )
    business_config_group_applied = bool(
        login.lower() in BUSINESS_CONFIG_ADMIN_LOGINS
        and business_config_group
        and business_config_group not in user.groups_id
    )
    group_commands = []
    if internal_group_applied:
        group_commands.append((4, internal_group.id))
    if business_initiator_group_applied:
        group_commands.append((4, business_initiator_group.id))
    if business_config_group_applied:
        group_commands.append((4, business_config_group.id))
    if group_commands:
        vals["groups_id"] = group_commands
    if profile:
        if profile.display_name and profile.display_name != user.name:
            vals["name"] = profile.display_name
        if "phone" in Users._fields and profile.phone:
            vals["phone"] = profile.phone
        if "mobile" in Users._fields and profile.phone:
            vals["mobile"] = profile.phone
        if profile.email:
            vals["email"] = profile.email.lower()
    before = {"login": user.login, "name": user.name, "email": user.email or "", "phone": getattr(user, "phone", "") or ""}
    user.write(vals)
    updated.append(
        {
            "id": user.id,
            "legacy_id": legacy_id,
            "name": vals.get("name", user.name),
            "old_login": before["login"],
            "login": login,
            "suffix_used": suffix_used,
            "password_initialized": True,
            "profile_used": bool(profile),
            "internal_group_applied": internal_group_applied,
            "business_initiator_group_applied": business_initiator_group_applied,
            "business_config_admin_target": login.lower() in BUSINESS_CONFIG_ADMIN_LOGINS,
            "business_config_group_applied": business_config_group_applied,
            "email_before": before["email"],
            "email_after": vals.get("email", before["email"]),
            "phone_before": before["phone"],
            "phone_after": vals.get("phone", before["phone"]),
        }
    )

if blocked:
    env.cr.rollback()  # noqa: F821
    payload = {
        "status": "FAIL",
        "db": env.cr.dbname,  # noqa: F821
        "mode": "history_real_user_normalize_write",
        "blocked": blocked,
        "db_writes": 0,
    }
else:
    env.cr.commit()  # noqa: F821
    payload = {
        "status": "PASS",
        "db": env.cr.dbname,  # noqa: F821
        "mode": "history_real_user_normalize_write",
        "decision": "real_users_normalized_for_login",
        "initial_password": INITIAL_PASSWORD,
        "excluded_legacy_user_ids": sorted(EXCLUDED_LEGACY_USER_IDS),
        "excluded_count": len(excluded),
        "excluded": excluded,
        "updated_count": len(updated),
        "suffix_count": sum(1 for row in updated if row["suffix_used"]),
        "business_config_admin_logins": sorted(BUSINESS_CONFIG_ADMIN_LOGINS),
        "business_config_admin_count": sum(1 for row in updated if row["business_config_admin_target"]),
        "updated": updated,
        "db_writes": len(updated),
    }

output = artifact_root() / "history_real_user_normalize_write_result_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("HISTORY_REAL_USER_NORMALIZE_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
