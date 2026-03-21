# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo import api, models

from odoo.addons.smart_core.core.scene_registry_provider import load_scene_configs as registry_load_scene_configs
from odoo.addons.smart_core.core.ui_base_contract_asset_event_queue import enqueue_scene_keys


def _text(value: Any) -> str:
    return str(value or "").strip()


def _scene_keys_by_signals(env, *, action_ids: list[int] | None = None, model_names: list[str] | None = None) -> list[str]:
    try:
        payload = registry_load_scene_configs(env) or []
    except Exception:
        return []
    scenes = payload if isinstance(payload, list) else []
    action_set = {int(item) for item in (action_ids or []) if int(item or 0) > 0}
    model_set = {_text(item) for item in (model_names or []) if _text(item)}
    out: list[str] = []
    for row in scenes:
        if not isinstance(row, dict):
            continue
        scene_key = _text(row.get("code") or row.get("key"))
        if not scene_key:
            continue
        if not action_set and not model_set:
            out.append(scene_key)
            continue
        target = row.get("target") if isinstance(row.get("target"), dict) else {}
        try:
            target_action_id = int(target.get("action_id") or 0)
        except Exception:
            target_action_id = 0
        target_model = _text(target.get("model"))
        if target_action_id and target_action_id in action_set:
            out.append(scene_key)
            continue
        if target_model and target_model in model_set:
            out.append(scene_key)
            continue
    seen = set()
    unique: list[str] = []
    for key in out:
        if key in seen:
            continue
        seen.add(key)
        unique.append(key)
    return unique


def _enqueue_from_signal(env, *, reason: str, action_ids: list[int] | None = None, model_names: list[str] | None = None) -> dict:
    keys = _scene_keys_by_signals(env, action_ids=action_ids, model_names=model_names)
    return enqueue_scene_keys(env, scene_keys=keys, reason=reason)


class IrActionsActWindowAssetTrigger(models.Model):
    _inherit = "ir.actions.act_window"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        _enqueue_from_signal(
            self.env,
            reason="event:ir.actions.act_window.create",
            action_ids=list(records.ids),
            model_names=[_text(rec.res_model) for rec in records if _text(rec.res_model)],
        )
        return records

    def write(self, vals):
        result = super().write(vals)
        _enqueue_from_signal(
            self.env,
            reason="event:ir.actions.act_window.write",
            action_ids=list(self.ids),
            model_names=[_text(rec.res_model) for rec in self if _text(rec.res_model)],
        )
        return result

    def unlink(self):
        action_ids = list(self.ids)
        model_names = [_text(rec.res_model) for rec in self if _text(rec.res_model)]
        result = super().unlink()
        _enqueue_from_signal(
            self.env,
            reason="event:ir.actions.act_window.unlink",
            action_ids=action_ids,
            model_names=model_names,
        )
        return result


class IrUiViewAssetTrigger(models.Model):
    _inherit = "ir.ui.view"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        _enqueue_from_signal(
            self.env,
            reason="event:ir.ui.view.create",
            model_names=[_text(rec.model) for rec in records if _text(rec.model)],
        )
        return records

    def write(self, vals):
        result = super().write(vals)
        _enqueue_from_signal(
            self.env,
            reason="event:ir.ui.view.write",
            model_names=[_text(rec.model) for rec in self if _text(rec.model)],
        )
        return result

    def unlink(self):
        model_names = [_text(rec.model) for rec in self if _text(rec.model)]
        result = super().unlink()
        _enqueue_from_signal(
            self.env,
            reason="event:ir.ui.view.unlink",
            model_names=model_names,
        )
        return result


class ResGroupsAssetTrigger(models.Model):
    _inherit = "res.groups"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        _enqueue_from_signal(self.env, reason="event:res.groups.create")
        return records

    def write(self, vals):
        result = super().write(vals)
        _enqueue_from_signal(self.env, reason="event:res.groups.write")
        return result

    def unlink(self):
        result = super().unlink()
        _enqueue_from_signal(self.env, reason="event:res.groups.unlink")
        return result
