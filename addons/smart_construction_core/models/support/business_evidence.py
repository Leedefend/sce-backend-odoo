# -*- coding: utf-8 -*-
import hashlib
import json

from odoo import api, fields, models
from odoo.exceptions import UserError


class ScBusinessEvidence(models.Model):
    _name = "sc.business.evidence"
    _description = "Business Evidence"
    _order = "operate_time desc, id desc"

    name = fields.Char(required=True, index=True)
    business_model = fields.Char(required=True, index=True)
    business_id = fields.Integer(required=True, index=True)
    evidence_type = fields.Selection(
        [
            ("payment", "Payment"),
            ("cost", "Cost"),
            ("settlement", "Settlement"),
            ("progress", "Progress"),
        ],
        required=True,
        index=True,
    )
    amount = fields.Float()
    quantity = fields.Float()
    source_model = fields.Char(index=True)
    source_id = fields.Integer(index=True)
    operator_id = fields.Many2one("res.users", index=True)
    operate_time = fields.Datetime(default=fields.Datetime.now, required=True, index=True)
    relation_chain = fields.Text()
    checksum = fields.Char(index=True, readonly=True)

    _sql_constraints = [
        (
            "uniq_sc_business_evidence_source",
            "unique(source_model, source_id, evidence_type)",
            "同一来源记录只能生成一条对应类型的业务证据。",
        ),
    ]

    @api.model
    def upsert_evidence(
        self,
        *,
        name,
        business_model,
        business_id,
        evidence_type,
        source_model,
        source_id,
        amount=None,
        quantity=None,
        operator=None,
        relation_chain=None,
    ):
        operator = operator or self.env.user
        payload = {
            "name": name,
            "business_model": business_model,
            "business_id": int(business_id),
            "evidence_type": evidence_type,
            "amount": float(amount or 0.0),
            "quantity": float(quantity or 0.0),
            "source_model": source_model,
            "source_id": int(source_id),
            "operator_id": operator.id if operator else False,
            "operate_time": fields.Datetime.now(),
            "relation_chain": self._json_dumps(relation_chain or {}),
        }
        payload["checksum"] = self._build_checksum(payload)
        existing = self.search(
            [
                ("source_model", "=", source_model),
                ("source_id", "=", int(source_id)),
                ("evidence_type", "=", evidence_type),
            ],
            limit=1,
        )
        if existing:
            existing.with_context(allow_evidence_mutation=True).write(payload)
            return existing
        return self.with_context(allow_evidence_mutation=True).create(payload)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get("allow_evidence_mutation"):
            raise UserError("Business evidence is immutable and can only be produced by the evidence builder.")
        updated = []
        for vals in vals_list:
            row = dict(vals)
            row["checksum"] = row.get("checksum") or self._build_checksum(row)
            updated.append(row)
        return super().create(updated)

    def write(self, vals):
        if not self.env.context.get("allow_evidence_mutation"):
            raise UserError("Business evidence is immutable and cannot be edited directly.")
        updated = dict(vals)
        sample = self[:1]
        updated["checksum"] = self._build_checksum(
            {
                "name": updated.get("name", sample.name if sample else ""),
                "business_model": updated.get("business_model", sample.business_model if sample else ""),
                "business_id": updated.get("business_id", sample.business_id if sample else 0),
                "evidence_type": updated.get("evidence_type", sample.evidence_type if sample else ""),
                "amount": updated.get("amount", sample.amount if sample else 0.0),
                "quantity": updated.get("quantity", sample.quantity if sample else 0.0),
                "source_model": updated.get("source_model", sample.source_model if sample else ""),
                "source_id": updated.get("source_id", sample.source_id if sample else 0),
                "relation_chain": updated.get("relation_chain", sample.relation_chain if sample else ""),
            }
        )
        return super().write(updated)

    def unlink(self):
        if not self.env.context.get("allow_evidence_mutation"):
            raise UserError("Business evidence is immutable and cannot be deleted directly.")
        return super().unlink()

    @staticmethod
    def _json_dumps(value):
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        except TypeError:
            return json.dumps({"value": str(value)}, ensure_ascii=False, sort_keys=True)

    @classmethod
    def _build_checksum(cls, payload):
        raw = cls._json_dumps(
            {
                "name": payload.get("name"),
                "business_model": payload.get("business_model"),
                "business_id": payload.get("business_id"),
                "evidence_type": payload.get("evidence_type"),
                "amount": payload.get("amount"),
                "quantity": payload.get("quantity"),
                "source_model": payload.get("source_model"),
                "source_id": payload.get("source_id"),
                "relation_chain": payload.get("relation_chain"),
            }
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
