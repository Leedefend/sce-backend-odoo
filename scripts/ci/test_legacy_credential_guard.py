#!/usr/bin/env python3

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import legacy_credential_guard


class LegacyCredentialGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.value = "fictional-credential-for-guard-only"
        self.fingerprint = hashlib.sha256(self.value.encode()).hexdigest()[:12]
        self.known = {self.fingerprint: "TEST-LC-001"}

    def test_fictional_known_fingerprint_is_detected_without_echo(self) -> None:
        findings = legacy_credential_guard.scan_text(f"PASSWORD={self.value}", "fixture", self.known)
        self.assertEqual(findings[0].fingerprint_id, "TEST-LC-001")
        self.assertNotIn(self.value, repr(findings))

    def test_revoked_placeholders_are_allowed(self) -> None:
        for placeholder in ("<REVOKED_LEGACY_USERNAME>", "<REVOKED_LEGACY_SECRET>"):
            self.assertEqual(legacy_credential_guard.scan_text(f"PASSWORD={placeholder}", "fixture", self.known), [])

    def test_missing_catalog_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            legacy_credential_guard.load_catalog(Path("/definitely/missing/catalog.json"))

    def test_pr_jsonl_scans_offline_body(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "prs.jsonl"
            source.write_text(json.dumps({"number": 7, "body": f"password={self.value}"}) + "\n")
            findings, count = legacy_credential_guard.pr_body_matches(source, self.known)
        self.assertEqual(count, 1)
        self.assertEqual(findings[0].location, "PR#7")

    def test_safe_result_contains_no_candidate_value(self) -> None:
        findings = legacy_credential_guard.scan_text(f"TOKEN={self.value}", "fixture", self.known)
        result = legacy_credential_guard.safe_result(
            findings,
            {"TEST-LC-001"},
            1,
            0,
            {"revocation": {"credentials_revoked": False, "sessions_revoked": False}},
        )
        rendered = json.dumps(result)
        self.assertNotIn(self.value, rendered)
        self.assertFalse(result["secret_values_recorded"])


if __name__ == "__main__":
    unittest.main()
