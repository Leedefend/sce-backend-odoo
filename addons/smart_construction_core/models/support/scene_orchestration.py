# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class ScCapability(models.Model):
    _name = "sc.capability"
    _description = "SC Capability Catalog"
    _order = "sequence, id"

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    key = fields.Char(required=True, index=True)
    name = fields.Char(required=True)
    ui_label = fields.Char()
    ui_hint = fields.Char()
    intent = fields.Char(help="Intent to execute, e.g. ui.contract / api.data / execute_button")
    required_flag = fields.Char(help="Entitlement flag required to use this capability")
    default_payload = fields.Json()
    required_group_ids = fields.Many2many("res.groups", string="Required Groups")
    role_scope = fields.Char(help="Comma-separated role codes, e.g. project_manager,finance_manager")
    capability_scope = fields.Char(help="Comma-separated dependency capability keys")
    tags = fields.Char(help="Comma-separated tags, e.g. project,contract,cost")
    status = fields.Selection(
        [("alpha", "Alpha"), ("beta", "Beta"), ("ga", "GA")],
        default="alpha",
        required=True,
    )
    version = fields.Char(default="v0.1")
    smoke_test = fields.Boolean(default=False, help="Include in capability smoke tests")
    is_test = fields.Boolean(default=False, help="Mark as test-only capability (excluded from lint by default)")

    _sql_constraints = [
        ("sc_capability_key_uniq", "unique(key)", "Capability key must be unique."),
    ]

    def _user_allowed(self, user):
        self.ensure_one()
        return bool(self._access_context(user).get("allowed"))

    def _user_visible(self, user):
        self.ensure_one()
        return bool(self._access_context(user).get("visible"))

    @api.model
    def _csv_items(self, raw):
        if not raw:
            return []
        return [x.strip() for x in str(raw).split(",") if x and x.strip()]

    def _role_codes_for_user(self, user):
        if not user:
            return set()
        role_codes = set()
        group_xmlids = user.groups_id.get_external_id().values()
        prefix = "smart_construction_core.group_sc_role_"
        for xmlid in group_xmlids:
            if isinstance(xmlid, str) and xmlid.startswith(prefix):
                role_codes.add(xmlid[len(prefix):])
        if user.has_group("base.group_system"):
            role_codes.add("admin")
        return role_codes

    def _flag_enabled(self, flags, flag):
        if not flag:
            return True
        val = (flags or {}).get(flag)
        if isinstance(val, bool):
            return val is True
        if isinstance(val, (int, float)):
            return val == 1
        if isinstance(val, str):
            return val.strip().lower() in {"1", "true", "yes", "y", "on"}
        return False

    @api.model
    def _reason_message(self, reason_code):
        code = str(reason_code or "").upper()
        reason_map = {
            "CAPABILITY_SCOPE_CYCLE": _("能力依赖存在循环"),
            "ROLE_SCOPE_MISMATCH": _("角色范围不匹配"),
            "PERMISSION_DENIED": _("权限不足"),
            "FEATURE_DISABLED": _("订阅未开通"),
            "CAPABILITY_SCOPE_MISSING": _("缺少前置能力"),
            "ACCESS_RESTRICTED": _("当前能力不可用"),
        }
        return reason_map.get(code) or _("当前能力不可用")

    @api.model
    def _normalize_access_result(self, access):
        data = dict(access or {})
        state = str(data.get("state") or "").upper()
        reason_code = str(data.get("reason_code") or "").upper()
        reason = str(data.get("reason") or "")
        if state == "LOCKED":
            if not reason_code:
                reason_code = "ACCESS_RESTRICTED"
            if not reason:
                reason = self._reason_message(reason_code)
        data["state"] = state
        data["reason_code"] = reason_code
        data["reason"] = reason
        return data

    def _access_context(self, user):
        return self._normalize_access_result(self._access_context_inner(user, seen=set()))

    def _access_context_inner(self, user, seen):
        self.ensure_one()
        seen = set(seen or set())
        cap_key = str(self.key or f"id:{self.id}")
        if cap_key in seen:
            return self._normalize_access_result({
                "visible": True,
                "allowed": False,
                "state": "LOCKED",
                "reason_code": "CAPABILITY_SCOPE_CYCLE",
                "reason": self._reason_message("CAPABILITY_SCOPE_CYCLE"),
            })
        seen.add(cap_key)

        # Role/group mismatch: hide from directory.
        role_scope_items = self._csv_items(self.role_scope)
        if role_scope_items:
            role_codes = self._role_codes_for_user(user)
            if not (set(role_scope_items) & role_codes):
                return self._normalize_access_result({
                    "visible": False,
                    "allowed": False,
                    "state": "LOCKED",
                    "reason_code": "ROLE_SCOPE_MISMATCH",
                    "reason": self._reason_message("ROLE_SCOPE_MISMATCH"),
                })
        if self.required_group_ids and not bool(self.required_group_ids & user.groups_id):
            return self._normalize_access_result({
                "visible": False,
                "allowed": False,
                "state": "LOCKED",
                "reason_code": "PERMISSION_DENIED",
                "reason": self._reason_message("PERMISSION_DENIED"),
            })

        reason_code = ""
        reason = ""
        allowed = True

        # Entitlement mismatch: visible but locked.
        if self.required_flag:
            flags = {}
            Entitlement = self.env.get("sc.entitlement")
            if Entitlement and user:
                try:
                    payload = Entitlement.get_payload(user) or {}
                    flags = payload.get("flags") or {}
                except Exception:
                    flags = {}
            if not self._flag_enabled(flags, self.required_flag):
                allowed = False
                reason_code = "FEATURE_DISABLED"
                reason = self._reason_message("FEATURE_DISABLED")

        # Capability dependency mismatch: visible but locked.
        dep_keys = self._csv_items(self.capability_scope)
        if dep_keys:
            deps = self.sudo().search([("key", "in", dep_keys), ("active", "=", True)])
            dep_map = {cap.key: cap for cap in deps}
            missing = []
            for key in dep_keys:
                dep = dep_map.get(key)
                if not dep:
                    missing.append(key)
                    continue
                dep_access = dep._access_context_inner(user, seen=seen)
                if not dep_access.get("allowed"):
                    missing.append(key)
            if missing:
                allowed = False
                reason_code = "CAPABILITY_SCOPE_MISSING"
                reason = _("缺少前置能力: %s") % ",".join(missing)

        state = "READY" if self.status == "ga" else "PREVIEW"
        if not allowed:
            state = "LOCKED"
        return self._normalize_access_result({
            "visible": True,
            "allowed": allowed,
            "state": state,
            "reason_code": reason_code,
            "reason": reason,
        })

    def _resolve_payload(self, payload):
        resolved = dict(payload or {})
        if resolved.get("action_xmlid") and not resolved.get("action_id"):
            action_ref = self.env.ref(resolved.get("action_xmlid"), raise_if_not_found=False)
            if action_ref:
                resolved["action_id"] = action_ref.id
        if resolved.get("menu_xmlid") and not resolved.get("menu_id"):
            menu_ref = self.env.ref(resolved.get("menu_xmlid"), raise_if_not_found=False)
            if menu_ref:
                resolved["menu_id"] = menu_ref.id
        return resolved

    def to_public_dict(self, user):
        self.ensure_one()
        group_xmlids = self.required_group_ids.get_external_id()
        payload = self._resolve_payload(self.default_payload or {})
        access = self._access_context(user)
        return {
            "key": self.key,
            "name": self.name,
            "ui_label": self.ui_label or self.name,
            "ui_hint": self.ui_hint or "",
            "intent": self.intent or "",
            "required_flag": self.required_flag or "",
            "default_payload": payload,
            "required_groups": [
                group_xmlids.get(g.id)
                for g in self.required_group_ids
                if group_xmlids.get(g.id)
            ],
            "role_scope": self._csv_items(self.role_scope),
            "capability_scope": self._csv_items(self.capability_scope),
            "tags": [t.strip() for t in (self.tags or "").split(",") if t.strip()],
            "status": self.status,
            "version": self.version,
            "smoke_test": bool(self.smoke_test),
            "state": access.get("state"),
            "reason_code": access.get("reason_code"),
            "reason": access.get("reason"),
        }

    @api.model
    def lint_capabilities(self, ignore_keys=None, include_tests=False):
        issues = []
        domain = [("active", "=", True)]
        if not include_tests:
            domain.append(("is_test", "=", False))
        caps = self.search(domain, order="sequence, id")
        allowed_intents = self.env["sc.scene"].browse()._get_allowed_intents()
        ignore_set = {k for k in (ignore_keys or []) if k}
        seen_keys = {}
        for cap in caps:
            if not cap.is_test and isinstance(cap.key, str) and cap.key.startswith("scene.validation."):
                # Auto-heal legacy test-only capabilities created by smoke imports.
                try:
                    cap.sudo().write({"is_test": True})
                except Exception:
                    pass
            if cap.is_test and not include_tests:
                continue
            if cap.key in ignore_set:
                continue
            if cap.key in seen_keys:
                issues.append({
                    "code": "DUPLICATE_KEY",
                    "message": _("Duplicate capability key."),
                    "detail": {"capability_key": cap.key, "capability_id": cap.id},
                })
            seen_keys[cap.key] = cap.id

            if not cap.intent:
                issues.append({
                    "code": "INTENT_MISSING",
                    "message": _("Capability intent is missing."),
                    "detail": {"capability_key": cap.key},
                })
            elif cap.intent not in allowed_intents:
                issues.append({
                    "code": "INTENT_NOT_ALLOWED",
                    "message": _("Capability intent is not allowed."),
                    "detail": {"capability_key": cap.key, "intent": cap.intent},
                })

            if cap.required_group_ids:
                group_xmlids = cap.required_group_ids.get_external_id()
                missing = [
                    g.id for g in cap.required_group_ids if not group_xmlids.get(g.id)
                ]
                if missing:
                    issues.append({
                        "code": "GROUP_XMLID_MISSING",
                        "message": _("Required groups missing xmlid."),
                        "detail": {"capability_key": cap.key, "group_ids": missing},
                    })

            role_scope_items = self._csv_items(cap.role_scope)
            if role_scope_items:
                known_roles = set()
                groups = self.env["res.groups"].sudo().search([
                    ("category_id", "=", self.env.ref("smart_construction_core.module_category_smart_construction").id),
                ])
                for xmlid in groups.get_external_id().values():
                    prefix = "smart_construction_core.group_sc_role_"
                    if isinstance(xmlid, str) and xmlid.startswith(prefix):
                        known_roles.add(xmlid[len(prefix):])
                unknown_roles = [r for r in role_scope_items if r not in known_roles]
                if unknown_roles:
                    issues.append({
                        "code": "ROLE_SCOPE_UNKNOWN",
                        "message": _("Role scope contains unknown role codes."),
                        "detail": {"capability_key": cap.key, "role_scope": unknown_roles},
                    })

            for dep_key in self._csv_items(cap.capability_scope):
                dep = self.search([("key", "=", dep_key)], limit=1)
                if not dep:
                    issues.append({
                        "code": "CAPABILITY_SCOPE_NOT_FOUND",
                        "message": _("Capability scope key not found."),
                        "detail": {"capability_key": cap.key, "dependency": dep_key},
                    })

            payload = cap.default_payload or {}
            menu_xmlid = payload.get("menu_xmlid")
            if menu_xmlid and not self.env.ref(menu_xmlid, raise_if_not_found=False):
                issues.append({
                    "code": "MENU_XMLID_NOT_FOUND",
                    "message": _("Menu xmlid not found."),
                    "detail": {"capability_key": cap.key, "menu_xmlid": menu_xmlid},
                })
            action_xmlid = payload.get("action_xmlid")
            if action_xmlid and not self.env.ref(action_xmlid, raise_if_not_found=False):
                issues.append({
                    "code": "ACTION_XMLID_NOT_FOUND",
                    "message": _("Action xmlid not found."),
                    "detail": {"capability_key": cap.key, "action_xmlid": action_xmlid},
                })
            menu_id = payload.get("menu_id")
            if menu_id:
                try:
                    if not self.env["ir.ui.menu"].browse(int(menu_id)).exists():
                        raise ValueError
                except Exception:
                    issues.append({
                        "code": "MENU_ID_NOT_FOUND",
                        "message": _("Menu id not found."),
                        "detail": {"capability_key": cap.key, "menu_id": menu_id},
                    })
            action_id = payload.get("action_id")
            if action_id:
                try:
                    if not self.env["ir.actions.actions"].browse(int(action_id)).exists():
                        raise ValueError
                except Exception:
                    issues.append({
                        "code": "ACTION_ID_NOT_FOUND",
                        "message": _("Action id not found."),
                        "detail": {"capability_key": cap.key, "action_id": action_id},
                    })

        return issues


