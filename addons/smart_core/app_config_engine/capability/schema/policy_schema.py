# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def normalize_policy_payload(payload: Any) -> Dict[str, Dict[str, Any]]:
    if not isinstance(payload, dict):
        payload = {}
    normalized: Dict[str, Dict[str, Any]] = {}
    permission = payload.get("permission") if isinstance(payload.get("permission"), dict) else {}
    normalized["permission"] = {
        "required_roles": permission.get("required_roles") if isinstance(permission.get("required_roles"), list) else [],
        "required_groups": permission.get("required_groups") if isinstance(permission.get("required_groups"), list) else [],
        "access_mode": str(permission.get("access_mode") or "execute").strip() or "execute",
        "data_scope": str(permission.get("data_scope") or "user_env").strip() or "user_env",
    }

    release = payload.get("release") if isinstance(payload.get("release"), dict) else {}
    normalized["release"] = {
        "tier": str(release.get("tier") or "standard").strip() or "standard",
        "slice": str(release.get("slice") or "").strip(),
        "exposure_mode": str(release.get("exposure_mode") or "default").strip() or "default",
        "approval_required": bool(release.get("approval_required", False)),
        "feature_flag": str(release.get("feature_flag") or "").strip(),
    }

    lifecycle = payload.get("lifecycle") if isinstance(payload.get("lifecycle"), dict) else {}
    normalized["lifecycle"] = {
        "status": str(lifecycle.get("status") or "ga").strip() or "ga",
        "deprecated": bool(lifecycle.get("deprecated", False)),
        "replacement_key": str(lifecycle.get("replacement_key") or "").strip(),
        "introduced_in": str(lifecycle.get("introduced_in") or "").strip(),
        "sunset_after": str(lifecycle.get("sunset_after") or "").strip(),
    }
    return normalized
