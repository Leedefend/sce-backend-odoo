FROM node:22.17.0-bookworm-slim@sha256:b04ce4ae4e95b522112c2e5c52f781471a5cbc3b594527bcddedee9bc48c03a0 AS frontend-build

WORKDIR /build/frontend
COPY frontend/ ./
ARG FRONTEND_BUILD_SHA256
ARG VITE_ODOO_DB=sc_prod
ARG VITE_APP_ENV=production
ENV VITE_ODOO_DB=${VITE_ODOO_DB} \
    VITE_ODOO_DB_LOCKED=1 \
    VITE_APP_ENV=${VITE_APP_ENV} \
    VITE_BUILD_MODE=production \
    VITE_BUILD_OUT_DIR=/build/frontend/apps/web/dist
RUN corepack enable \
    && corepack prepare pnpm@9.12.3 --activate \
    && apt-get update \
    && apt-get install -y --no-install-recommends python3 \
    && rm -rf /var/lib/apt/lists/* \
    && pnpm install --frozen-lockfile \
    && pnpm -C packages/design-tokens build \
    && pnpm -C apps/web exec vite build --mode production \
    && calculated="$(cd apps/web/dist && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')" \
    && test -n "$FRONTEND_BUILD_SHA256" \
    && test "$calculated" = "$FRONTEND_BUILD_SHA256" \
    && printf '%s\n' "$calculated" > apps/web/dist/.build-sha256

FROM odoo:17.0@sha256:f88f646a0f5fc0b225995ee28953d9ce7367cc731b1756765114691fb97d18e5

ARG SOURCE_SHA
ARG FRONTEND_BUILD_SHA256
LABEL org.opencontainers.image.revision=${SOURCE_SHA} \
      io.sce.frontend.sha256=${FRONTEND_BUILD_SHA256} \
      io.sce.frontend.node.version="22.17.0-build-only" \
      io.sce.runtime.rtl="unsupported-ltr-only"

USER root

# Odoo 17 compiles the supported LTR web bundle through Python/libsass.  The
# product does not offer RTL locales, so the legacy Node/less/rtlcss toolchain
# is not part of the production runtime.  Frontend static assets are built in
# the separately pinned frontend build environment.
RUN apt-get update \
    && apt-get purge -y nodejs npm node-less libnode-dev libnode72 \
    && apt-get autoremove -y --purge \
    && rm -rf /usr/local/bin/rtlcss /usr/local/lib/node_modules/rtlcss \
    && ! command -v node \
    && ! command -v lessc \
    && ! command -v rtlcss \
    && ! dpkg-query -W 'node-*' 'libnode*' 2>/dev/null \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖（工程化：集中在 requirements-odoo.txt）
COPY requirements-odoo.txt /tmp/requirements-odoo.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements-odoo.txt

# Product addons are copied explicitly. Customer, demo, seed and migration
# modules must be mounted as separate delivery artifacts at runtime.
RUN mkdir -p /mnt/product-addons /mnt/customer-addons /mnt/test-addons /mnt/source-addons \
    && ln -s /mnt/product-addons /mnt/extra-addons
COPY --chown=odoo:odoo addons/sc_norm_engine/ /mnt/product-addons/sc_norm_engine/
COPY --chown=odoo:odoo addons/smart_core/ /mnt/product-addons/smart_core/
COPY --chown=odoo:odoo addons/smart_scene/ /mnt/product-addons/smart_scene/
COPY --chown=odoo:odoo addons/smart_license_core/ /mnt/product-addons/smart_license_core/
COPY --chown=odoo:odoo addons/smart_construction_core/ /mnt/product-addons/smart_construction_core/
COPY --chown=odoo:odoo addons/smart_construction_portal/ /mnt/product-addons/smart_construction_portal/
COPY --chown=odoo:odoo addons/smart_construction_scene/ /mnt/product-addons/smart_construction_scene/
COPY --chown=odoo:odoo addons/smart_construction_bundle/ /mnt/product-addons/smart_construction_bundle/
COPY --chown=odoo:odoo addons_external/oca_server_ux/ /mnt/addons_external/oca_server_ux/
COPY --chown=odoo:odoo --from=frontend-build /build/frontend/apps/web/dist/ /opt/sce/frontend/

USER odoo