class ScScene(models.Model):
    _name = "sc.scene"
    _description = "SC Scene"
    _order = "sequence, id"

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    layout = fields.Selection([("grid", "Grid"), ("flow", "Flow")], default="grid")
    is_default = fields.Boolean(default=False)
    is_test = fields.Boolean(default=False, help="Mark as test-only scene (hidden by default).")
    version = fields.Char(default="v0.1")
    state = fields.Selection(
        [("draft", "Draft"), ("published", "Published"), ("archived", "Archived")],
        default="draft",
        required=True,
    )
    published_at = fields.Datetime()
    published_by = fields.Many2one("res.users")
    active_version_id = fields.Many2one("sc.scene.version", ondelete="set null")
    target_group_ids = fields.Many2many("res.groups", string="Target Groups")
    description = fields.Char()
    tile_ids = fields.One2many("sc.scene.tile", "scene_id", string="Tiles")

    _sql_constraints = [
        ("sc_scene_code_uniq", "unique(code)", "Scene code must be unique."),
    ]

    def _user_allowed(self, user):
        if not self.target_group_ids:
            return True
        return bool(self.target_group_ids & user.groups_id)

    def to_public_dict(self, user):
        self.ensure_one()
        version_payload = self.active_version_id.payload_json if self.active_version_id else None
        if self.state == "published" and isinstance(version_payload, dict):
            payload = dict(version_payload)
            payload["tiles"] = self._filter_payload_tiles(payload.get("tiles") or [], user)
            return payload
        tiles = []
        for tile in self.tile_ids.filtered(lambda t: t.active and t.visible):
            if tile.capability_id and not tile.capability_id._user_visible(user):
                continue
            tiles.append(tile.to_public_dict(user))
        return {
            "code": self.code,
            "name": self.name,
            "layout": self.layout,
            "is_default": bool(self.is_default),
            "is_test": bool(self.is_test),
            "version": self.version,
            "tiles": tiles,
        }

    def _build_version_payload(self, user=None):
        self.ensure_one()
        user = user or self.env.user
        tiles = []
        for tile in self.tile_ids.filtered(lambda t: t.active and t.visible):
            if tile.capability_id and not tile.capability_id._user_visible(user):
                continue
            tiles.append(tile.to_public_dict(user))
        return {
            "code": self.code,
            "name": self.name,
            "layout": self.layout,
            "is_default": bool(self.is_default),
            "is_test": bool(self.is_test),
            "version": self.version,
            "tiles": tiles,
        }

    def _filter_payload_tiles(self, payload_tiles, user):
        Cap = self.env["sc.capability"].sudo()
        keys = [str(tile.get("key") or "") for tile in payload_tiles if isinstance(tile, dict)]
        caps = Cap.search([("key", "in", [k for k in keys if k]), ("active", "=", True)])
        cap_map = {cap.key: cap for cap in caps}
        filtered = []
        for tile in payload_tiles:
            if not isinstance(tile, dict):
                continue
            key = str(tile.get("key") or "")
            cap = cap_map.get(key)
            if not cap:
                continue
            if not cap._user_visible(user):
                continue
            access = cap._access_context(user)
            item = dict(tile)
            item["status"] = cap.status
            item["role_scope"] = cap._csv_items(cap.role_scope)
            item["capability_scope"] = cap._csv_items(cap.capability_scope)
            item["allowed"] = bool(access.get("allowed"))
            item["user_visible"] = bool(access.get("visible"))
            item["state"] = access.get("state")
            item["reason_code"] = access.get("reason_code")
            item["reason"] = access.get("reason")
            filtered.append(item)
        return filtered

    def _get_allowed_intents(self):
        param = self.env["ir.config_parameter"].sudo().get_param("sc.scene.allowed_intents", "")
        if param:
            return {v.strip() for v in param.split(",") if v.strip()}
        return {
            "ui.contract",
            "api.data",
            "execute_button",
            "system.init",
            "system.ping",
            "login",
        }

    def _validate_scene(self):
        self.ensure_one()
        issues = []
        allowed_intents = self._get_allowed_intents()
        group_xmlids = {}
        for tile in self.tile_ids.filtered(lambda t: t.active and t.visible):
            cap = tile.capability_id
            if not cap:
                issues.append({
                    "code": "CAPABILITY_MISSING",
                    "message": _("Tile has no capability."),
                    "detail": {"tile_id": tile.id},
                })
                continue
            if not cap.active:
                issues.append({
                    "code": "CAPABILITY_INACTIVE",
                    "message": _("Capability is inactive."),
                    "detail": {"tile_id": tile.id, "capability_key": cap.key},
                })
            if cap.intent and cap.intent not in allowed_intents:
                issues.append({
                    "code": "INTENT_NOT_ALLOWED",
                    "message": _("Capability intent is not allowed."),
                    "detail": {"tile_id": tile.id, "capability_key": cap.key, "intent": cap.intent},
                })

            if cap.required_group_ids:
                if not group_xmlids:
                    group_xmlids = cap.required_group_ids.get_external_id()
                missing = [
                    g.id for g in cap.required_group_ids if not group_xmlids.get(g.id)
                ]
                if missing:
                    issues.append({
                        "code": "GROUP_XMLID_MISSING",
                        "message": _("Required groups missing xmlid."),
                        "detail": {"tile_id": tile.id, "capability_key": cap.key, "group_ids": missing},
                    })

            payload = tile._merge_payload(cap.default_payload or {}, tile.payload_override or {})
            menu_xmlid = payload.get("menu_xmlid")
            if menu_xmlid:
                if not self.env.ref(menu_xmlid, raise_if_not_found=False):
                    issues.append({
                        "code": "MENU_XMLID_NOT_FOUND",
                        "message": _("Menu xmlid not found."),
                        "detail": {"tile_id": tile.id, "menu_xmlid": menu_xmlid},
                    })
            action_xmlid = payload.get("action_xmlid")
            if action_xmlid:
                if not self.env.ref(action_xmlid, raise_if_not_found=False):
                    issues.append({
                        "code": "ACTION_XMLID_NOT_FOUND",
                        "message": _("Action xmlid not found."),
                        "detail": {"tile_id": tile.id, "action_xmlid": action_xmlid},
                    })
            menu_id = payload.get("menu_id")
            if menu_id:
                if not self.env["ir.ui.menu"].browse(int(menu_id)).exists():
                    issues.append({
                        "code": "MENU_ID_NOT_FOUND",
                        "message": _("Menu id not found."),
                        "detail": {"tile_id": tile.id, "menu_id": menu_id},
                    })
            action_id = payload.get("action_id")
            if action_id:
                if not self.env["ir.actions.actions"].browse(int(action_id)).exists():
                    issues.append({
                        "code": "ACTION_ID_NOT_FOUND",
                        "message": _("Action id not found."),
                        "detail": {"tile_id": tile.id, "action_id": action_id},
                    })

        status = "pass" if not issues else "fail"
        validation = self.env["sc.scene.validation"].sudo().create({
            "scene_id": self.id,
            "status": status,
            "issues_json": issues,
            "checked_at": fields.Datetime.now(),
            "checked_by": self.env.user.id,
        })
        return status, issues, validation

    def _log_audit(self, event, version=None, payload_diff=None):
        self.env["sc.scene.audit.log"].sudo().create({
            "event": event,
            "actor_user_id": self.env.user.id,
            "scene_id": self.id,
            "version_id": version.id if version else None,
            "payload_diff": payload_diff or {},
            "created_at": fields.Datetime.now(),
        })

    def action_publish(self):
        for scene in self:
            Entitlement = scene.env.get("sc.entitlement")
            Usage = scene.env.get("sc.usage.counter")
            if Entitlement:
                ent = Entitlement.get_effective(scene.env.user.company_id)
                limits = ent.effective_limits_json or {}
                max_scenes = int(limits.get("max_scenes") or 0)
                if max_scenes:
                    current = None
                    if Usage:
                        current = Usage.get_usage_map(scene.env.user.company_id).get("scenes_published")
                    if current is None:
                        current = scene.env["sc.scene"].search_count([
                            ("active", "=", True),
                            ("state", "=", "published"),
                            ("is_test", "=", False),
                        ])
                    if current >= max_scenes:
                        raise UserError(
                            _("LIMIT_EXCEEDED: max_scenes=%s current=%s") % (max_scenes, current)
                        )
            status, issues, validation = scene._validate_scene()
            if status != "pass":
                raise UserError(
                    _("Scene validation failed. Please fix issues before publish. (validation_id=%s)")
                    % validation.id
                )
            payload = scene._build_version_payload(scene.env.user)
            version_seq = scene.env["sc.scene.version"].search_count([("scene_id", "=", scene.id)]) + 1
            ver = scene.env["sc.scene.version"].create({
                "scene_id": scene.id,
                "version": f"v{version_seq}",
                "payload_json": payload,
                "note": self.env.context.get("publish_note") or "",
                "source": self.env.context.get("publish_source") or "manual",
            })
            scene.write({
                "active_version_id": ver.id,
                "state": "published",
                "published_at": fields.Datetime.now(),
                "published_by": scene.env.user.id,
            })
            scene._log_audit("publish", version=ver)
            if Usage:
                Usage.bump(scene.env.user.company_id, "scenes_published", 1)

    def action_archive(self):
        self.write({"state": "archived"})
        for scene in self:
            scene._log_audit("archive")

    def action_set_active_version(self, version_id):
        version = self.env["sc.scene.version"].browse(version_id)
        if version and version.scene_id and version.scene_id.id in self.ids:
            version.scene_id.write({
                "active_version_id": version.id,
                "state": "published",
                "published_at": fields.Datetime.now(),
                "published_by": self.env.user.id,
            })
            version.scene_id._log_audit("rollback", version=version)


