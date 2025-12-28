FROM odoo:17.0

USER root

# 安装 Python 依赖（工程化：集中在 requirements-odoo.txt）
COPY requirements-odoo.txt /tmp/requirements-odoo.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements-odoo.txt

USER odoo
