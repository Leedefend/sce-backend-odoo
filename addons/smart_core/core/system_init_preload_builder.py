# -*- coding: utf-8 -*-
from __future__ import annotations

import logging

from odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher import ActionDispatcher
from odoo.addons.smart_core.app_config_engine.utils.misc import format_versions, stable_etag

_logger = logging.getLogger(__name__)


class SystemInitPreloadBuilder:
    def build(self, env, su_env, params: dict, default_home_action, contract_service):
        home_contract = None
        etags = {}
        parts_version = {}
        preload_items = []

        if default_home_action:
            try:
                p_home = {"subject": "action", "action_id": default_home_action, "with_data": False}
                home_data, home_versions = ActionDispatcher(env, su_env).dispatch(p_home)
                home_contract = contract_service.finalize_data(
                    home_data,
                    subject="action",
                    meta={"version": format_versions(home_versions)},
                )
                parts_version["home"] = format_versions(home_versions)
                etags["home"] = stable_etag(home_contract)
            except Exception as exc:
                _logger.warning("system.init home preload failed: action=%s, err=%s", default_home_action, exc)

        want_preload = bool(params.get("with_preload", True))
        preload_actions = params.get("preload_actions") or []
        if want_preload and preload_actions:
            for act in preload_actions:
                try:
                    p_pre = {"subject": "action", "action_id": act, "with_data": False}
                    pre_data, pre_versions = ActionDispatcher(env, su_env).dispatch(p_pre)
                    contract = contract_service.finalize_data(
                        pre_data,
                        subject="action",
                        meta={"version": format_versions(pre_versions)},
                    )
                    etag = stable_etag(contract)
                    preload_items.append({"key": act, "etag": etag})
                    parts_version[act] = format_versions(pre_versions)
                    etags[act] = etag
                except Exception as exc:
                    _logger.warning("system.init preload failed: action=%s, err=%s", act, exc)
                    continue

        return home_contract, preload_items, etags, parts_version