class ScSceneTile(models.Model):
    _name = "sc.scene.tile"
    _description = "SC Scene Tile"
    _order = "sequence, id"

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    scene_id = fields.Many2one("sc.scene", required=True, ondelete="cascade")
    capability_id = fields.Many2one("sc.capability", required=True, ondelete="restrict")
    title = fields.Char()
    subtitle = fields.Char()
    icon = fields.Char()
    badge = fields.Char()
    visible = fields.Boolean(default=True)
    span = fields.Integer(default=1)
    min_width = fields.Integer(default=200)
    payload_override = fields.Json()
    version = fields.Char(default="v0.1")

    def _merge_payload(self, base_payload, override_payload):
        payload = dict(base_payload or {})
        if isinstance(override_payload, dict):
            payload.update(override_payload)
        return payload

    def to_public_dict(self, user):
        self.ensure_one()
        cap = self.capability_id
        payload = self._merge_payload(cap.default_payload or {}, self.payload_override or {})
        if payload.get("action_xmlid") and not payload.get("action_id"):
            action_ref = self.env.ref(payload.get("action_xmlid"), raise_if_not_found=False)
            if action_ref:
                payload["action_id"] = action_ref.id
        if payload.get("menu_xmlid") and not payload.get("menu_id"):
            menu_ref = self.env.ref(payload.get("menu_xmlid"), raise_if_not_found=False)
            if menu_ref:
                payload["menu_id"] = menu_ref.id
        access = cap._access_context(user)
        return {
            "key": cap.key,
            "title": self.title or cap.ui_label or cap.name,
            "subtitle": self.subtitle or cap.ui_hint or "",
            "icon": self.icon or "",
            "badge": self.badge or "",
            "sequence": self.sequence,
            "visible": bool(self.visible),
            "span": self.span,
            "min_width": self.min_width,
            "intent": cap.intent or "",
            "payload": payload,
            "status": cap.status,
            "version": cap.version,
            "role_scope": cap._csv_items(cap.role_scope),
            "capability_scope": cap._csv_items(cap.capability_scope),
            "allowed": bool(access.get("allowed")),
            "user_visible": bool(access.get("visible")),
            "state": access.get("state"),
            "reason_code": access.get("reason_code"),
            "reason": access.get("reason"),
        }


