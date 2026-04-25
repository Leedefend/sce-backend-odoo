# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyFileIndex(models.Model):
    _name = "sc.legacy.file.index"
    _description = "Legacy File Index Fact"
    _order = "upload_time desc, legacy_file_key"

    legacy_file_key = fields.Char(required=True, index=True)
    source_table = fields.Char(required=True, index=True)
    legacy_file_id = fields.Char(required=True, index=True)
    legacy_pid = fields.Char(index=True)
    bill_id = fields.Char(index=True)
    bill_type = fields.Char(index=True)
    business_id = fields.Char(index=True)
    file_system_data_id = fields.Char(index=True)
    file_name = fields.Char(required=True, index=True)
    file_path = fields.Char(required=True, index=True)
    preview_path = fields.Char()
    file_md5 = fields.Char(index=True)
    file_size = fields.Integer(index=True)
    extension = fields.Char(index=True)
    uploader_legacy_user_id = fields.Char(index=True)
    uploader_name = fields.Char(index=True)
    upload_time = fields.Datetime(index=True)
    deleter_legacy_user_id = fields.Char(index=True)
    deleter_name = fields.Char(index=True)
    delete_time = fields.Datetime(index=True)
    encrypted_flag = fields.Char(index=True)
    temporary_flag = fields.Char(index=True)
    note = fields.Text()
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ("legacy_file_key_unique", "unique(legacy_file_key)", "Legacy file key must be unique."),
    ]
