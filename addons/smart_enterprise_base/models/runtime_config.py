# -*- coding: utf-8 -*-

from odoo import api, models


class SmartEnterpriseBaseRuntimeConfig(models.AbstractModel):
    _name = "smart.enterprise.base.runtime"
    _description = "Smart Enterprise Base Runtime Config"

    @api.model
    def ensure_extension_module_registration(self):
        icp = self.env["ir.config_parameter"].sudo()
        raw_value = str(icp.get_param("sc.core.extension_modules") or "").strip()
        modules = []
        seen = set()
        for item in [segment.strip() for segment in raw_value.split(",") if segment.strip()]:
            if item in seen:
                continue
            seen.add(item)
            modules.append(item)
        if "smart_enterprise_base" not in seen:
            modules.append("smart_enterprise_base")
        icp.set_param("sc.core.extension_modules", ",".join(modules))
        return True