class ScSceneVersion(models.Model):
    _name = "sc.scene.version"
    _description = "SC Scene Version"
    _order = "create_date desc, id desc"

    scene_id = fields.Many2one("sc.scene", required=True, ondelete="cascade")
    version = fields.Char(required=True)
    payload_json = fields.Json(required=True)
    note = fields.Char()
    source = fields.Selection(
        [("manual", "Manual"), ("import", "Import"), ("system", "System")],
        default="manual",
    )
    create_date = fields.Datetime(readonly=True)
    create_uid = fields.Many2one("res.users", readonly=True)


class ScUserPreference(models.Model):
    _name = "sc.user.preference"
    _description = "SC User Preference"
    _order = "id desc"

    user_id = fields.Many2one("res.users", required=True, index=True, ondelete="cascade")
    default_scene_id = fields.Many2one("sc.scene", ondelete="set null")
    pinned_tile_keys = fields.Json()
    recent_tiles = fields.Json()

    _sql_constraints = [
        ("sc_user_pref_user_uniq", "unique(user_id)", "Preference already exists for user."),
    ]

    @classmethod
    def get_or_create(cls, env, user):
        pref = env["sc.user.preference"].sudo().search([("user_id", "=", user.id)], limit=1)
        if pref:
            return pref
        return env["sc.user.preference"].sudo().create({"user_id": user.id})


