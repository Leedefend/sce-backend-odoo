# -*- coding: utf-8 -*-
"""Generate read-only custody evidence for legacy online attachments.

Run through odoo shell. The output is intentionally compatible with
legacy_online_attachment_mirror_job_audit.py result discovery: it proves that
online legacy file-index rows resolve to non-empty local files without rerunning
the historical downloader.
"""

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from odoo.addons.smart_core.handlers.file_download import _legacy_file_roots


JOB_ROOT = Path(
    os.getenv(
        "LEGACY_ATTACHMENT_CUSTODY_EVIDENCE_JOB_ROOT",
        "/mnt/artifacts/backend/legacy-online-mirror-jobs",
    )
)
SOURCE_CONTAINS = [
    item.strip()
    for item in (os.getenv("LEGACY_ATTACHMENT_CUSTODY_EVIDENCE_SOURCE_CONTAINS") or "online_old").split(",")
    if item.strip()
]
EXAMPLE_LIMIT = int(os.getenv("LEGACY_ATTACHMENT_CUSTODY_EVIDENCE_EXAMPLE_LIMIT", "30") or "30")


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


def _safe_job_root():
    candidates = [JOB_ROOT, Path("/tmp/legacy-online-mirror-jobs")]
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".legacy_online_custody_evidence_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return Path("/tmp")


def main():
    if "sc.legacy.file.index" not in env:  # noqa: F821
        raise RuntimeError("model not found: sc.legacy.file.index")
    FileIndex = env["sc.legacy.file.index"].sudo().with_context(active_test=False)  # noqa: F821
    roots = [root.resolve() for root in _legacy_file_roots()]
    records = FileIndex.search(_source_domain(), order="source_table, id")
    counts = Counter()
    source_counts = Counter()
    examples = []
    for item in records:
        counts["file_index_rows"] += 1
        source_counts[item.source_table or ""] += 1
        relative = str(item.preview_path or item.file_path or "").strip()
        if not relative:
            counts["missing_index_path"] += 1
            if len(examples) < EXAMPLE_LIMIT:
                examples.append(
                    {
                        "kind": "missing_index_path",
                        "id": item.id,
                        "source_table": item.source_table,
                        "legacy_file_key": item.legacy_file_key,
                        "file_name": item.file_name,
                    }
                )
            continue
        resolved = _resolve_with_roots(relative, roots)
        if not resolved:
            counts["files_local_missing"] += 1
            if len(examples) < EXAMPLE_LIMIT:
                examples.append(
                    {
                        "kind": "missing_local_file",
                        "id": item.id,
                        "source_table": item.source_table,
                        "legacy_file_key": item.legacy_file_key,
                        "file_name": item.file_name,
                        "relative_path": relative,
                    }
                )
            continue
        if resolved.stat().st_size <= 0:
            counts["zero_size_local_file"] += 1
            if len(examples) < EXAMPLE_LIMIT:
                examples.append(
                    {
                        "kind": "zero_size_local_file",
                        "id": item.id,
                        "source_table": item.source_table,
                        "legacy_file_key": item.legacy_file_key,
                        "file_name": item.file_name,
                        "relative_path": relative,
                        "resolved_path": str(resolved),
                    }
                )
            continue
        counts["files_local_ok"] += 1

    failures = (
        int(counts.get("missing_index_path") or 0)
        + int(counts.get("files_local_missing") or 0)
        + int(counts.get("zero_size_local_file") or 0)
    )
    payload = {
        "status": "PASS" if failures == 0 else "FAIL",
        "model": "sc.legacy.file.index.online_custody_evidence",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_name": env.cr.dbname,  # noqa: F821
        "mirror_root": ":".join(str(item) for item in roots),
        "source_contains": SOURCE_CONTAINS,
        "counts": dict(counts),
        "source_counts": dict(source_counts.most_common()),
        "examples": examples,
    }
    job_root = _safe_job_root()
    run_dir = job_root / ("custody_evidence_%s" % datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    run_dir.mkdir(parents=True, exist_ok=True)
    output = run_dir / "sc_legacy_file_index_online_custody_evidence.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "scope": "legacy_online_attachment_custody_evidence",
        "status": payload["status"],
        "database": payload["db_name"],
        "job_root": str(job_root),
        "output": str(output),
        "file_index_rows": int(counts.get("file_index_rows") or 0),
        "files_local_ok": int(counts.get("files_local_ok") or 0),
        "files_local_missing": int(counts.get("files_local_missing") or 0),
        "zero_size_local_file": int(counts.get("zero_size_local_file") or 0),
        "missing_index_path": int(counts.get("missing_index_path") or 0),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    if failures:
        raise SystemExit(1)


main()
