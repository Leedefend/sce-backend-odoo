# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ScScenePackageInstallation(models.Model):
    _name = "sc.scene.package.installation"
    _description = "SC Scene Package Installation"
    _order = "installed_at desc, id desc"

    package_name = fields.Char(required=True, index=True)
    installed_version = fields.Char(required=True)
    installed_at = fields.Datetime(required=True, default=fields.Datetime.now)
    last_upgrade_at = fields.Datetime()
    channel = fields.Char()
    source = fields.Selection(
        [("import", "Import"), ("export", "Export")],
        required=True,
        default="import",
    )
    checksum = fields.Char()
    active = fields.Boolean(default=True, index=True)

    @api.constrains("package_name", "active")
    def _check_single_active_per_package(self):
        for rec in self:
            if not rec.active or not rec.package_name:
                continue
            conflict = self.search_count([
                ("id", "!=", rec.id),
                ("package_name", "=", rec.package_name),
                ("active", "=", True),
            ])
            if conflict:
                raise ValidationError("Only one active installation is allowed per package_name.")
