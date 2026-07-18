from __future__ import annotations

import hashlib
import hmac
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


PAYLOAD_SCHEMA_VERSION = "sce.customer_payload_manifest.v1"
CUSTOMER_MODULE_SCHEMA_VERSION = "sce.customer_module_manifest.v1"
TENANT_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{2,62}$")
PAYLOAD_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
MODULE_NAME_RE = re.compile(r"^sce_customer_[a-z0-9_]+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class TenantDeliveryManifestError(ValueError):
    pass


def canonical_manifest_bytes(payload: dict[str, Any]) -> bytes:
    canonical = json.loads(json.dumps(payload))
    signature = canonical.get("signature")
    if isinstance(signature, dict):
        signature["value"] = ""
    return json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def manifest_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_manifest_bytes(payload)).hexdigest()


def sign_manifest_hmac(payload: dict[str, Any], key: bytes) -> str:
    if not key:
        raise TenantDeliveryManifestError("signature key must not be empty")
    return hmac.new(key, canonical_manifest_bytes(payload), hashlib.sha256).hexdigest()


def verify_manifest_hmac(payload: dict[str, Any], key: bytes) -> None:
    signature = payload.get("signature")
    if not isinstance(signature, dict):
        raise TenantDeliveryManifestError("signature must be an object")
    if signature.get("algorithm") != "hmac-sha256":
        raise TenantDeliveryManifestError("unsupported signature algorithm")
    supplied = str(signature.get("value") or "")
    if not SHA256_RE.fullmatch(supplied):
        raise TenantDeliveryManifestError("signature value must be lowercase sha256 hex")
    expected = sign_manifest_hmac(payload, key)
    if not hmac.compare_digest(supplied, expected):
        raise TenantDeliveryManifestError("payload signature mismatch")


def _version_tuple(value: str) -> tuple[int, ...]:
    text = str(value or "").strip()
    if not text or any(not item.isdigit() for item in text.split(".")):
        raise TenantDeliveryManifestError("product versions must be dot-separated integers")
    return tuple(int(item) for item in text.split("."))


def _verify_product_range(version_range: Any, product_version: str | None) -> None:
    if not isinstance(version_range, dict):
        raise TenantDeliveryManifestError("product_version_range must be an object")
    minimum = _version_tuple(version_range.get("min_inclusive"))
    maximum = _version_tuple(version_range.get("max_exclusive"))
    if minimum >= maximum:
        raise TenantDeliveryManifestError("product version range is empty")
    if product_version is None:
        return
    current = _version_tuple(product_version)
    if not minimum <= current < maximum:
        raise TenantDeliveryManifestError("payload is incompatible with the product version")


