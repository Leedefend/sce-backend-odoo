# -*- coding: utf-8 -*-
import copy
import hashlib
import json
from datetime import datetime

from odoo import fields
from odoo.modules.module import get_module_path

from odoo.addons.smart_construction_scene import scene_registry


SCENE_CHANNELS = {"stable", "beta", "dev"}
IMPORT_STRATEGIES = {"skip_existing", "override_existing", "rename_on_conflict"}


class ScenePackageService:
    def __init__(self, env, user=None):
        self.env = env
        self.user = user or env.user

    def _config(self):
        return self.env["ir.config_parameter"].sudo()

    def _normalize_channel(self, value):
        raw = str(value or "stable").strip().lower()
        return raw if raw in SCENE_CHANNELS else "stable"

    def _safe_json_loads(self, raw, fallback):
        if not raw:
            return copy.deepcopy(fallback)
        try:
            parsed = json.loads(raw)
        except Exception:
            return copy.deepcopy(fallback)
        return parsed if isinstance(parsed, type(fallback)) else copy.deepcopy(fallback)

    def _require_reason(self, reason):
        if not reason or not str(reason).strip():
            raise ValueError("reason is required")

    def _canonicalize_scene(self, scene):
        if not isinstance(scene, dict):
            return None
        item = copy.deepcopy(scene)
        code = str(item.get("code") or item.get("key") or "").strip()
        if not code:
            return None
        item["code"] = code
        item.pop("key", None)
        return item

    def _canonicalize_scenes(self, scenes):
        out = []
        for scene in scenes or []:
            normalized = self._canonicalize_scene(scene)
            if normalized:
                out.append(normalized)
        out.sort(key=lambda row: row.get("code") or "")
        return out

    def _checksum(self, payload):
        wire = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(wire.encode("utf-8")).hexdigest()

    def _load_profiles(self, schema_version):
        normalized = str(schema_version or "v2").strip().lower()
        if not normalized.startswith("v"):
            normalized = f"v{normalized}"
        module_path = get_module_path("smart_construction_scene")
        if not module_path:
            return {}
        profile_path = f"{module_path}/schema/scene_profiles_{normalized}.json"
        try:
            with open(profile_path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    def _policy_defaults(self):
        config = self._config()
        def _safe_int(raw, fallback):
            try:
                return int(raw)
            except Exception:
                return fallback
        return {
            "auto_degrade": {
                "enabled": str(config.get_param("sc.scene.auto_degrade.enabled") or "true").strip().lower() in {"1", "true", "yes", "on"},
                "critical_threshold": {
                    "resolve_errors": _safe_int(config.get_param("sc.scene.auto_degrade.critical_threshold.resolve_errors") or 1, 1),
                    "drift_warn": _safe_int(config.get_param("sc.scene.auto_degrade.critical_threshold.drift_warn") or 1, 1),
                },
                "action": str(config.get_param("sc.scene.auto_degrade.action") or "rollback_pinned").strip().lower(),
            },
            "channel_defaults": {
                "default": self._normalize_channel(config.get_param("sc.scene.channel.default") or "stable"),
            },
        }

    def _governance_log(self, action, *, reason, payload=None, trace_id=None, company_id=None):
        try:
            self.env["sc.scene.governance.log"].sudo().create({
                "action": action,
                "actor_id": self.user.id if self.user else None,
                "company_id": company_id,
                "from_channel": None,
                "to_channel": None,
                "reason": reason,
                "trace_id": trace_id,
                "payload_json": payload or {},
                "created_at": fields.Datetime.now(),
            })
            return
        except Exception:
            pass

        try:
            self.env["sc.audit.log"].sudo().write_event(
                event_code="SCENE_GOVERNANCE_ACTION",
                model="scene.package",
                res_id=0,
                action=action,
                after={"payload": payload or {}},
                reason=reason,
                trace_id=trace_id or "",
                company_id=company_id,
            )
        except Exception:
            return

    def _installed_packages(self):
        raw = self._config().get_param("sc.scene.package.installed")
        parsed = self._safe_json_loads(raw, [])
        return parsed if isinstance(parsed, list) else []

    def _save_installed_packages(self, rows):
        self._config().set_param("sc.scene.package.installed", json.dumps(rows, ensure_ascii=True))

    def _imported_scene_map(self):
        raw = self._config().get_param("sc.scene.package.imported_scenes")
        parsed = self._safe_json_loads(raw, {})
        return parsed if isinstance(parsed, dict) else {}

    def _save_imported_scene_map(self, mapping):
        self._config().set_param("sc.scene.package.imported_scenes", json.dumps(mapping, ensure_ascii=True))

    def _validate_package(self, package_json):
        if isinstance(package_json, str):
            try:
                package_json = json.loads(package_json)
            except Exception as exc:
                raise ValueError("package_json invalid") from exc
        if not isinstance(package_json, dict):
            raise ValueError("package_json must be object")

        required = [
            "package_name",
            "package_version",
            "schema_version",
            "scene_version",
            "scenes",
            "profiles",
            "defaults",
            "policies",
            "compatibility",
            "checksum",
        ]
        for key in required:
            if key not in package_json:
                raise ValueError(f"package missing key: {key}")
        if not isinstance(package_json.get("scenes"), list):
            raise ValueError("package scenes must be list")

        payload = copy.deepcopy(package_json)
        checksum = str(payload.pop("checksum") or "").strip()
        if not checksum:
            raise ValueError("package checksum missing")
        computed = self._checksum(payload)
        if checksum != computed:
            raise ValueError("package checksum mismatch")
        payload["checksum"] = checksum
        payload["scenes"] = self._canonicalize_scenes(payload.get("scenes"))
        return payload

    def _next_renamed_code(self, base_code, existing_codes):
        idx = 1
        while True:
            candidate = f"{base_code}__pkg{idx}"
            if candidate not in existing_codes:
                return candidate
            idx += 1

    def list_packages(self):
        return {
            "items": self._installed_packages(),
            "count": len(self._installed_packages()),
        }

    def export_package(self, package_name, package_version, scene_channel="stable", reason="scene package export", trace_id=None):
        name = str(package_name or "").strip()
        version = str(package_version or "").strip()
        if not name:
            raise ValueError("package_name is required")
        if not version:
            raise ValueError("package_version is required")

        from odoo.addons.smart_core.handlers.system_init import SystemInitHandler

        channel = self._normalize_channel(scene_channel)
        handler = SystemInitHandler(
            self.env,
            self.env,
            None,
            context={"trace_id": trace_id or ""},
            payload={"params": {"scene": "web", "with_preload": False, "scene_channel": channel}},
        )
        init_result = handler.handle(payload={"params": {"scene": "web", "with_preload": False, "scene_channel": channel}})
        init_data = init_result.get("data") if isinstance(init_result, dict) else {}
        init_data = init_data if isinstance(init_data, dict) else {}

        schema_version = str(init_data.get("schema_version") or "v2")
        scene_version = str(init_data.get("scene_version") or "")
        scenes = self._canonicalize_scenes(init_data.get("scenes") if isinstance(init_data.get("scenes"), list) else [])

        payload = {
            "package_name": name,
            "package_version": version,
            "schema_version": schema_version,
            "scene_version": scene_version,
            "scenes": scenes,
            "profiles": self._load_profiles(schema_version),
            "defaults": {
                "scene_channel": channel,
                "rollback_active": str(self._config().get_param("sc.scene.rollback") or "0").strip().lower() in {"1", "true", "yes", "on"},
                "use_pinned": str(self._config().get_param("sc.scene.use_pinned") or "0").strip().lower() in {"1", "true", "yes", "on"},
            },
            "policies": self._policy_defaults(),
            "compatibility": {
                "min_core_version": "10.6.0",
                "supported_schema_versions": [schema_version],
            },
            "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        }
        checksum = self._checksum(payload)
        package = dict(payload)
        package["checksum"] = checksum

        self._governance_log(
            "package_export",
            reason=str(reason or "scene package export"),
            payload={
                "package_name": name,
                "package_version": version,
                "scene_channel": channel,
                "scene_count": len(scenes),
                "checksum": checksum,
            },
            trace_id=trace_id,
            company_id=self.user.company_id.id if self.user and self.user.company_id else None,
        )

        return {
            "action": "package_export",
            "package_name": name,
            "package_version": version,
            "scene_channel": channel,
            "scene_count": len(scenes),
            "checksum": checksum,
            "trace_id": trace_id or "",
            "package": package,
        }

    def dry_run_import(self, package_json):
        package = self._validate_package(package_json)
        existing = scene_registry.load_scene_configs(self.env)
        existing_by_code = {
            str(scene.get("code") or scene.get("key") or ""): scene
            for scene in existing if isinstance(scene, dict)
        }

        additions = []
        conflicts = []
        overwrite_fields = []
        for scene in package.get("scenes") or []:
            code = str(scene.get("code") or "").strip()
            if not code:
                continue
            if code not in existing_by_code:
                additions.append({"scene_key": code})
                continue
            current = existing_by_code.get(code) or {}
            changed = sorted(
                [
                    key for key in set(list(scene.keys()) + list(current.keys()))
                    if (scene.get(key) != current.get(key))
                ]
            )
            conflicts.append({
                "scene_key": code,
                "existing": True,
                "changed_fields": changed,
            })
            overwrite_fields.extend(changed)

        return {
            "dry_run": True,
            "package_name": package.get("package_name"),
            "package_version": package.get("package_version"),
            "checksum": package.get("checksum"),
            "summary": {
                "scene_count": len(package.get("scenes") or []),
                "additions_count": len(additions),
                "conflicts_count": len(conflicts),
            },
            "report": {
                "additions": additions,
                "conflicts": conflicts,
                "overwrite_fields": sorted(set(overwrite_fields)),
            },
        }

    def import_package(self, package_json, strategy, reason, trace_id=None):
        self._require_reason(reason)
        package = self._validate_package(package_json)
        strategy = str(strategy or "skip_existing").strip().lower()
        if strategy not in IMPORT_STRATEGIES:
            raise ValueError("invalid strategy")

        existing = scene_registry.load_scene_configs(self.env)
        existing_codes = {
            str(scene.get("code") or scene.get("key") or "")
            for scene in existing if isinstance(scene, dict)
        }

        imported_map = self._imported_scene_map()
        for key in list(imported_map.keys()):
            if not isinstance(imported_map.get(key), dict):
                imported_map.pop(key, None)

        imported_keys = []
        skipped_keys = []
        renamed = []
        all_codes = set(existing_codes) | set(imported_map.keys())

        for raw_scene in package.get("scenes") or []:
            scene = self._canonicalize_scene(raw_scene)
            if not scene:
                continue
            code = scene.get("code")
            if code in all_codes:
                if strategy == "skip_existing":
                    skipped_keys.append(code)
                    continue
                if strategy == "rename_on_conflict":
                    new_code = self._next_renamed_code(code, all_codes)
                    scene = copy.deepcopy(scene)
                    scene["code"] = new_code
                    imported_map[new_code] = scene
                    imported_keys.append(new_code)
                    renamed.append({"from": code, "to": new_code})
                    all_codes.add(new_code)
                    continue
            imported_map[code] = scene
            imported_keys.append(code)
            all_codes.add(code)

        self._save_imported_scene_map(imported_map)

        installed = self._installed_packages()
        now = datetime.utcnow().isoformat() + "Z"
        installed = [
            row for row in installed
            if not (
                str((row or {}).get("package_name") or "") == str(package.get("package_name") or "")
                and str((row or {}).get("package_version") or "") == str(package.get("package_version") or "")
            )
        ]
        installed.append({
            "package_name": package.get("package_name"),
            "package_version": package.get("package_version"),
            "schema_version": package.get("schema_version"),
            "scene_version": package.get("scene_version"),
            "scene_count": len(package.get("scenes") or []),
            "checksum": package.get("checksum"),
            "imported_at": now,
            "strategy": strategy,
        })
        installed.sort(key=lambda row: (str(row.get("package_name") or ""), str(row.get("package_version") or "")))
        self._save_installed_packages(installed)

        self._governance_log(
            "package_import",
            reason=str(reason),
            payload={
                "package_name": package.get("package_name"),
                "package_version": package.get("package_version"),
                "strategy": strategy,
                "imported_scene_keys": imported_keys,
                "skipped_scene_keys": skipped_keys,
                "renamed": renamed,
                "checksum": package.get("checksum"),
            },
            trace_id=trace_id,
            company_id=self.user.company_id.id if self.user and self.user.company_id else None,
        )

        return {
            "action": "package_import",
            "package_name": package.get("package_name"),
            "package_version": package.get("package_version"),
            "strategy": strategy,
            "imported_scene_keys": imported_keys,
            "skipped_scene_keys": skipped_keys,
            "renamed": renamed,
            "trace_id": trace_id or "",
            "summary": {
                "imported_count": len(imported_keys),
                "skipped_count": len(skipped_keys),
                "renamed_count": len(renamed),
            },
        }
