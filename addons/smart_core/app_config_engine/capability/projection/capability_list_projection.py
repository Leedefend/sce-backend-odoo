# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .capability_runtime_exposure import resolve_primary_intent, resolve_runtime_target


def build_capability_list_projection(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in rows:
        identity = row.get("identity") if isinstance(row, dict) else {}
        ui = row.get("ui") if isinstance(row, dict) else {}
        if not isinstance(identity, dict):
            continue
        key = str(identity.get("key") or "").strip()
        if not key:
            continue
        ownership = row.get("ownership") if isinstance(row.get("ownership"), dict) else {}
        binding = row.get("binding") if isinstance(row.get("binding"), dict) else {}
        permission = row.get("permission") if isinstance(row.get("permission"), dict) else {}
        release = row.get("release") if isinstance(row.get("release"), dict) else {}
        lifecycle = row.get("lifecycle") if isinstance(row.get("lifecycle"), dict) else {}
        runtime = row.get("runtime") if isinstance(row.get("runtime"), dict) else {}
        primary_intent = resolve_primary_intent(row)
        runtime_target = resolve_runtime_target(row)
        out.append(
            {
                "key": key,
                "name": str(identity.get("name") or "").strip(),
                "domain": str(identity.get("domain") or "").strip(),
                "type": str(identity.get("type") or "").strip(),
                "group_key": str((ui or {}).get("group_key") or "").strip(),
                "label": str((ui or {}).get("label") or identity.get("name") or "").strip(),
                "owner_module": str((ownership or {}).get("owner_module") or "").strip(),
                "source_module": str((ownership or {}).get("source_module") or "").strip(),
                "access_mode": str((permission or {}).get("access_mode") or "execute").strip() or "execute",
                "release_tier": str((release or {}).get("tier") or "").strip(),
                "lifecycle_status": str((lifecycle or {}).get("status") or "").strip(),
                "target_scene_key": str((((binding or {}).get("scene") or {}).get("entry_scene_key") or "")).strip(),
                "primary_intent": primary_intent,
                "supports_entry": bool((runtime or {}).get("supports_entry", False)),
                "runtime_target": runtime_target,
            }
        )
    return out
