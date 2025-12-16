# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID
from odoo.tools import config
import sys


def main():
    # 读取容器内 Odoo 配置
    config.parse_config(["-c", "/etc/odoo/odoo.conf"])
    db = config["db_name"]
    registry = odoo.registry(db)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        code = env["sc.data.validator"].run_cli()
        sys.exit(code)


if __name__ == "__main__":
    main()
