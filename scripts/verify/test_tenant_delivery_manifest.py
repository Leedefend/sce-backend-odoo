#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "addons/smart_core/utils/tenant_delivery_manifest.py"
SPEC = importlib.util.spec_from_file_location("tenant_delivery_manifest", MODULE_PATH)
manifest = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(manifest)


class TenantDeliveryManifestTest(unittest.TestCase):
    def _payload(self, content: bytes = b"payload\n"):
        payload = {
            "schema_version": "sce.customer_payload_manifest.v1",
            "payload_id": "sample-data-1",
            "tenant_key": "sample",
            "payload_version": "1.0.0",
            "product_version_range": {"min_inclusive": "17.0.0", "max_exclusive": "18.0.0"},
            "created_at": "2026-07-18T00:00:00Z",
            "source_cutoff_at": "2026-07-17T00:00:00Z",
            "files": [
                {
                    "path": "data/records.jsonl",
                    "media_type": "application/x-ndjson",
                    "rows": 1,
                    "bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            ],
            "import_order": ["data/records.jsonl"],
            "attachments": {"mode": "none"},
            "encryption": {"algorithm": "age", "key_id": "sample-test-key", "recipients": []},
            "signature": {"algorithm": "hmac-sha256", "key_id": "sample-signing-key", "value": ""},
            "acceptance_fingerprints": {"records": 1},
        }
        payload["signature"]["value"] = manifest.sign_manifest_hmac(payload, b"test-secret")
        return payload

    def test_valid_signed_payload_and_file(self):
        content = b"payload\n"
        payload = self._payload(content)
        manifest.validate_payload_manifest(
            payload,
            expected_tenant_key="sample",
            product_version="17.0.1",
        )
        manifest.verify_manifest_hmac(payload, b"test-secret")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data/records.jsonl"
            path.parent.mkdir()
            path.write_bytes(content)
            manifest.verify_payload_files(payload, Path(tmp))

    def test_rejects_cross_tenant_payload(self):
        with self.assertRaisesRegex(manifest.TenantDeliveryManifestError, "tenant"):
            manifest.validate_payload_manifest(self._payload(), expected_tenant_key="another")

    def test_rejects_path_escape(self):
        payload = self._payload()
        payload["files"][0]["path"] = "../records.jsonl"
        payload["import_order"] = ["../records.jsonl"]
        with self.assertRaisesRegex(manifest.TenantDeliveryManifestError, "unsafe"):
            manifest.validate_payload_manifest(payload)

    def test_rejects_signature_mismatch(self):
        payload = self._payload()
        payload["payload_version"] = "2.0.0"
        with self.assertRaisesRegex(manifest.TenantDeliveryManifestError, "signature mismatch"):
            manifest.verify_manifest_hmac(payload, b"test-secret")

    def test_sample_customer_module_manifest(self):
        payload = json.loads(
            (ROOT / "customer_addons/sce_customer_sample/customer_module_manifest.json").read_text()
        )
        manifest.validate_customer_module_manifest(payload)


if __name__ == "__main__":
    unittest.main()
