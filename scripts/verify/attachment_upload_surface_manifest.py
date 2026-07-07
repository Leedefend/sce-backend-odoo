"""Generate a production read-only manifest for attachment upload surfaces.

The manifest is intentionally metadata-only. It identifies models where
file.upload is enabled by backend policy, then records whether the selected
business user has write access and at least one writable record.
"""

import json
import os
from pathlib import Path

try:
    from odoo.addons.smart_construction_core.core_extension import smart_core_file_upload_allowed_models
except Exception:  # pragma: no cover - loaded inside Odoo shell in real runs
    smart_core_file_upload_allowed_models = None


OUTPUT = Path(
    os.getenv("LEGACY_ATTACHMENT_UPLOAD_SURFACE_OUTPUT")
    or os.getenv(
        "ATTACHMENT_UPLOAD_SURFACE_MANIFEST_OUTPUT",
        "/mnt/artifacts/backend/attachment_upload_surface_manifest.json",
    )
)
LOGIN = os.getenv("LEGACY_ATTACHMENT_UPLOAD_SURFACE_LOGIN") or os.getenv("ATTACHMENT_UPLOAD_SURFACE_LOGIN") or os.getenv("E2E_LOGIN") or "wutao"
SAMPLE_LIMIT = int(os.getenv("LEGACY_ATTACHMENT_UPLOAD_SURFACE_SAMPLE_LIMIT") or os.getenv("ATTACHMENT_UPLOAD_SURFACE_SAMPLE_LIMIT") or "3")
REQUIRED_MODELS = {
    item.strip()
    for item in (os.getenv("LEGACY_ATTACHMENT_UPLOAD_SURFACE_REQUIRED_MODELS") or os.getenv("ATTACHMENT_UPLOAD_SURFACE_REQUIRED_MODELS") or "").split(",")
    if item.strip()
}


def _safe_write_json(path, data):
    candidates = [path, Path("/tmp/attachment_upload_surface_manifest.json")]
    last_error = None
    for candidate in candidates:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            candidate.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
            return str(candidate)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise last_error


def _first_menu_action_for_model(model_name):
    Action = env["ir.actions.act_window"].sudo()  # noqa: F821
    action = Action.search([("res_model", "=", model_name)], limit=1)
    menu_id = None
    if action:
        for menu in env["ir.ui.menu"].sudo().search([("action", "!=", False)], limit=20000):  # noqa: F821
            try:
                if menu.action and menu.action._name == "ir.actions.act_window" and menu.action.id == action.id:
                    menu_id = menu.id
                    break
            except Exception:
                continue
    return {
        "action_id": action.id if action else None,
        "action_name": action.name if action else "",
        "menu_id": menu_id,
    }


def _contract_upload_enabled(model_name, record_id, action_id):
    try:
        handler = env["smart_core.ui.contract.v2"]  # noqa: F821
    except Exception:
        return None
    try:
        payload = {
            "model": model_name,
            "record_id": record_id,
            "action_id": action_id,
            "view_type": "form",
            "render_profile": "edit",
        }
        contract = handler.sudo().get_contract(payload) if hasattr(handler, "get_contract") else None
    except Exception:
        return None
    if not isinstance(contract, dict):
        return None
    form = (contract.get("views") or {}).get("form") or {}
    attachments = form.get("attachments") or {}
    upload = attachments.get("upload") or {}
    return bool(attachments.get("enabled") and upload.get("enabled") is not False and upload.get("intent") == "file.upload")


def _row_for_model(model_name, user):
    row = {
        "model": model_name,
        "exists": model_name in env,  # noqa: F821
        "required": model_name in REQUIRED_MODELS,
    }
    if model_name not in env:  # noqa: F821
        row["classification"] = "missing_model"
        return row

    Model = env[model_name]  # noqa: F821
    row["record_count_sudo"] = Model.sudo().search_count([])
    row.update(_first_menu_action_for_model(model_name))
    try:
        row["transient"] = bool(getattr(Model, "_transient", False))
        row["abstract"] = bool(getattr(Model, "_abstract", False))
    except Exception:
        row["transient"] = None
        row["abstract"] = None

    UserModel = Model.with_user(user)
    try:
        UserModel.check_access_rights("read")
        row["read_rights"] = True
    except Exception as exc:  # noqa: BLE001
        row["read_rights"] = False
        row["read_error"] = type(exc).__name__

    try:
        UserModel.check_access_rights("write")
        row["write_rights"] = True
    except Exception as exc:  # noqa: BLE001
        row["write_rights"] = False
        row["write_error"] = type(exc).__name__
        row["sample_writable_ids"] = []
        row["classification"] = "not_business_user_writable"
        return row

    sample_ids = []
    for rec in UserModel.search([], limit=max(SAMPLE_LIMIT * 4, SAMPLE_LIMIT)):
        try:
            rec.check_access_rule("write")
            sample_ids.append(rec.id)
        except Exception:
            continue
        if len(sample_ids) >= SAMPLE_LIMIT:
            break
    row["sample_writable_ids"] = sample_ids
    row["sample_record_id"] = sample_ids[0] if sample_ids else None
    row["contract_upload_enabled_probe"] = _contract_upload_enabled(
        model_name,
        row["sample_record_id"],
        row.get("action_id"),
    ) if row["sample_record_id"] else None

    if not sample_ids:
        row["classification"] = "no_writable_record"
    elif row["contract_upload_enabled_probe"] is False:
        row["classification"] = "contract_upload_not_enabled"
    else:
        row["classification"] = "browser_upload_candidate"
    return row


allowed_models = []
if smart_core_file_upload_allowed_models:
    allowed_models = sorted(smart_core_file_upload_allowed_models(env))  # noqa: F821

user = env["res.users"].search([("login", "=", LOGIN)], limit=1)  # noqa: F821
if not user:
    raise RuntimeError("upload surface login not found: %s" % LOGIN)

rows = [_row_for_model(model_name, user) for model_name in allowed_models]
candidate_rows = [row for row in rows if row.get("classification") == "browser_upload_candidate"]
missing_required = [
    row["model"]
    for row in rows
    if row["model"] in REQUIRED_MODELS and row.get("classification") != "browser_upload_candidate"
]
data = {
    "scope": "attachment_upload_surface_manifest",
    "schema_version": "1.0",
    "login": LOGIN,
    "allowed_model_count": len(allowed_models),
    "candidate_count": len(candidate_rows),
    "required_models": sorted(REQUIRED_MODELS),
    "missing_required_candidate_models": missing_required,
    "rows": rows,
    "samples": [
        {
            "model": row["model"],
            "record_id": row["sample_record_id"],
            "action_id": row.get("action_id"),
            "menu_id": row.get("menu_id"),
        }
        for row in candidate_rows
    ],
    "status": "PASS" if not missing_required else "FAIL",
}
data["output"] = _safe_write_json(OUTPUT, data)
print(json.dumps(data, ensure_ascii=False, sort_keys=True))
