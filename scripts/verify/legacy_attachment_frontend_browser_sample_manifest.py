# -*- coding: utf-8 -*-
"""Build local-production-backed legacy attachment samples for browser checks.

Run through odoo shell. The output is a JSON array accepted by
legacy_attachment_frontend_browser_acceptance.js. Every sample is proven to
resolve to a non-empty file under the production legacy attachment mounts before
the browser check runs.
"""

import hashlib
import json
import mimetypes
import os
from collections import Counter
from pathlib import Path

from odoo.addons.smart_core.handlers.file_download import LEGACY_FILE_URL_PREFIX, _resolve_legacy_file_path


OUTPUT = Path(
    os.getenv(
        "LEGACY_ATTACHMENT_BROWSER_SAMPLE_MANIFEST_OUTPUT",
        "/mnt/artifacts/backend/legacy_attachment_frontend_browser_samples.json",
    )
)
PER_MIMETYPE = os.getenv("LEGACY_ATTACHMENT_BROWSER_SAMPLE_PER_MIMETYPE", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
EXCLUDE_MODELS = {
    item.strip()
    for item in os.getenv("LEGACY_ATTACHMENT_BROWSER_SAMPLE_EXCLUDE_MODELS", "").replace("\n", ",").split(",")
    if item.strip()
}


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _mode_for_mimetype(mimetype: str) -> str:
    normalized = (mimetype or "").strip().lower()
    if normalized.startswith("image/") or normalized == "application/pdf" or normalized.startswith("text/"):
        return "preview"
    return "download"


def _safe_output(path: Path) -> Path:
    candidates = [path, Path("/tmp/legacy_attachment_frontend_browser_samples.json")]
    for candidate in candidates:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            probe = candidate.parent / ".legacy_attachment_browser_manifest_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return Path("/tmp/legacy_attachment_frontend_browser_samples.json")


def _legacy_relative_path(url: str) -> str:
    clean = str(url or "").strip()
    if clean.startswith(LEGACY_FILE_URL_PREFIX):
        return clean[len(LEGACY_FILE_URL_PREFIX) :].strip()
    return ""


def main():
    Attachment = env["ir.attachment"].sudo()  # noqa: F821
    rows = Attachment.search(
        [("type", "=", "url"), ("url", "=like", LEGACY_FILE_URL_PREFIX + "%")],
        order="res_model, mimetype, id",
    )
    rows_by_model = Counter()
    local_ok_by_model = Counter()
    selected_keys = set()
    samples = []
    skipped_missing_local = []

    for attachment in rows:
        model = attachment.res_model or "<blank>"
        rows_by_model[model] += 1
        if model in EXCLUDE_MODELS:
            continue
        relative_path = _legacy_relative_path(attachment.url)
        local_path = _resolve_legacy_file_path(relative_path) if relative_path else None
        if not local_path:
            if len(skipped_missing_local) < 50:
                skipped_missing_local.append(
                    {
                        "id": attachment.id,
                        "name": attachment.name,
                        "res_model": model,
                        "res_id": attachment.res_id,
                        "url": attachment.url,
                    }
                )
            continue
        local_path = Path(local_path)
        try:
            local_size = local_path.stat().st_size
        except OSError:
            local_size = 0
        if local_size <= 0:
            continue
        local_ok_by_model[model] += 1
        mimetype = attachment.mimetype or mimetypes.guess_type(attachment.name or str(local_path))[0] or "application/octet-stream"
        key = (model, mimetype) if PER_MIMETYPE else (model, "*")
        if key in selected_keys:
            continue
        selected_keys.add(key)
        label_mimetype = mimetype.replace("/", "_").replace(".", "_")
        samples.append(
            {
                "label": "%s-%s-%s" % (model.replace(".", "_"), label_mimetype, attachment.id),
                "mode": _mode_for_mimetype(mimetype),
                "id": attachment.id,
                "name": attachment.name or local_path.name,
                "mimetype": mimetype,
                "res_model": model,
                "res_id": attachment.res_id,
                "url": attachment.url,
                "expected_source": "production_local_legacy_file_root",
                "expected_local_path": str(local_path),
                "expected_local_size": local_size,
                "expected_local_sha256": _sha256(local_path),
            }
        )

    required_models = {model for model in rows_by_model if model not in EXCLUDE_MODELS}
    covered_models = {sample["res_model"] for sample in samples}
    missing_models = sorted(required_models - covered_models)
    payload = {
        "scope": "legacy_attachment_frontend_browser_sample_manifest",
        "database": env.cr.dbname,  # noqa: F821
        "per_mimetype": PER_MIMETYPE,
        "rows_by_model": dict(rows_by_model),
        "local_ok_by_model": dict(local_ok_by_model),
        "required_model_count": len(required_models),
        "covered_model_count": len(covered_models),
        "missing_models": missing_models,
        "sample_count": len(samples),
        "samples": samples,
        "skipped_missing_local_examples": skipped_missing_local,
        "status": "PASS" if not missing_models and samples else "FAIL",
    }
    output = _safe_output(OUTPUT)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({**payload, "output": str(output), "samples": samples[:20]}, ensure_ascii=False, indent=2, sort_keys=True))
    if payload["status"] != "PASS":
        raise SystemExit(1)


main()
