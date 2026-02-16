#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations


CONTROLLER_ROUTE_POLICY = {
    "frontend_api.py": {
        "/api/login": {"type": "json", "auth": "public", "csrf": False, "methods": {"POST"}, "cors": "*"},
        "/api/logout": {"type": "json", "auth": "public", "csrf": False, "methods": {"POST"}, "cors": "*"},
        "/api/session/get": {"type": "json", "auth": "public", "csrf": False, "methods": {"POST"}, "cors": "*"},
        "/api/menu/tree": {"type": "json", "auth": "user", "csrf": False, "methods": {"POST"}, "cors": "*"},
        "/api/user_menus": {"type": "json", "auth": "user", "csrf": False, "methods": {"POST"}, "cors": "*"},
    },
    "scene_template_controller.py": {
        "/api/scenes/export": {"type": "http", "auth": "public", "csrf": False, "methods": {"GET"}},
        "/api/scenes/import": {"type": "http", "auth": "public", "csrf": False, "methods": {"POST"}},
    },
    "pack_controller.py": {
        "/api/packs/publish": {"type": "http", "auth": "public", "csrf": False, "methods": {"POST"}},
        "/api/packs/catalog": {"type": "http", "auth": "public", "csrf": False, "methods": {"GET"}},
        "/api/packs/install": {"type": "http", "auth": "public", "csrf": False, "methods": {"POST"}},
        "/api/packs/upgrade": {"type": "http", "auth": "public", "csrf": False, "methods": {"POST"}},
    },
}

