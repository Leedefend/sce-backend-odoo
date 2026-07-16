#!/usr/bin/env python3

from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import secret_scan


class SecretScanTest(unittest.TestCase):
    online_password_name = "OLD_" + "SCBS_" + "PASSWORD"
    direct_password_name = "SCBSLY_" + "PASSWORD"

    def test_online_assignment_is_redacted(self) -> None:
        secret = "fixture-value-that-must-not-be-printed"
        findings = secret_scan.scan_line(f"{self.online_password_name}={secret}")
        self.assertEqual([item.rule for item in findings], ["online_credential_assignment"])
        self.assertNotIn(secret, repr(findings))

    def test_placeholders_are_allowed(self) -> None:
        placeholders = ("<redacted>", "<provided-via-secret-environment>", "${" + self.online_password_name + "}", "...")
        for value in placeholders:
            self.assertEqual(secret_scan.scan_line(f"{self.online_password_name}={value}"), [])

    def test_literal_default_is_rejected(self) -> None:
        findings = secret_scan.scan_line(f'os.getenv("{self.online_password_name}", "not-a-placeholder")')
        self.assertEqual(findings[0].rule, "online_credential_literal_default")

    def test_cross_system_fallback_is_rejected(self) -> None:
        findings = secret_scan.scan_line(
            f"{self.direct_password_name} = os.getenv('{self.direct_password_name}') or os.getenv('{self.online_password_name}')"
        )
        self.assertIn("scbsly_cross_system_credential_fallback", [item.rule for item in findings])

    def test_main_output_never_echoes_matching_value(self) -> None:
        secret = "fixture-value-that-must-not-be-printed"
        stderr = io.StringIO()
        fixture_path = secret_scan.ROOT / "fictional-security-fixture.md"
        with (
            mock.patch.object(secret_scan, "worktree_files", return_value=[fixture_path]),
            mock.patch.object(secret_scan, "read_text", return_value=f"{self.online_password_name}={secret}"),
            contextlib.redirect_stderr(stderr),
        ):
            self.assertEqual(secret_scan.main(), 1)
        self.assertNotIn(secret, stderr.getvalue())
        self.assertIn("fingerprint=", stderr.getvalue())

    def test_cloud_and_bearer_shapes_are_rejected(self) -> None:
        cloud_value = "AKIA" + "A" * 16
        bearer_value = "Bearer " + "a" * 32
        self.assertIn("aws_access_key", [item.rule for item in secret_scan.scan_line(cloud_value)])
        self.assertIn("bearer_token", [item.rule for item in secret_scan.scan_line(bearer_value)])


if __name__ == "__main__":
    unittest.main()
