#!/usr/bin/env python3

from __future__ import annotations

import contextlib
import io
import json
import os
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import online_capture_security as security
import scbs_55_old_system_list_count_probe as scbs_probe


class OnlineCaptureSecurityTest(unittest.TestCase):
    def base_env(self, system: str = "scbs") -> dict[str, str]:
        prefix = "OLD_SCBS" if system == "scbs" else "SCBSLY"
        output_prefix = "SCBS" if system == "scbs" else "SCBSLY"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = str(Path(temp_dir))
        return {
            "SCBS_CAPTURE_MODE": "online",
            "SCBS_ONLINE_CAPTURE_CONFIRM": security.ONLINE_CONFIRM_VALUE,
            "SCBS_CAPTURE_DESTINATION_ALLOWLIST": "http://127.0.0.1:18999",
            f"{prefix}_BASE_URL": "http://127.0.0.1:18999/capture",
            f"{prefix}_USERNAME": "local-fixture-user",
            f"{prefix}_PASSWORD": "local-fixture-secret",
            f"{prefix}_CAPTURE_WINDOW": "fixture-window",
            f"{output_prefix}_CAPTURE_RAW_OUTPUT_DIR": f"{root}/raw",
            f"{output_prefix}_CAPTURE_MANIFEST_OUTPUT_DIR": f"{root}/manifest",
            f"{output_prefix}_CAPTURE_AUDIT_LOG_PATH": f"{root}/audit.log",
        }

    def assert_preflight_fails_without_network(self, env: dict[str, str]) -> tuple[str, ...]:
        with mock.patch.object(socket, "create_connection", side_effect=AssertionError("network attempted")) as connect:
            with self.assertRaises(security.CapturePreflightError) as caught:
                security.require_online_capture(("scbs",), env)
        connect.assert_not_called()
        return caught.exception.reasons

    def test_default_offline_never_opens_network(self) -> None:
        with mock.patch.object(socket, "create_connection", side_effect=AssertionError("network attempted")) as connect:
            config = security.load_capture_config("scbs", {})
        self.assertEqual(config.mode, "offline")
        connect.assert_not_called()

    def test_missing_username_fails_before_network(self) -> None:
        env = self.base_env()
        del env["OLD_SCBS_USERNAME"]
        self.assertIn("missing:OLD_SCBS_USERNAME", self.assert_preflight_fails_without_network(env))

    def test_missing_password_fails_before_network(self) -> None:
        env = self.base_env()
        del env["OLD_SCBS_PASSWORD"]
        self.assertIn("missing:OLD_SCBS_PASSWORD", self.assert_preflight_fails_without_network(env))

    def test_missing_confirmation_fails_before_network(self) -> None:
        env = self.base_env()
        del env["SCBS_ONLINE_CAPTURE_CONFIRM"]
        self.assertIn("missing_or_invalid:SCBS_ONLINE_CAPTURE_CONFIRM", self.assert_preflight_fails_without_network(env))

    def test_destination_must_be_allowlisted(self) -> None:
        env = self.base_env()
        env["SCBS_CAPTURE_DESTINATION_ALLOWLIST"] = "https://example.invalid"
        self.assertIn("destination_not_allowed:OLD_SCBS_BASE_URL", self.assert_preflight_fails_without_network(env))

    def test_placeholder_credentials_are_rejected(self) -> None:
        env = self.base_env()
        env["OLD_SCBS_PASSWORD"] = "<provided-via-secret-environment>"
        self.assertIn("placeholder:OLD_SCBS_PASSWORD", self.assert_preflight_fails_without_network(env))

    def test_scbsly_has_no_scbs_credential_fallback(self) -> None:
        env = self.base_env("scbsly")
        env.pop("SCBSLY_USERNAME")
        env.pop("SCBSLY_PASSWORD")
        env["OLD_SCBS_USERNAME"] = "must-not-fallback"
        env["OLD_SCBS_PASSWORD"] = "must-not-fallback"
        with self.assertRaises(security.CapturePreflightError) as caught:
            security.require_online_capture(("scbsly",), env)
        self.assertIn("missing:SCBSLY_USERNAME", caught.exception.reasons)
        self.assertIn("missing:SCBSLY_PASSWORD", caught.exception.reasons)

    def test_valid_local_fixture_configuration_is_accepted_without_io(self) -> None:
        env = self.base_env()
        with mock.patch.object(socket, "create_connection", side_effect=AssertionError("network attempted")) as connect:
            config = security.require_online_capture(("scbs",), env)["scbs"]
        self.assertTrue(config.public_summary()["secret_present"])
        connect.assert_not_called()

    def test_shared_scbs_login_fails_before_request_by_default(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
            scbs_probe.requests.Session, "request", side_effect=AssertionError("network attempted")
        ) as request:
            with self.assertRaises(security.CapturePreflightError):
                scbs_probe.login(scbs_probe.requests.Session())
        request.assert_not_called()

    def test_failed_preflight_does_not_create_capture_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env = self.base_env()
            env["SCBS_CAPTURE_RAW_OUTPUT_DIR"] = str(Path(temp_dir) / "raw")
            env["SCBS_CAPTURE_MANIFEST_OUTPUT_DIR"] = str(Path(temp_dir) / "manifest")
            del env["OLD_SCBS_PASSWORD"]
            with self.assertRaises(security.CapturePreflightError):
                security.require_online_capture(("scbs",), env)
            self.assertFalse((Path(temp_dir) / "raw").exists())
            self.assertFalse((Path(temp_dir) / "manifest").exists())

    def test_all_direct_online_entrypoints_use_shared_guard(self) -> None:
        root = Path(__file__).resolve().parents[2]
        guarded = (
            "scripts/migration/scbs_self_funding_visible_surface_online_patch.py",
            "scripts/migration/scbs_joint_acceptance_online_replay.py",
            "scripts/migration/scbs_55_old_system_form_surface_login_probe.py",
            "scripts/migration/scbs_55_old_system_visible_surface_login_probe.py",
            "scripts/migration/legacy_online_attachment_mirror.py",
            "scripts/migration/legacy_base_system_file_missing_mirror.py",
            "scripts/verify/scbs_55_old_system_list_count_probe.py",
            "scripts/verify/scbsly_direct_project_acceptance_menu_probe.py",
            "scripts/verify/scbsly_current_user_menu_dump.py",
        )
        for relative in guarded:
            with self.subTest(relative=relative):
                text = (root / relative).read_text(encoding="utf-8")
                self.assertIn("require_online_capture", text)

    def test_cli_failure_is_stable_and_redacted(self) -> None:
        env = self.base_env()
        secret = env["OLD_SCBS_PASSWORD"]
        del env["SCBS_ONLINE_CAPTURE_CONFIRM"]
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=True), contextlib.redirect_stderr(stderr):
            code = security.main(["--system", "scbs", "--require-online"])
        self.assertEqual(code, security.EXIT_PREFLIGHT_FAILED)
        self.assertNotIn(secret, stderr.getvalue())
        self.assertEqual(json.loads(stderr.getvalue())["network_requests"], 0)

    def test_redaction_covers_headers_and_url_credentials(self) -> None:
        secret = "local-fixture-secret"
        credential_url = "https://" + "user:" + secret + "@example.invalid"
        text = f"Authorization=Bearer-{secret} Cookie={secret} password={secret} {credential_url}"
        redacted = security.redact_text(text)
        self.assertNotIn(secret, redacted)


if __name__ == "__main__":
    unittest.main()
