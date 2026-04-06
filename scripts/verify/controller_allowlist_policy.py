#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations


CONTROLLER_ROUTE_POLICY = {
    "addons/smart_core/controllers/platform_session_api.py": {
        "/api/login": {"type": "json", "auth": "public", "csrf": False, "methods": {"POST"}, "cors": "*"},
        "/api/logout": {"type": "json", "auth": "public", "csrf": False, "methods": {"POST"}, "cors": "*"},
        "/api/session/get": {"type": "json", "auth": "public", "csrf": False, "methods": {"POST"}, "cors": "*"},
    },
    "addons/smart_core/controllers/platform_menu_api.py": {
        "/api/menu/tree": {"type": "json", "auth": "user", "csrf": False, "methods": {"POST"}, "cors": "*"},
        "/api/user_menus": {"type": "json", "auth": "user", "csrf": False, "methods": {"POST"}, "cors": "*"},
    },
    "addons/smart_core/controllers/platform_execute_api.py": {
        "/api/execute_button": {"type": "http", "auth": "user", "csrf": False, "methods": {"POST"}},
    },
    "addons/smart_core/controllers/platform_portal_execute_api.py": {
        "/api/contract/portal_execute_button": {"type": "http", "auth": "user", "csrf": False, "methods": {"GET"}},
        "/api/portal/execute_button": {"type": "http", "auth": "user", "csrf": False, "methods": {"POST"}},
    },
    "addons/smart_core/controllers/platform_ui_contract_api.py": {
        "/api/ui/contract": {"type": "http", "auth": "user", "csrf": False, "methods": {"GET", "POST"}},
    },
    "addons/smart_core/controllers/platform_scene_template_api.py": {
        "/api/scenes/export": {"type": "http", "auth": "public", "csrf": False, "methods": {"GET"}},
        "/api/scenes/import": {"type": "http", "auth": "public", "csrf": False, "methods": {"POST"}},
    },
    "addons/smart_core/controllers/platform_packs_api.py": {
        "/api/packs/publish": {"type": "http", "auth": "public", "csrf": False, "methods": {"POST"}},
        "/api/packs/catalog": {"type": "http", "auth": "public", "csrf": False, "methods": {"GET"}},
        "/api/packs/install": {"type": "http", "auth": "public", "csrf": False, "methods": {"POST"}},
        "/api/packs/upgrade": {"type": "http", "auth": "public", "csrf": False, "methods": {"POST"}},
    },
}


CONTROLLER_DELEGATE_ALLOWLIST = {
    "frontend_api.py",
    "execute_controller.py",
    "portal_execute_button_controller.py",
    "ui_contract_controller.py",
    "scene_template_controller.py",
    "pack_controller.py",
}
