#!/usr/bin/env python3
"""Fail-closed user/demo production-boundary audit and rehearsal cleanup.

Run through ``make odoo.shell.exec``. Reports contain only counts, technical IDs,
and irreversible login fingerprints; no profile values are emitted.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path


ACTION = os.getenv("USER_DATA_ACTION", "impact").strip().lower()
REPORT_PATH = Path(os.getenv("USER_DATA_REPORT_PATH", "/tmp/user-data-production-boundary.json"))
PLAN_PATH = Path(os.getenv("USER_DATA_PLAN_PATH", "/tmp/user-data-demo-removal-plan.json"))
FIXED_DEMO_LOGINS = {
    "demo_role_finance",
    "demo_role_project_a_member",
    "demo_role_pm",
    "demo_role_owner",
    "demo_role_executive",
}


def _ids(name: str) -> set[int]:
    values = set()
    for item in os.getenv(name, "").split(","):
        item = item.strip()
        if item:
            values.add(int(item))
    return values


def _fingerprint(value: str) -> str:
    return hashlib.sha256(str(value or "").encode()).hexdigest()[:16]


def _canonical_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _audit_user_references(user) -> dict:
    audit = {"create_uid": 0, "write_uid": 0}
    for field in audit:
        env.cr.execute(  # noqa: F821
            "SELECT table_name FROM information_schema.columns "
            "WHERE table_schema='public' AND column_name=%s ORDER BY table_name",
            (field,),
        )
        for (table,) in env.cr.fetchall():  # noqa: F821
            env.cr.execute(  # noqa: F821
                'SELECT count(*) FROM "' + table + '" WHERE "' + field + '"=%s',
                (user.id,),
            )
            audit[field] += env.cr.fetchone()[0]  # noqa: F821
    followers = env["mail.followers"].sudo().search_count(  # noqa: F821
        [("partner_id", "=", user.partner_id.id)]
    )
    return {**audit, "followers": followers, "total": sum(audit.values()) + followers}


def _build_inventory() -> dict:
    Users = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821
    Imd = env["ir.model.data"].sudo()  # noqa: F821
    demo_xmlids = Imd.search_read(
        [("module", "=", "smart_construction_demo")],
        ["model", "res_id", "noupdate"],
    )
    owned_user_ids = {row["res_id"] for row in demo_xmlids if row["model"] == "res.users"}
    candidates = Users.search(
        [
            "|",
            "|",
            ("id", "in", list(owned_user_ids) or [0]),
            ("login", "in", sorted(FIXED_DEMO_LOGINS)),
            ("login", "like", "demo_%"),
        ],
        order="id asc",
    )
    rows = []
    for user in candidates:
        refs = _audit_user_references(user)
        owned = user.id in owned_user_ids
        fixed = user.login in FIXED_DEMO_LOGINS
        action = "deactivate_preserve_history" if refs["total"] else "safe_delete_candidate"
        rows.append(
            {
                "user_id": user.id,
                "login_ref": _fingerprint(user.login),
                "active": bool(user.active),
                "demo_owned": owned,
                "fixed_fixture_account": fixed,
                "company_count": len(user.company_ids),
                "group_count": len(user.groups_id),
                "references": refs,
                "proposed_action": action,
            }
        )
    by_model = {}
    for row in demo_xmlids:
        by_model[row["model"]] = by_model.get(row["model"], 0) + 1
    module = env["ir.module.module"].sudo().search(  # noqa: F821
        [("name", "=", "smart_construction_demo")], limit=1
    )
    return {
        "database": env.cr.dbname,  # noqa: F821
        "module_state": module.state if module else "missing",
        "demo_owned_xmlid_count": len(demo_xmlids),
        "demo_owned_by_model": dict(sorted(by_model.items())),
        "candidate_users": rows,
    }


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _guard_apply(plan: dict) -> None:
    db = env.cr.dbname  # noqa: F821
    if os.getenv("SC_ENVIRONMENT") != "user_data_rehearsal":
        raise RuntimeError("SC_ENVIRONMENT must be user_data_rehearsal")
    if db != "sc_user_data_rehearsal":
        raise RuntimeError("apply is restricted to sc_user_data_rehearsal")
    if db in {"", "postgres", "sc_demo", "sc_frontend_acceptance"}:
        raise RuntimeError("dangerous database refused")
    if os.getenv("USER_DATA_APPLY_CONFIRM") != "APPLY_USER_DATA_PRODUCTION_BOUNDARY":
        raise RuntimeError("USER_DATA_APPLY_CONFIRM is missing")
    expected_hash = os.getenv("USER_DATA_PLAN_SHA256", "").strip()
    if not expected_hash or expected_hash != plan.get("plan_sha256"):
        raise RuntimeError("USER_DATA_PLAN_SHA256 mismatch")
    backup_manifest = Path(os.getenv("USER_DATA_BACKUP_MANIFEST", ""))
    backup_sha = os.getenv("USER_DATA_BACKUP_MANIFEST_SHA256", "").strip()
    if not backup_manifest.is_file() or not backup_sha:
        raise RuntimeError("paired backup manifest evidence is required")
    if hashlib.sha256(backup_manifest.read_bytes()).hexdigest() != backup_sha:
        raise RuntimeError("paired backup manifest checksum mismatch")


inventory = _build_inventory()
decisions = {
    "database": inventory["database"],
    "module_state": inventory["module_state"],
    "candidate_users": inventory["candidate_users"],
}
plan_hash = _canonical_hash(decisions)
plan = {
    "schema_version": 1,
    "mode": "dry_run",
    "plan_sha256": plan_hash,
    **decisions,
}

if ACTION == "impact":
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "action": ACTION,
        "database_writes": 0,
        **inventory,
    }
    _write(REPORT_PATH, payload)
elif ACTION == "plan":
    _write(PLAN_PATH, plan)
    payload = {"action": ACTION, "database_writes": 0, **plan}
    _write(REPORT_PATH, payload)
elif ACTION == "apply":
    if not PLAN_PATH.is_file():
        raise RuntimeError("plan file is missing")
    loaded_plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    _guard_apply(loaded_plan)
    if loaded_plan.get("plan_sha256") != plan_hash:
        raise RuntimeError("database state drifted after plan generation")
    deactivate_ids = _ids("USER_DATA_APPROVED_DEACTIVATE_IDS")
    delete_ids = _ids("USER_DATA_APPROVED_DELETE_IDS")
    planned_deactivate = {
        row["user_id"]
        for row in inventory["candidate_users"]
        if row["proposed_action"] == "deactivate_preserve_history"
    }
    planned_delete = {
        row["user_id"]
        for row in inventory["candidate_users"]
        if row["proposed_action"] == "safe_delete_candidate"
    }
    if deactivate_ids != planned_deactivate or delete_ids != planned_delete:
        raise RuntimeError("approved user IDs must exactly match the reviewed plan")
    Users = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821
    for user in Users.browse(sorted(deactivate_ids)).exists():
        company_ids = [user.company_id.id] if user.company_id else []
        user.write(
            {
                "active": False,
                "password": secrets.token_urlsafe(48),
                "groups_id": [(6, 0, [])],
                "company_ids": [(6, 0, company_ids)],
            }
        )
    for user in Users.browse(sorted(delete_ids)).exists():
        if _audit_user_references(user)["total"]:
            raise RuntimeError("delete candidate gained historical references")
        user.unlink()
    env.cr.commit()  # noqa: F821
    payload = {
        "schema_version": 1,
        "action": ACTION,
        "plan_sha256": plan_hash,
        "deactivated": len(deactivate_ids),
        "deleted": len(delete_ids),
        "database_writes": len(deactivate_ids) + len(delete_ids),
    }
    _write(REPORT_PATH, payload)
elif ACTION == "verify":
    active_candidates = [row for row in inventory["candidate_users"] if row["active"]]
    passed = inventory["module_state"] == "uninstalled" and not active_candidates
    payload = {
        "schema_version": 1,
        "action": ACTION,
        "database_writes": 0,
        "module_state": inventory["module_state"],
        "active_demo_candidate_count": len(active_candidates),
        "pass": passed,
    }
    _write(REPORT_PATH, payload)
    if not passed:
        raise SystemExit(1)
else:
    raise RuntimeError("USER_DATA_ACTION must be impact, plan, apply, or verify")

env.cr.rollback()  # noqa: F821
print("USER_DATA_PRODUCTION_BOUNDARY=" + json.dumps(payload, sort_keys=True))
