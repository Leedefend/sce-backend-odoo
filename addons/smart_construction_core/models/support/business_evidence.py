# -*- coding: utf-8 -*-
import json

from odoo import api, fields, models


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
        existing = self.search(
            [
                ("source_model", "=", source_model),
                ("source_id", "=", int(source_id)),
                ("evidence_type", "=", evidence_type),
            ],
            limit=1,
        )
        if existing:
            existing.write(payload)
            return existing
        return self.create(payload)

    @staticmethod
    def _json_dumps(value):
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        except TypeError:
            return json.dumps({"value": str(value)}, ensure_ascii=False, sort_keys=True)
