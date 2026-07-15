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
    def test_online_assignment_is_redacted(self) -> None:
        secret = "fixture-value-that-must-not-be-printed"
        findings = secret_scan.scan_line(f"OLD_SCBS_PASSWORD={secret}")
        self.assertEqual([item.rule for item in findings], ["online_credential_assignment"])
        self.assertNotIn(secret, repr(findings))

    def test_placeholders_are_allowed(self) -> None:
        for value in ("<redacted>", "<provided-via-secret-environment>", "${OLD_SCBS_PASSWORD}", "..."):
            self.assertEqual(secret_scan.scan_line(f"OLD_SCBS_PASSWORD={value}"), [])

    def test_literal_default_is_rejected(self) -> None:
        findings = secret_scan.scan_line('os.getenv("OLD_SCBS_PASSWORD", "not-a-placeholder")')
        self.assertEqual(findings[0].rule, "online_credential_literal_default")

    def test_cross_system_fallback_is_rejected(self) -> None:
        findings = secret_scan.scan_line("SCBSLY_PASSWORD = os.getenv('SCBSLY_PASSWORD') or os.getenv('OLD_SCBS_PASSWORD')")
        self.assertIn("scbsly_cross_system_credential_fallback", [item.rule for item in findings])

    def test_main_output_never_echoes_matching_value(self) -> None:
        secret = "fixture-value-that-must-not-be-printed"
        stderr = io.StringIO()
        with mock.patch.object(secret_scan, "worktree_files", return_value=[]), contextlib.redirect_stderr(stderr):
            self.assertEqual(secret_scan.main(), 0)
        self.assertNotIn(secret, stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
