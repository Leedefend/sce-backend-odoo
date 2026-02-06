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

    def _semver_key(self, version):
        raw = str(version or "").strip()
        parts = raw.split(".")
        out = []
        for part in parts:
            try:
                out.append(int(part))
            except Exception:
                out.append(0)
        while len(out) < 3:
            out.append(0)
        return tuple(out[:3])

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
        # Compatibility fallback for legacy storage before installation registry model was introduced.
        raw = self._config().get_param("sc.scene.package.installed")
        parsed = self._safe_json_loads(raw, [])
        return parsed if isinstance(parsed, list) else []

    def _normalize_installation_row(self, row):
        item = row if isinstance(row, dict) else {}
        package_name = str(item.get("package_name") or "").strip()
        installed_version = str(item.get("installed_version") or item.get("package_version") or "").strip()
        return {
            "package_name": package_name,
            "installed_version": installed_version,
            "channel": str(item.get("channel") or "").strip(),
            "installed_at": item.get("installed_at") or item.get("imported_at"),
            "last_upgrade_at": item.get("last_upgrade_at"),
            "source": str(item.get("source") or "import"),
            "checksum": str(item.get("checksum") or "").strip(),
            "active": bool(item.get("active", True)),
        }

    def _list_installed_packages(self):
        try:
            rows = self.env["sc.scene.package.installation"].sudo().search([], order="installed_at desc, id desc")
        except Exception:
            return [self._normalize_installation_row(row) for row in self._installed_packages()]
        return [self._normalize_installation_row({
            "package_name": row.package_name,
            "installed_version": row.installed_version,
            "channel": row.channel,
            "installed_at": row.installed_at,
            "last_upgrade_at": row.last_upgrade_at,
            "source": row.source,
            "checksum": row.checksum,
            "active": row.active,
        }) for row in rows]

    def _record_installation(self, *, package_name, package_version, channel, source, checksum):
        try:
            Installation = self.env["sc.scene.package.installation"].sudo()
            active_current = Installation.search([
                ("package_name", "=", package_name),
                ("active", "=", True),
            ])
            from_version = None
            if active_current:
                versions = [str(row.installed_version or "").strip() for row in active_current if row.installed_version]
                if versions:
                    from_version = sorted(set(versions), key=self._semver_key)[-1]
            last_upgrade_at = fields.Datetime.now() if active_current else False
            if active_current:
                active_current.write({"active": False})
            created = Installation.create({
                "package_name": package_name,
                "installed_version": package_version,
                "installed_at": fields.Datetime.now(),
                "last_upgrade_at": last_upgrade_at,
                "channel": channel,
                "source": source,
                "checksum": checksum or "",
                "active": True,
            })
            return created, from_version
        except Exception:
            # Keep import path backward compatible if registry model/table is not ready yet.
            installed = self._installed_packages()
            from_version = None
            for row in installed:
                if str((row or {}).get("package_name") or "") != package_name:
                    continue
                val = str((row or {}).get("installed_version") or (row or {}).get("package_version") or "").strip()
                if val and (from_version is None or self._semver_key(val) > self._semver_key(from_version)):
                    from_version = val
                if bool((row or {}).get("active")):
                    row["active"] = False
            installed.append({
                "package_name": package_name,
                "installed_version": package_version,
                "channel": channel,
                "installed_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
                "last_upgrade_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z" if from_version else None,
                "source": source,
                "checksum": checksum or "",
                "active": True,
            })
            self._config().set_param("sc.scene.package.installed", json.dumps(installed, ensure_ascii=True))
            return None, from_version

    def _known_versions(self, package_name):
        name = str(package_name or "").strip()
        if not name:
            return []
        versions = []
        try:
            rows = self.env["sc.scene.package.installation"].sudo().search([
                ("package_name", "=", name),
            ])
            versions.extend([str(row.installed_version or "").strip() for row in rows])
        except Exception:
            pass
        legacy = self._installed_packages()
        for row in legacy:
            if str((row or {}).get("package_name") or "").strip() != name:
                continue
            val = str((row or {}).get("package_version") or (row or {}).get("installed_version") or "").strip()
            if val:
                versions.append(val)
        unique = sorted(set([v for v in versions if v]), key=self._semver_key)
        return unique

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
        items = self._list_installed_packages()
        return {
            "items": items,
            "count": len(items),
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
        previous_versions = [v for v in self._known_versions(name) if v != version]

        payload = {
            "package_name": name,
            "package_version": version,
            "schema_version": schema_version,
            "scene_version": scene_version,
            "previous_versions": previous_versions,
            "upgrade": {
                "type": "inplace",
                "supported_from": previous_versions,
                "breaking": False,
            },
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

        installation, from_version = self._record_installation(
            package_name=str(package.get("package_name") or ""),
            package_version=str(package.get("package_version") or ""),
            channel=self._normalize_channel((package.get("defaults") or {}).get("scene_channel") if isinstance(package.get("defaults"), dict) else "stable"),
            source="import",
            checksum=str(package.get("checksum") or ""),
        )

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
        self._governance_log(
            "package_install",
            reason=str(reason),
            payload={
                "package_name": package.get("package_name"),
                "from_version": from_version,
                "to_version": package.get("package_version"),
                "strategy": strategy,
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
            "installation": {
                "id": installation.id if installation else None,
                "package_name": installation.package_name if installation else package.get("package_name"),
                "installed_version": installation.installed_version if installation else package.get("package_version"),
                "active": bool(installation.active) if installation else True,
            },
        }