class ScSceneValidation(models.Model):
    _name = "sc.scene.validation"
    _description = "SC Scene Validation"
    _order = "checked_at desc, id desc"

    scene_id = fields.Many2one("sc.scene", required=True, ondelete="cascade")
    status = fields.Selection([("pass", "Pass"), ("fail", "Fail")], required=True)
    issues_json = fields.Json()
    checked_at = fields.Datetime()
    checked_by = fields.Many2one("res.users")


class ScSceneAuditLog(models.Model):
    _name = "sc.scene.audit.log"
    _description = "SC Scene Audit Log"
    _order = "created_at desc, id desc"

    event = fields.Selection(
        [
            ("publish", "Publish"),
            ("rollback", "Rollback"),
            ("archive", "Archive"),
            ("import", "Import"),
            ("export", "Export"),
            ("update_pref", "Update Preference"),
        ],
        required=True,
    )
    actor_user_id = fields.Many2one("res.users")
    scene_id = fields.Many2one("sc.scene", ondelete="set null")
    version_id = fields.Many2one("sc.scene.version", ondelete="set null")
    payload_diff = fields.Json()
    created_at = fields.Datetime()


class ScCapabilityAuditLog(models.Model):
    _name = "sc.capability.audit.log"
    _description = "SC Capability Audit Log"
    _order = "created_at desc, id desc"

    event = fields.Selection(
        [
            ("create", "Create"),
            ("update", "Update"),
            ("import", "Import"),
        ],
        required=True,
    )
    actor_user_id = fields.Many2one("res.users")
    capability_id = fields.Many2one("sc.capability", ondelete="set null")
    source_pack_id = fields.Char()
    payload_diff = fields.Json()
    created_at = fields.Datetime()