def validate_customer_module_manifest(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != CUSTOMER_MODULE_SCHEMA_VERSION:
        raise TenantDeliveryManifestError("customer module schema_version mismatch")
    tenant_key = str(payload.get("tenant_key") or "")
    module_name = str(payload.get("module_name") or "")
    if not TENANT_KEY_RE.fullmatch(tenant_key):
        raise TenantDeliveryManifestError("invalid tenant_key")
    if not MODULE_NAME_RE.fullmatch(module_name):
        raise TenantDeliveryManifestError("invalid customer module_name")
    if module_name != f"sce_customer_{tenant_key}":
        raise TenantDeliveryManifestError("module_name must match tenant_key")
    if payload.get("customer_key") != tenant_key:
        raise TenantDeliveryManifestError("customer_key must match tenant_key")
    if payload.get("module_key") != module_name:
        raise TenantDeliveryManifestError("module_key must match module_name")
    if payload.get("product_bundle") != "smart_construction_bundle":
        raise TenantDeliveryManifestError("customer module must target smart_construction_bundle")
    if payload.get("install_mode") != "customer_database_only":
        raise TenantDeliveryManifestError("customer module install mode must be customer_database_only")
    if payload.get("payload_manifest_version") != PAYLOAD_SCHEMA_VERSION:
        raise TenantDeliveryManifestError("customer payload manifest version mismatch")
    if payload.get("uninstall_policy") != "fail_closed":
        raise TenantDeliveryManifestError("customer module uninstall must fail closed")
    _verify_product_range(payload.get("product_version_range"), None)
    if payload.get("minimum_product_version") != payload["product_version_range"].get("min_inclusive"):
        raise TenantDeliveryManifestError("minimum_product_version must match product_version_range")
    _version_tuple(payload.get("maximum_tested_product_version"))


def _safe_relative_path(value: Any) -> str:
    text = str(value or "")
    path = PurePosixPath(text)
    if not text or path.is_absolute() or ".." in path.parts or text != path.as_posix():
        raise TenantDeliveryManifestError(f"unsafe payload path: {text!r}")
    return text


def validate_payload_manifest(
    payload: dict[str, Any],
    *,
    expected_tenant_key: str | None = None,
    product_version: str | None = None,
) -> None:
    if payload.get("schema_version") != PAYLOAD_SCHEMA_VERSION:
        raise TenantDeliveryManifestError("payload schema_version mismatch")
    tenant_key = str(payload.get("tenant_key") or "")
    payload_id = str(payload.get("payload_id") or "")
    if not TENANT_KEY_RE.fullmatch(tenant_key):
        raise TenantDeliveryManifestError("invalid tenant_key")
    if expected_tenant_key and tenant_key != expected_tenant_key:
        raise TenantDeliveryManifestError("payload tenant does not match customer module")
    if not PAYLOAD_ID_RE.fullmatch(payload_id):
        raise TenantDeliveryManifestError("invalid payload_id")
    _verify_product_range(payload.get("product_version_range"), product_version)

    files = payload.get("files")
    if not isinstance(files, list):
        raise TenantDeliveryManifestError("files must be a list")
    file_paths: set[str] = set()
    for item in files:
        if not isinstance(item, dict):
            raise TenantDeliveryManifestError("file entry must be an object")
        path = _safe_relative_path(item.get("path"))
        if path in file_paths:
            raise TenantDeliveryManifestError(f"duplicate payload path: {path}")
        file_paths.add(path)
        if not SHA256_RE.fullmatch(str(item.get("sha256") or "")):
            raise TenantDeliveryManifestError(f"invalid sha256 for {path}")
        for key in ("rows", "bytes"):
            value = item.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise TenantDeliveryManifestError(f"{key} must be a non-negative integer for {path}")

    import_order = payload.get("import_order")
    if not isinstance(import_order, list) or len(import_order) != len(set(import_order)):
        raise TenantDeliveryManifestError("import_order must be a unique list")
    if set(import_order) != file_paths:
        raise TenantDeliveryManifestError("import_order must cover every payload file exactly once")

    encryption = payload.get("encryption")
    if not isinstance(encryption, dict) or not encryption.get("algorithm") or not encryption.get("key_id"):
        raise TenantDeliveryManifestError("encryption metadata is required")
    signature = payload.get("signature")
    if not isinstance(signature, dict) or signature.get("algorithm") != "hmac-sha256" or not signature.get("key_id"):
        raise TenantDeliveryManifestError("supported signature metadata is required")
    if not isinstance(payload.get("acceptance_fingerprints"), dict):
        raise TenantDeliveryManifestError("acceptance_fingerprints must be an object")


def verify_payload_files(payload: dict[str, Any], payload_root: Path) -> None:
    root = payload_root.resolve(strict=True)
    for item in payload.get("files") or []:
        relative = _safe_relative_path(item.get("path"))
        path = (root / relative).resolve(strict=True)
        if root not in path.parents:
            raise TenantDeliveryManifestError(f"payload path escapes root: {relative}")
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                size += len(chunk)
                digest.update(chunk)
        if size != item.get("bytes"):
            raise TenantDeliveryManifestError(f"payload byte count mismatch: {relative}")
        if digest.hexdigest() != item.get("sha256"):
            raise TenantDeliveryManifestError(f"payload checksum mismatch: {relative}")
