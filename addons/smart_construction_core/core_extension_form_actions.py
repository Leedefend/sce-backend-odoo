# -*- coding: utf-8 -*-
from typing import Any


def build_payment_form_business_action_contract(data: dict[str, Any]) -> dict[str, Any]:
    rows = data.get("actions") if isinstance(data, dict) and isinstance(data.get("actions"), list) else []
    primary_key = str(data.get("primary_action_key") or "") if isinstance(data, dict) else ""
    method_aliases = {
        "submit": ["action_submit"],
        "approve": ["action_approve", "action_set_approved", "validate_tier"],
        "reject": ["reject_tier", "action_on_tier_rejected"],
        "done": ["action_done"],
    }
    actions = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        action_key = str(row.get("key") or "").strip()
        if not action_key:
            continue
        methods = method_aliases.get(action_key, [str(row.get("method") or "").strip()])
        if action_key == "approve" and str(row.get("method") or "").strip() == "action_approval_decision":
            methods = ["action_approval_decision", *methods]
        for method in methods:
            if not method:
                continue
            actions.append(
                {
                    "key": f"payment_{action_key}",
                    "action_key": action_key,
                    "label": str(row.get("label") or action_key),
                    "kind": "mutation",
                    "level": "header",
                    "selection": "none",
                    "visible_profiles": ["edit", "readonly"],
                    "method": method,
                    "intent": str(row.get("execute_intent") or row.get("intent") or "payment.request.execute"),
                    "allowed": bool(row.get("allowed")),
                    "reason_code": str(row.get("reason_code") or ""),
                    "blocked_message": str(row.get("blocked_message") or ""),
                    "warning_message": str(row.get("warning_message") or ""),
                    "advisory_warnings": list(row.get("advisory_warnings") or []),
                    "advisory_reason_codes": list(row.get("advisory_reason_codes") or []),
                    "force_block_available": bool(row.get("force_block_available")),
                    "suggested_action": str(row.get("suggested_action") or ""),
                    "required_role_key": str(row.get("required_role_key") or ""),
                    "required_role_label": str(row.get("required_role_label") or ""),
                    "handoff_required": bool(row.get("handoff_required")),
                    "handoff_hint": str(row.get("handoff_hint") or ""),
                    "requires_reason": bool(row.get("requires_reason")),
                    "required_params": list(row.get("required_params") or []),
                    "primary": action_key == primary_key,
                    "mutation": {
                        "type": "record_action",
                        "model": "payment.request",
                        "operation": action_key,
                        "payload_schema": {
                            "id": "record_id",
                            "reason": "string" if bool(row.get("requires_reason")) else "",
                        },
                    },
                    "refresh_policy": {
                        "on_success": ["scene_projection"],
                        "mode": "reload_record",
                        "scope": "record",
                    },
                }
            )
    attachments = {
        "enabled": True,
        "label": "附件",
        "upload": {
            "intent": "file.upload",
            "max_bytes": 5 * 1024 * 1024,
            "accepted_types": [],
        },
        "download": {
            "intent": "file.download",
        },
        "ui_labels": {
            "upload": "上传附件",
            "uploading": "上传中...",
            "download": "下载",
            "upload_failed": "附件上传失败",
            "download_failed": "附件下载失败",
            "size_exceeded": "文件过大",
        },
    }
    return {"actions": actions, "attachments": attachments}
