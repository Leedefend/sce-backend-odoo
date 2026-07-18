from __future__ import annotations

import os

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.smart_core.utils.tenant_delivery_manifest import (
    TenantDeliveryManifestError,
    manifest_sha256,
    validate_payload_manifest,
    verify_manifest_hmac,
)


class ScTenantPayloadImportBatch(models.Model):
    _name = "sc.tenant.payload.import.batch"
    _description = "Tenant payload import batch"
    _order = "create_date desc, id desc"

    payload_id = fields.Char(required=True, index=True, readonly=True)
    tenant_key = fields.Char(required=True, index=True, readonly=True)
    payload_version = fields.Char(required=True, readonly=True)
    schema_version = fields.Char(required=True, readonly=True)
    payload_hash = fields.Char(required=True, index=True, readonly=True)
    source_key = fields.Char(index=True, readonly=True)
    product_image_digest = fields.Char(readonly=True)
    customer_module_digest = fields.Char(readonly=True)
    signature_key_id = fields.Char(readonly=True)
    manifest_json = fields.Json(required=True, readonly=True)
    state = fields.Selection(
        [
            ("created", "Created"),
            ("verified", "Verified"),
            ("importing", "Importing"),
            ("paused", "Paused"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("rolled_back", "Rolled back"),
        ],
        required=True,
        default="created",
        index=True,
        readonly=True,
    )
    imported_count = fields.Integer(default=0, readonly=True)
    skipped_count = fields.Integer(default=0, readonly=True)
    failed_count = fields.Integer(default=0, readonly=True)
    checkpoint = fields.Json(default=dict, readonly=True)
    error_summary = fields.Text(readonly=True)
    acceptance_report = fields.Json(default=dict, readonly=True)
    started_at = fields.Datetime(readonly=True)
    completed_at = fields.Datetime(readonly=True)

    _sql_constraints = [
        ("tenant_payload_id_unique", "unique(tenant_key, payload_id)", "A tenant payload may only create one import batch."),
        ("tenant_payload_hash_unique", "unique(tenant_key, payload_hash)", "A tenant payload hash may only be imported once."),
        ("tenant_payload_counts_non_negative", "check(imported_count >= 0 and skipped_count >= 0 and failed_count >= 0)", "Import counters cannot be negative."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        normalized = []
        for vals in vals_list:
            item = dict(vals)
            manifest = item.get("manifest_json")
            if not isinstance(manifest, dict):
                raise ValidationError("manifest_json must be an object")
            try:
                validate_payload_manifest(manifest, expected_tenant_key=item.get("tenant_key"))
            except TenantDeliveryManifestError as exc:
                raise ValidationError(str(exc)) from exc
            signature = manifest.get("signature") or {}
            item.update(
                {
                    "payload_id": manifest["payload_id"],
                    "tenant_key": manifest["tenant_key"],
                    "payload_version": manifest["payload_version"],
                    "schema_version": manifest["schema_version"],
                    "payload_hash": manifest_sha256(manifest),
                    "signature_key_id": signature.get("key_id"),
                    "state": "created",
                }
            )
            normalized.append(item)
        return super().create(normalized)

    def action_verify(self, product_version):
        key = os.environ.get("SC_CUSTOMER_PAYLOAD_HMAC_KEY", "").encode("utf-8")
        if not key:
            raise UserError("SC_CUSTOMER_PAYLOAD_HMAC_KEY is required to verify a customer payload")
        for batch in self:
            if batch.state != "created":
                raise UserError("Only a created payload batch can be verified")
            try:
                validate_payload_manifest(
                    batch.manifest_json,
                    expected_tenant_key=batch.tenant_key,
                    product_version=product_version,
                )
                verify_manifest_hmac(batch.manifest_json, key)
            except TenantDeliveryManifestError as exc:
                raise UserError(str(exc)) from exc
            batch.write({"state": "verified", "error_summary": False})
        return True

    def action_start(self):
        for batch in self:
            if batch.state not in {"verified", "paused"}:
                raise UserError("Only a verified or paused payload batch can start")
            values = {"state": "importing", "error_summary": False}
            if not batch.started_at:
                values["started_at"] = fields.Datetime.now()
            batch.write(values)
        return True

    def update_checkpoint(self, *, checkpoint, imported_count, skipped_count, failed_count):
        for batch in self:
            if batch.state != "importing":
                raise UserError("Checkpoint updates require an importing payload batch")
            batch.write(
                {
                    "checkpoint": checkpoint or {},
                    "imported_count": imported_count,
                    "skipped_count": skipped_count,
                    "failed_count": failed_count,
                }
            )
        return True

    def action_pause(self):
        for batch in self:
            if batch.state != "importing":
                raise UserError("Only an importing payload batch can be paused")
            batch.write({"state": "paused"})
        return True

    def action_complete(self, acceptance_report):
        for batch in self:
            if batch.state != "importing":
                raise UserError("Only an importing payload batch can be completed")
            if batch.failed_count:
                raise UserError("A payload batch with failed rows cannot be completed")
            batch.write(
                {
                    "state": "completed",
                    "completed_at": fields.Datetime.now(),
                    "acceptance_report": acceptance_report or {},
                }
            )
        return True

    def action_fail(self, error_summary):
        for batch in self:
            if batch.state not in {"verified", "importing", "paused"}:
                raise UserError("This payload batch cannot transition to failed")
            batch.write({"state": "failed", "error_summary": str(error_summary or "")})
        return True

    def action_mark_rolled_back(self, acceptance_report=None):
        for batch in self:
            if batch.state != "failed":
                raise UserError("Only a failed payload batch can be marked rolled back")
            batch.write(
                {
                    "state": "rolled_back",
                    "acceptance_report": acceptance_report or {},
                    "completed_at": fields.Datetime.now(),
                }
            )
        return True

    def unlink(self):
        if not self.env.context.get("allow_audited_tenant_destroy"):
            raise UserError("Tenant payload batches are immutable. Use the audited tenant-destroy workflow.")
        return super().unlink()
