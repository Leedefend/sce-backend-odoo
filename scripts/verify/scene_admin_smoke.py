#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_get_json, http_post_json


def _cleanup_test_pack(import_url: str, auth_header: dict, payload: dict) -> None:
    http_post_json(
        import_url,
        {
            "cleanup_test": True,
            "capabilities": payload.get("capabilities"),
            "scenes": payload.get("scenes"),
        },
        headers=auth_header,
    )


def _require_deprecation(payload: dict, *, label: str) -> None:
    dep = payload.get("deprecation") if isinstance(payload.get("deprecation"), dict) else {}
    if (dep.get("status") or "").strip().lower() != "deprecated":
        raise RuntimeError(f"{label} missing deprecation.status=deprecated")
    if not str(dep.get("replacement") or "").strip():
        raise RuntimeError(f"{label} missing deprecation.replacement")
    if not str(dep.get("sunset_date") or "").strip():
        raise RuntimeError(f"{label} missing deprecation.sunset_date")


def main():
    base_url = get_base_url()
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"

    intent_url = f"{base_url}/api/v1/intent"
    scenes_url = f"{base_url}/api/scenes/my"
    scenes_url_tests = f"{scenes_url}?include_tests=1"
    pref_get_url = f"{base_url}/api/preferences/get"
    pref_set_url = f"{base_url}/api/preferences/set"
    export_url = f"{base_url}/api/scenes/export"
    import_url = f"{base_url}/api/scenes/import"

    # login (JWT)
    login_payload = {
        "intent": "login",
        "params": {"db": db_name, "login": login, "password": password},
    }
    status, login_resp = http_post_json(
        intent_url, login_payload, headers={"X-Anonymous-Intent": "1"}
    )
    require_ok(status, login_resp, "login")
    token = (login_resp.get("data") or {}).get("token")
    if not token:
        raise RuntimeError("login response missing token")
    auth_header = {"Authorization": f"Bearer {token}"}

    created_test = False
    seed_payload = {
        "mode": "merge",
        "capabilities": [
            {
                "key": "scene.smoke.default",
                "name": "Scene Smoke Default",
                "intent": "system.ping",
                "is_test": True,
            }
        ],
        "scenes": [
            {
                "code": "scene_smoke_default",
                "name": "Scene Smoke Default",
                "layout": "grid",
                "state": "published",
                "is_test": True,
                "tiles": [
                    {
                        "capability_key": "scene.smoke.default",
                        "sequence": 10,
                    }
                ],
            }
        ],
    }
    bad_payload = {
        "mode": "merge",
        "capabilities": [
            {
                "key": "scene.validation.bad",
                "name": "Scene Validation Bad",
                "intent": "ui.contract",
                "default_payload": {"action_xmlid": "invalid.action_xmlid"},
                "is_test": True,
            }
        ],
        "scenes": [
            {
                "code": "scene_validation_bad",
                "name": "Scene Validation Bad",
                "layout": "grid",
                "state": "published",
                "is_test": True,
                "tiles": [
                    {
                        "capability_key": "scene.validation.bad",
                        "sequence": 10,
                    }
                ],
            }
        ],
    }
    try:
        # scenes.my should be OK and non-empty
        status, scenes_resp = http_get_json(scenes_url, headers=auth_header)
        require_ok(status, scenes_resp, "scenes.my")
        scenes_data = scenes_resp.get("data") or {}
        _require_deprecation(scenes_data, label="scenes.my")
        scenes = scenes_data.get("scenes") or []
        if not scenes:
            status, seed_resp = http_post_json(import_url, seed_payload, headers=auth_header)
            require_ok(status, seed_resp, "scenes.import seed")
            created_test = True
            status, scenes_resp = http_get_json(scenes_url_tests, headers=auth_header)
            require_ok(status, scenes_resp, "scenes.my (after seed)")
            scenes_data = scenes_resp.get("data") or {}
            _require_deprecation(scenes_data, label="scenes.my (after seed)")
            scenes = scenes_data.get("scenes") or []
            if not scenes:
                raise RuntimeError("scenes.my returned empty list after seed")
        default_scene = scenes_data.get("default_scene") or scenes[0].get("code")
        if not default_scene:
            raise RuntimeError("default_scene missing")

        # preference set/get should round-trip
        status, pref_set = http_post_json(
            pref_set_url, {"default_scene": default_scene}, headers=auth_header
        )
        require_ok(status, pref_set, "preferences.set")
        status, pref_get = http_get_json(pref_get_url, headers=auth_header)
        require_ok(status, pref_get, "preferences.get")
        pref_default = (pref_get.get("data") or {}).get("default_scene")
        if pref_default != default_scene:
            raise RuntimeError("preferences default_scene mismatch")

        # scenes.my should reflect default_scene
        status, scenes_resp2 = http_get_json(scenes_url, headers=auth_header)
        require_ok(status, scenes_resp2, "scenes.my (after pref)")
        _require_deprecation(scenes_resp2.get("data") or {}, label="scenes.my (after pref)")
        if (scenes_resp2.get("data") or {}).get("default_scene") != default_scene:
            raise RuntimeError("scenes.my default_scene did not update")

        # export should be forbidden without auth
        status, export_noauth = http_get_json(export_url)
        if status not in (401, 403):
            raise RuntimeError(f"export without auth should be 401/403, got {status}")

        # export with auth should succeed
        status, export_resp = http_get_json(export_url, headers=auth_header)
        require_ok(status, export_resp, "scenes.export")
        export_data = export_resp.get("data") or {}
        export_scenes = export_data.get("scenes") or []
        if not export_scenes:
            raise RuntimeError("scenes.export returned empty scenes")
        for scene in export_scenes:
            if "state" not in scene or "tiles" not in scene:
                raise RuntimeError("scenes.export scene missing state/tiles")

        # dry-run import should return diff
        status, dry_run_resp = http_post_json(
            import_url,
            {"mode": "merge", "dry_run": True, "capabilities": export_data.get("capabilities"), "scenes": export_scenes},
            headers=auth_header,
        )
        require_ok(status, dry_run_resp, "scenes.import dry_run")
        data = dry_run_resp.get("data") or {}
        diff = data.get("diff") or {}
        diff_v2 = data.get("diff_v2") or {}
        if not isinstance(diff, dict) or "capabilities" not in diff or "scenes" not in diff:
            raise RuntimeError("dry_run diff missing expected keys")
        if diff_v2 and not ("creates" in diff_v2 and "updates" in diff_v2 and "deletes" in diff_v2):
            raise RuntimeError("dry_run diff_v2 missing expected keys")

        # validation failure on publish (bad tile)
        _cleanup_test_pack(import_url, auth_header, bad_payload)
        status, bad_resp = http_post_json(import_url, bad_payload, headers=auth_header)
        if status < 400 or bad_resp.get("ok") is True:
            raise RuntimeError("expected validation error for bad scene import")
        error = bad_resp.get("error") or {}
        if error.get("code") != "VALIDATION_ERROR":
            raise RuntimeError("expected VALIDATION_ERROR for bad scene import")
        details = error.get("details") or {}
        if not (isinstance(details, dict) and details.get("issues")):
            raise RuntimeError("validation issues missing in error details")

        print("[scene_admin_smoke] PASS")
    finally:
        if created_test:
            _cleanup_test_pack(import_url, auth_header, seed_payload)
        _cleanup_test_pack(import_url, auth_header, bad_payload)


if __name__ == "__main__":
    main()
