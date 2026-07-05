# -*- coding: utf-8 -*-
"""Audit local custody completeness for legacy attachment file indexes.

Run through odoo shell. The audit is read-only by default: missing files are
reported as metrics unless LEGACY_ATTACHMENT_COMPLETENESS_STRICT=1 is set.
"""

import json
import os
from collections import Counter
from pathlib import Path

from odoo.addons.smart_core.handlers.file_download import (
    LEGACY_FILE_URL_PREFIX,
    _legacy_file_roots,
)


OUTPUT_JSON = Path(
    os.getenv(
        "LEGACY_ATTACHMENT_COMPLETENESS_OUTPUT",
        "/mnt/artifacts/backend/legacy_attachment_mirror_completeness_audit.json",
    )
)
OUTPUT_MD = Path(
    os.getenv(
        "LEGACY_ATTACHMENT_COMPLETENESS_MD_OUTPUT",
        "/mnt/artifacts/backend/legacy_attachment_mirror_completeness_audit.md",
    )
)
SOURCE_CONTAINS = [
    item.strip()
    for item in (os.getenv("LEGACY_ATTACHMENT_COMPLETENESS_SOURCE_CONTAINS") or "").split(",")
    if item.strip()
]
STRICT = os.getenv("LEGACY_ATTACHMENT_COMPLETENESS_STRICT", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
PRINT_FULL = os.getenv("LEGACY_ATTACHMENT_COMPLETENESS_PRINT_FULL", "0").strip().lower() in {
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


LIMIT = _env_int("LEGACY_ATTACHMENT_COMPLETENESS_LIMIT", 5000)
EXAMPLE_LIMIT = _env_int("LEGACY_ATTACHMENT_COMPLETENESS_EXAMPLE_LIMIT", 30)
ALLOW_MISSING_FILES = _env_int("LEGACY_ATTACHMENT_COMPLETENESS_ALLOW_MISSING_FILES", 0)


def _domain():
    domain = [("active", "=", True)]
    if SOURCE_CONTAINS:
        if len(SOURCE_CONTAINS) == 1:
            domain.append(("source_table", "ilike", SOURCE_CONTAINS[0]))
            return domain
        domain.extend(["|"] * (len(SOURCE_CONTAINS) - 1))
        domain.extend(("source_table", "ilike", item) for item in SOURCE_CONTAINS)
    return domain


def _safe_output_path():
    candidates = [
        OUTPUT_JSON,
        Path("/tmp/legacy_attachment_mirror_completeness_audit.json"),
    ]
    for candidate in candidates:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            probe = candidate.parent / ".legacy_attachment_completeness_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return candidates[-1]


def _safe_md_output_path():
    candidates = [
        OUTPUT_MD,
        Path("/tmp/legacy_attachment_mirror_completeness_audit.md"),
    ]
    for candidate in candidates:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            probe = candidate.parent / ".legacy_attachment_completeness_md_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return candidates[-1]


def _file_stat(path):
    if not path:
        return {}
    try:
        return {"size": path.stat().st_size, "path": str(path)}
    except OSError:
        return {"path": str(path)}


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


def _best_relative_path(item, roots):
    candidates = [
        str(getattr(item, "preview_path", "") or "").strip(),
        str(getattr(item, "file_path", "") or "").strip(),
    ]
    candidates = [value for value in candidates if value]
    for candidate in candidates:
        if _resolve_with_roots(candidate, roots):
            return candidate
    return candidates[0] if candidates else ""


def _add_example(examples, kind, item, extra=None):
    if len(examples) >= EXAMPLE_LIMIT:
        return
    payload = {
        "kind": kind,
        "id": item.id,
        "legacy_file_key": item.legacy_file_key,
        "legacy_file_id": item.legacy_file_id,
        "bill_id": item.bill_id,
        "source_table": item.source_table,
        "file_name": item.file_name,
        "file_path": item.file_path,
        "preview_path": item.preview_path,
    }
    if extra:
        payload.update(extra)
    examples.append(payload)


def _audit_file_index():
    FileIndex = env["sc.legacy.file.index"].sudo().with_context(active_test=False)  # noqa: F821
    records = FileIndex.search(_domain(), order="source_table, id", limit=LIMIT or None)
    roots = [root.resolve() for root in _legacy_file_roots()]
    counts = Counter()
    source_counts = Counter()
    extension_counts = Counter()
    examples = []

    for item in records:
        counts["file_index_rows"] += 1
        source = item.source_table or ""
        source_counts[source] += 1
        if item.extension:
            extension_counts[item.extension] += 1
        if not item.file_path and not item.preview_path:
            counts["missing_index_path"] += 1
            _add_example(examples, "missing_index_path", item)
            continue

        relative_path = _best_relative_path(item, roots)
        if not relative_path:
            counts["unresolvable_relative_path"] += 1
            _add_example(examples, "unresolvable_relative_path", item)
            continue

        resolved = _resolve_with_roots(relative_path, roots)
        if not resolved:
            counts["missing_local_file"] += 1
            _add_example(examples, "missing_local_file", item, {"relative_path": relative_path})
            continue

        stat = _file_stat(resolved)
        if stat.get("size", 0) <= 0:
            counts["zero_size_local_file"] += 1
            _add_example(examples, "zero_size_local_file", item, {"relative_path": relative_path, **stat})
            continue
        counts["local_file_ok"] += 1

    return {
        "counts": dict(counts),
        "source_counts": dict(source_counts.most_common()),
        "extension_counts": dict(extension_counts.most_common(30)),
        "examples": examples,
    }


def _audit_legacy_url_attachments():
    Attachment = env["ir.attachment"].sudo()  # noqa: F821
    domain = [("type", "=", "url"), ("url", "like", LEGACY_FILE_URL_PREFIX + "%")]
    rows = Attachment.search(domain, order="id", limit=LIMIT or None)
    roots = [root.resolve() for root in _legacy_file_roots()]
    counts = Counter()
    examples = []
    for attachment in rows:
        counts["legacy_url_attachments"] += 1
        relative_path = (attachment.url or "")[len(LEGACY_FILE_URL_PREFIX) :].strip()
        resolved = _resolve_with_roots(relative_path, roots)
        if not resolved:
            counts["legacy_url_missing_local_file"] += 1
            if len(examples) < EXAMPLE_LIMIT:
                examples.append(
                    {
                        "kind": "legacy_url_missing_local_file",
                        "id": attachment.id,
                        "name": attachment.name,
                        "res_model": attachment.res_model,
                        "res_id": attachment.res_id,
                        "relative_path": relative_path,
                    }
                )
            continue
        stat = _file_stat(resolved)
        if stat.get("size", 0) <= 0:
            counts["legacy_url_zero_size_local_file"] += 1
            continue
        counts["legacy_url_local_file_ok"] += 1
    return {"counts": dict(counts), "examples": examples}


def _render_markdown(payload):
    file_counts = payload["file_index"]["counts"]
    url_counts = payload["legacy_url_attachments"]["counts"]
    lines = [
        "# Legacy Attachment Mirror Completeness Audit",
        "",
        "- status: `%s`" % payload["status"],
        "- database: `%s`" % payload["database"],
        "- strict: `%s`" % payload["strict"],
        "- limit: `%s`" % payload["limit"],
        "- source_contains: `%s`" % (",".join(payload["source_contains"]) or "<all>"),
        "",
        "## File Index",
        "",
        "| metric | count |",
        "| --- | ---: |",
    ]
    for key in sorted(file_counts):
        lines.append("| `%s` | %s |" % (key, file_counts[key]))
    lines.extend(["", "## Legacy URL Attachments", "", "| metric | count |", "| --- | ---: |"])
    for key in sorted(url_counts):
        lines.append("| `%s` | %s |" % (key, url_counts[key]))
    lines.extend(["", "## Source Counts", "", "| source_table | count |", "| --- | ---: |"])
    for source, count in payload["file_index"]["source_counts"].items():
        lines.append("| `%s` | %s |" % (source or "<blank>", count))
    if payload["errors"]:
        lines.extend(["", "## Errors", ""])
        for error in payload["errors"]:
            lines.append("- %s" % error)
    return "\n".join(lines).rstrip() + "\n"


def _summary_payload(payload, output, md_output):
    file_counts = payload["file_index"]["counts"]
    url_counts = payload["legacy_url_attachments"]["counts"]
    return {
        "scope": payload["scope"],
        "database": payload["database"],
        "status": payload["status"],
        "strict": payload["strict"],
        "limit": payload["limit"],
        "source_contains": payload["source_contains"],
        "missing_files": payload["missing_files"],
        "missing_legacy_url_files": payload["missing_legacy_url_files"],
        "file_index_rows": int(file_counts.get("file_index_rows") or 0),
        "local_file_ok": int(file_counts.get("local_file_ok") or 0),
        "missing_local_file": int(file_counts.get("missing_local_file") or 0),
        "zero_size_local_file": int(file_counts.get("zero_size_local_file") or 0),
        "legacy_url_attachments": int(url_counts.get("legacy_url_attachments") or 0),
        "legacy_url_local_file_ok": int(url_counts.get("legacy_url_local_file_ok") or 0),
        "legacy_url_missing_local_file": int(url_counts.get("legacy_url_missing_local_file") or 0),
        "errors": payload["errors"],
        "json_output": str(output),
        "markdown_output": str(md_output),
    }


def main():
    if "sc.legacy.file.index" not in env:  # noqa: F821
        raise RuntimeError("model not found: sc.legacy.file.index")

    file_index_audit = _audit_file_index()
    legacy_url_audit = _audit_legacy_url_attachments()
    file_counts = file_index_audit["counts"]
    url_counts = legacy_url_audit["counts"]
    missing_files = int(file_counts.get("missing_local_file") or 0) + int(file_counts.get("zero_size_local_file") or 0)
    missing_legacy_urls = int(url_counts.get("legacy_url_missing_local_file") or 0) + int(
        url_counts.get("legacy_url_zero_size_local_file") or 0
    )
    errors = []
    if STRICT and missing_files + missing_legacy_urls > ALLOW_MISSING_FILES:
        errors.append(
            "missing local files exceed allowance: %s > %s"
            % (missing_files + missing_legacy_urls, ALLOW_MISSING_FILES)
        )

    payload = {
        "scope": "legacy_attachment_mirror_completeness_audit",
        "database": env.cr.dbname,  # noqa: F821
        "status": "PASS" if not errors else "FAIL",
        "strict": STRICT,
        "allow_missing_files": ALLOW_MISSING_FILES,
        "limit": LIMIT,
        "source_contains": SOURCE_CONTAINS,
        "legacy_file_roots": [str(item) for item in _legacy_file_roots()],
        "file_index": file_index_audit,
        "legacy_url_attachments": legacy_url_audit,
        "missing_files": missing_files,
        "missing_legacy_url_files": missing_legacy_urls,
        "errors": errors,
    }
    output = _safe_output_path()
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    md_output = _safe_md_output_path()
    md_output.write_text(_render_markdown(payload), encoding="utf-8")
    console_payload = payload if PRINT_FULL else _summary_payload(payload, output, md_output)
    print(json.dumps(console_payload, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    if errors:
        raise SystemExit(1)


main()
