#!/usr/bin/env python3
"""Close user-facing legacy business menu exposures after formal projections exist."""

from __future__ import annotations

import json
import os
from pathlib import Path


TARGET_MENU_XMLIDS = [
    "smart_construction_core.menu_scbs55_user_acceptance_080_公司人员名册_配置",
    "smart_construction_core.menu_scbs55_user_acceptance_350_到款确认表",
    "smart_construction_core.menu_scbs55_user_acceptance_360_资金日报表",
    "smart_construction_core.menu_scbs55_user_acceptance_420_进项上报",
    "smart_construction_core.menu_scbs55_user_acceptance_440_外经证登记",
    "smart_construction_core.menu_scbs55_user_acceptance_450_供货合同分析",
]


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim,sc_migration_fresh").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"))  # noqa: F821
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


def action_res_model(menu) -> str:
    action = menu.action
    if not action:
        return ""
    return str(getattr(action, "res_model", "") or "")


ensure_allowed_db()
Menu = env["ir.ui.menu"].sudo().with_context(active_test=False)  # noqa: F821

rows = []
closed_count = 0
for xmlid in TARGET_MENU_XMLIDS:
    menu = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
    if not menu:
        rows.append({"xmlid": xmlid, "status": "missing"})
        continue
    if menu._name != "ir.ui.menu":
        rows.append({"xmlid": xmlid, "status": "not_menu", "model": menu._name})
        continue
    res_model = action_res_model(menu)
    row = {
        "xmlid": xmlid,
        "menu_id": int(menu.id),
        "menu_name": menu.complete_name,
        "active_before": bool(menu.active),
        "res_model": res_model,
    }
    if res_model.startswith("sc.legacy.") and menu.active:
        menu.write({"active": False})
        closed_count += 1
        row["status"] = "closed"
    elif res_model.startswith("sc.legacy."):
        row["status"] = "already_closed"
    else:
        row["status"] = "skipped_non_legacy_action"
    row["active_after"] = bool(Menu.browse(menu.id).active)
    rows.append(row)

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "history_legacy_business_menu_exposure_close_write",
    "database": env.cr.dbname,  # noqa: F821
    "target_count": len(TARGET_MENU_XMLIDS),
    "closed_count": closed_count,
    "rows": rows,
}
output_json = artifact_root() / "history_legacy_business_menu_exposure_close_write_result_v1.json"
output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("HISTORY_LEGACY_BUSINESS_MENU_EXPOSURE_CLOSE_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
