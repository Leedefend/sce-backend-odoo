# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from typing import Any, Dict, Tuple

from ..core.registry import CapabilityRegistry


_REGISTRY_ARTIFACT_CACHE: dict[str, Dict[str, Any]] = {}


class CapabilityRegistryService:
    def __init__(self, *, platform_owner: str = "smart_core"):
        self.registry = CapabilityRegistry(platform_owner=platform_owner)

    @staticmethod
    def _artifact_version() -> str:
        return "v1"

    @staticmethod
    def _contract_version() -> str:
        return "v1"

    @staticmethod
    def _schema_version() -> str:
        return "v1"

    def _cache_key(self, env, user=None, *, mode: str) -> str:
        try:
            dbname = str(getattr(getattr(env, "cr", None), "dbname", "") or "").strip()
        except Exception:
            dbname = ""
        try:
            user_id = int(getattr(user, "id", 0) or 0)
        except Exception:
            user_id = 0
        normalized_mode = str(mode or "runtime").strip() or "runtime"
        return f"{dbname or '__default__'}::{self.registry.platform_owner}::{normalized_mode}::{user_id}"

    def _uncached_verification_salt(self, env) -> str:
        try:
            cr = getattr(env, "cr", None)
            if cr is None:
                return ""
            cr.execute(
                "SELECT value FROM ir_config_parameter WHERE key = %s",
                ["smart_core.capability_registry.verify_salt"],
            )
            row = cr.fetchone()
            return str(row[0] if row else "" or "").strip()
        except Exception:
            return ""

    def _verification_salt(self, env) -> str:
        verify_salt = self._uncached_verification_salt(env)
        if verify_salt:
            return verify_salt
        return str(os.environ.get("SMART_CORE_CAPABILITY_REGISTRY_VERIFY_SALT") or "").strip()

    def _expected_invalidation_key(self, env, *, mode: str) -> str:
        normalized_mode = str(mode or "runtime").strip() or "runtime"
        try:
            module_rows = env["ir.module.module"].sudo().search_read(
                [("state", "=", "installed"), ("name", "like", "smart_%")],
                fields=["name"],
                order="name asc",
            )
        except Exception:
            module_rows = []
        module_names = sorted(
            str(row.get("name") or "").strip()
            for row in (module_rows or [])
            if isinstance(row, dict) and str(row.get("name") or "").strip()
        )
        verify_salt = self._verification_salt(env)
        payload = {
            "artifact_version": self._artifact_version(),
            "contract_version": self._contract_version(),
            "schema_version": self._schema_version(),
            "platform_owner": self.registry.platform_owner,
            "mode": normalized_mode,
            "modules": module_names,
            "verify_salt": verify_salt,
        }
        return hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

    def _build_materialized_artifact(
        self,
        *,
        rows: list[dict[str, Any]],
        mode: str,
        cache_key: str,
        invalidation_key: str,
    ) -> Dict[str, Any]:
        return {
            "rows": [dict(row) for row in rows if isinstance(row, dict)],
            "artifact_version": self._artifact_version(),
            "source": "materialized_kernel_registry",
            "fallback_used": False,
            "fallback_reason": "",
            "stale": False,
            "mode": mode,
            "build_meta": {
                "platform_owner": self.registry.platform_owner,
                "cache_key": cache_key,
                "materialized_placeholder": True,
                "preferred_source": "materialized_kernel_registry",
                "contract_version": self._contract_version(),
                "schema_version": self._schema_version(),
                "mode": mode,
                "invalidation_key": invalidation_key,
            },
        }

    def _is_runtime_materialized_success(
        self,
        artifact: Dict[str, Any],
        *,
        mode: str,
        expected_invalidation_key: str,
    ) -> bool:
        if not isinstance(artifact, dict):
            return False
        if str(mode or "runtime").strip() != "runtime":
            return False
        if str(artifact.get("source") or "").strip() != "materialized_kernel_registry":
            return False
        if bool(artifact.get("fallback_used")):
            return False
        if str(artifact.get("fallback_reason") or "").strip():
            return False
        if bool(artifact.get("stale")):
            return False
        if str(artifact.get("artifact_version") or "").strip() != self._artifact_version():
            return False
        if not isinstance(artifact.get("rows"), list):
            return False
        build_meta = artifact.get("build_meta")
        if not isinstance(build_meta, dict):
            return False
        if str(build_meta.get("invalidation_key") or "").strip() != str(expected_invalidation_key or "").strip():
            return False
        return True

    def get_registry_bundle(self, env, user=None) -> Dict[str, Any]:
        return self.registry.build(env, user=user)

    def get_registry_bundle_with_timings(self, env, user=None) -> Tuple[Dict[str, Any], dict[str, int]]:
        return self.registry.build_with_timings(env, user=user)

    def get_registry_artifact(self, env, user=None, *, mode: str = "runtime") -> Dict[str, Any]:
        artifact, _timings = self.get_registry_artifact_with_timings(env, user=user, mode=mode)
        return artifact

    def get_registry_artifact_with_timings(
        self,
        env,
        user=None,
        *,
        mode: str = "runtime",
    ) -> Tuple[Dict[str, Any], dict[str, int]]:
        normalized_mode = str(mode or "runtime").strip() or "runtime"
        cache_key = self._cache_key(env, user=user, mode=normalized_mode)
        expected_invalidation_key = self._expected_invalidation_key(env, mode=normalized_mode)
        cached_artifact = _REGISTRY_ARTIFACT_CACHE.get(cache_key)
        if self._is_runtime_materialized_success(
            cached_artifact,
            mode=normalized_mode,
            expected_invalidation_key=expected_invalidation_key,
        ):
            return deepcopy(cached_artifact), {"artifact.materialized_read_hit": 0}

        bundle, timings_ms = self.get_registry_bundle_with_timings(env, user=user)
        rows = bundle.get("rows") if isinstance(bundle, dict) else []
        errors = bundle.get("errors") if isinstance(bundle, dict) else {}
        snapshot = bundle.get("snapshot") if isinstance(bundle, dict) else []
        source = "runtime_query_registry_build"
        fallback_used = normalized_mode == "runtime"
        stale = False
        fallback_reason = ""
        if fallback_used:
            cached_invalidation_key = ""
            if isinstance(cached_artifact, dict):
                build_meta = cached_artifact.get("build_meta")
                if isinstance(build_meta, dict):
                    cached_invalidation_key = str(build_meta.get("invalidation_key") or "").strip()
            if cached_invalidation_key and cached_invalidation_key != expected_invalidation_key:
                stale = True
                fallback_reason = "artifact_stale"
            else:
                fallback_reason = "artifact_missing"
        materialized_artifact = self._build_materialized_artifact(
            rows=rows if isinstance(rows, list) else [],
            mode=normalized_mode,
            cache_key=cache_key,
            invalidation_key=expected_invalidation_key,
        )
        _REGISTRY_ARTIFACT_CACHE[cache_key] = materialized_artifact
        artifact = {
            "rows": rows if isinstance(rows, list) else [],
            "artifact_version": self._artifact_version(),
            "source": source,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "stale": stale,
            "mode": normalized_mode,
            "build_meta": {
                "platform_owner": self.registry.platform_owner,
                "timings_available": bool(timings_ms),
                "snapshot_size": len(snapshot) if isinstance(snapshot, list) else 0,
                "error_count": sum(
                    len(value) for value in errors.values() if isinstance(value, list)
                ) if isinstance(errors, dict) else 0,
                "preferred_source": "materialized_kernel_registry",
                "materialized_seeded": True,
                "cache_key": cache_key,
                "contract_version": self._contract_version(),
                "schema_version": self._schema_version(),
                "mode": normalized_mode,
                "invalidation_key": expected_invalidation_key,
            },
        }
        return artifact, timings_ms
