# -*- coding: utf-8 -*-
"""Audit legacy online attachment mirror job outputs and local custody.

Run through odoo shell. This script is intended for post-job acceptance: it
reads result JSON files written by legacy_online_attachment_mirror.py and
samples the online file indexes in the database against local mirror roots.
"""

import json
import os
from collections import Counter
from pathlib import Path

from odoo.addons.smart_core.handlers.file_download import _legacy_file_roots


JOB_ROOT = Path(os.getenv("LEGACY_ATTACHMENT_JOB_ROOT", "/mnt/artifacts/backend/legacy-online-mirror-jobs"))
OUTPUT_JSON = Path(
    os.getenv(
        "LEGACY_ATTACHMENT_JOB_AUDIT_OUTPUT",
        "/mnt/artifacts/backend/legacy_online_attachment_mirror_job_audit.json",
    )
)
OUTPUT_MD = Path(
    os.getenv(
        "LEGACY_ATTACHMENT_JOB_AUDIT_MD_OUTPUT",
        "/mnt/artifacts/backend/legacy_online_attachment_mirror_job_audit.md",
    )
)
SOURCE_CONTAINS = [
    item.strip()
    for item in (os.getenv("LEGACY_ATTACHMENT_JOB_AUDIT_SOURCE_CONTAINS") or "online_old").split(",")
    if item.strip()
]
STRICT = os.getenv("LEGACY_ATTACHMENT_JOB_AUDIT_STRICT", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
PRINT_FULL = os.getenv("LEGACY_ATTACHMENT_JOB_AUDIT_PRINT_FULL", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


def _env_int(name, default):
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return default
    return int(str(raw).strip())


INDEX_LIMIT = _env_int("LEGACY_ATTACHMENT_JOB_AUDIT_INDEX_LIMIT", 5000)
EXAMPLE_LIMIT = _env_int("LEGACY_ATTACHMENT_JOB_AUDIT_EXAMPLE_LIMIT", 30)
ALLOW_JOB_FAILURES = _env_int("LEGACY_ATTACHMENT_JOB_AUDIT_ALLOW_JOB_FAILURES", 0)
ALLOW_MISSING_FILES = _env_int("LEGACY_ATTACHMENT_JOB_AUDIT_ALLOW_MISSING_FILES", 0)


def _safe_path(path, fallback):
    candidates = [path, fallback]
    for candidate in candidates:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            probe = candidate.parent / ".legacy_attachment_job_audit_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return fallback


def _source_domain():
    domain = [("active", "=", True)]
    if SOURCE_CONTAINS:
        if len(SOURCE_CONTAINS) == 1:
            domain.append(("source_table", "ilike", SOURCE_CONTAINS[0]))
            return domain
        domain.extend(["|"] * (len(SOURCE_CONTAINS) - 1))
        domain.extend(("source_table", "ilike", item) for item in SOURCE_CONTAINS)
    return domain


def _path_candidates(relative_path):
    clean = str(relative_path or "").strip().replace("\\", "/").lstrip("/")
    if not clean or ".." in Path(clean).parts:
        return []
    candidates = [clean]
    if clean.startswith("UploadFile/UserFile/"):
        candidates.append(clean[len("UploadFile/") :])
    if clean.startswith("~/"):
        without_home = clean[2:]
        candidates.append(without_home)
        if without_home.startswith("File_New/"):
            candidates.append("OldSystem/" + without_home)
            candidates.append("UploadFile/OldSystem/" + without_home)
    if clean.startswith("File_New/"):
        candidates.append("OldSystem/" + clean)
        candidates.append("UploadFile/OldSystem/" + clean)
    return list(dict.fromkeys(candidates))


def _resolve_with_roots(relative_path, roots):
    for candidate in _path_candidates(relative_path):
        for root_resolved in roots:
            full_path = (root_resolved / candidate).resolve()
            try:
                full_path.relative_to(root_resolved)
            except ValueError:
                continue
            if full_path.is_file():
                return full_path
    return None


def _job_result_files():
    if not JOB_ROOT.exists():
        return []
    return sorted(item for item in JOB_ROOT.rglob("*.json") if item.is_file())


def _load_job_results():
    counts = Counter()
    result_counts = Counter()
    models = Counter()
    examples = []
    files = _job_result_files()
    for path in files:
        counts["result_files"] += 1
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            counts["result_parse_failed"] += 1
            if len(examples) < EXAMPLE_LIMIT:
                examples.append({"kind": "result_parse_failed", "path": str(path), "error": str(exc)})
            continue
        if not isinstance(payload, dict) or not isinstance(payload.get("counts"), dict):
            counts["result_non_mirror_skipped"] += 1
            continue
        if not (payload.get("mirror_root") or str(payload.get("model") or "").strip()):
            counts["result_non_mirror_skipped"] += 1
            continue
        counts["mirror_result_files"] += 1
        status = str(payload.get("status") or "").upper()
        if status != "PASS":
            counts["result_status_not_pass"] += 1
        model = str(payload.get("model") or "<unknown>")
        models[model] += 1
        for key, value in (payload.get("counts") or {}).items():
            if isinstance(value, int):
                result_counts[key] += value
        if len(examples) < EXAMPLE_LIMIT:
            examples.append(
                {
                    "kind": "result_file",
                    "path": str(path),
                    "status": status,
                    "model": model,
                    "counts": payload.get("counts") or {},
                }
            )
    return {
        "job_root": str(JOB_ROOT),
        "counts": dict(counts),
        "mirror_counts": dict(result_counts),
        "model_counts": dict(models.most_common()),
        "examples": examples,
    }


def _audit_online_file_index():
    FileIndex = env["sc.legacy.file.index"].sudo().with_context(active_test=False)  # noqa: F821
    records = FileIndex.search(_source_domain(), order="source_table, id", limit=INDEX_LIMIT or None)
    roots = [root.resolve() for root in _legacy_file_roots()]
    counts = Counter()
    source_counts = Counter()
    examples = []
    for item in records:
        counts["file_index_rows"] += 1
        source_counts[item.source_table or ""] += 1
        relative = str(item.preview_path or item.file_path or "").strip()
        if not relative:
            counts["missing_index_path"] += 1
            continue
        resolved = _resolve_with_roots(relative, roots)
        if not resolved:
            counts["missing_local_file"] += 1
            if len(examples) < EXAMPLE_LIMIT:
                examples.append(
                    {
                        "kind": "missing_local_file",
                        "id": item.id,
                        "source_table": item.source_table,
                        "legacy_file_key": item.legacy_file_key,
                        "bill_id": item.bill_id,
                        "file_name": item.file_name,
                        "relative_path": relative,
                    }
                )
            continue
        if resolved.stat().st_size <= 0:
            counts["zero_size_local_file"] += 1
            continue
        counts["local_file_ok"] += 1
    return {
        "limit": INDEX_LIMIT,
        "source_contains": SOURCE_CONTAINS,
        "legacy_file_roots": [str(item) for item in _legacy_file_roots()],
        "counts": dict(counts),
        "source_counts": dict(source_counts.most_common()),
        "examples": examples,
    }


def _render_markdown(payload):
    lines = [
        "# Legacy Online Attachment Mirror Job Audit",
        "",
        "- status: `%s`" % payload["status"],
        "- database: `%s`" % payload["database"],
        "- strict: `%s`" % payload["strict"],
        "- job_root: `%s`" % payload["job_results"]["job_root"],
        "- index_limit: `%s`" % payload["file_index"]["limit"],
        "",
        "## Job Results",
        "",
        "| metric | count |",
        "| --- | ---: |",
    ]
    for key, count in sorted(payload["job_results"]["counts"].items()):
        lines.append("| `%s` | %s |" % (key, count))
    lines.extend(["", "## Mirror Counts", "", "| metric | count |", "| --- | ---: |"])
    for key, count in sorted(payload["job_results"]["mirror_counts"].items()):
        lines.append("| `%s` | %s |" % (key, count))
    lines.extend(["", "## File Index Sample", "", "| metric | count |", "| --- | ---: |"])
    for key, count in sorted(payload["file_index"]["counts"].items()):
        lines.append("| `%s` | %s |" % (key, count))
    lines.extend(["", "## Source Counts", "", "| source_table | count |", "| --- | ---: |"])
    for source, count in payload["file_index"]["source_counts"].items():
        lines.append("| `%s` | %s |" % (source or "<blank>", count))
    if payload["errors"]:
        lines.extend(["", "## Errors", ""])
        for error in payload["errors"]:
            lines.append("- %s" % error)
    return "\n".join(lines).rstrip() + "\n"


def _summary_payload(payload, output, md_output):
    job_counts = payload["job_results"]["counts"]
    mirror_counts = payload["job_results"]["mirror_counts"]
    file_counts = payload["file_index"]["counts"]
    return {
        "scope": payload["scope"],
        "database": payload["database"],
        "status": payload["status"],
        "strict": payload["strict"],
        "job_root": payload["job_results"]["job_root"],
        "result_files": int(job_counts.get("result_files") or 0),
        "mirror_result_files": int(job_counts.get("mirror_result_files") or 0),
        "job_failure_count": payload["job_failure_count"],
        "files_local_ok": int(mirror_counts.get("files_local_ok") or 0),
        "files_download_failed": int(mirror_counts.get("files_download_failed") or 0),
        "files_local_missing": int(mirror_counts.get("files_local_missing") or 0),
        "online_fetch_failed": int(mirror_counts.get("online_fetch_failed") or 0),
        "file_index_rows": int(file_counts.get("file_index_rows") or 0),
        "local_file_ok": int(file_counts.get("local_file_ok") or 0),
        "missing_local_file": int(file_counts.get("missing_local_file") or 0),
        "zero_size_local_file": int(file_counts.get("zero_size_local_file") or 0),
        "errors": payload["errors"],
        "json_output": str(output),
        "markdown_output": str(md_output),
    }


def main():
    if "sc.legacy.file.index" not in env:  # noqa: F821
        raise RuntimeError("model not found: sc.legacy.file.index")
    job_results = _load_job_results()
    file_index = _audit_online_file_index()
    mirror_counts = job_results["mirror_counts"]
    job_failure_count = (
        int(job_results["counts"].get("result_parse_failed") or 0)
        + int(job_results["counts"].get("result_status_not_pass") or 0)
        + int(mirror_counts.get("files_download_failed") or 0)
        + int(mirror_counts.get("files_local_missing") or 0)
        + int(mirror_counts.get("online_fetch_failed") or 0)
    )
    missing_files = int(file_index["counts"].get("missing_local_file") or 0) + int(
        file_index["counts"].get("zero_size_local_file") or 0
    )
    errors = []
    if STRICT and not job_results["counts"].get("mirror_result_files"):
        errors.append("no mirror job result files found")
    if STRICT and job_failure_count > ALLOW_JOB_FAILURES:
        errors.append("job failures exceed allowance: %s > %s" % (job_failure_count, ALLOW_JOB_FAILURES))
    if STRICT and missing_files > ALLOW_MISSING_FILES:
        errors.append("missing local files exceed allowance: %s > %s" % (missing_files, ALLOW_MISSING_FILES))

    payload = {
        "scope": "legacy_online_attachment_mirror_job_audit",
        "database": env.cr.dbname,  # noqa: F821
        "status": "PASS" if not errors else "FAIL",
        "strict": STRICT,
        "allow_job_failures": ALLOW_JOB_FAILURES,
        "allow_missing_files": ALLOW_MISSING_FILES,
        "job_failure_count": job_failure_count,
        "missing_files": missing_files,
        "job_results": job_results,
        "file_index": file_index,
        "errors": errors,
    }
    json_output = _safe_path(OUTPUT_JSON, Path("/tmp/legacy_online_attachment_mirror_job_audit.json"))
    md_output = _safe_path(OUTPUT_MD, Path("/tmp/legacy_online_attachment_mirror_job_audit.md"))
    json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    md_output.write_text(_render_markdown(payload), encoding="utf-8")
    console_payload = payload if PRINT_FULL else _summary_payload(payload, json_output, md_output)
    print(json.dumps(console_payload, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    if errors:
        raise SystemExit(1)


main()
