import fs from "node:fs";
import path from "node:path";

function findRepoRoot(start) {
  let current = path.resolve(start);
  for (let i = 0; i < 8; i += 1) {
    if (fs.existsSync(path.join(current, "frontend/apps/web/src/styles/product-patterns.css"))) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  throw new Error(`Unable to locate repo root from ${start}`);
}

const ROOT = findRepoRoot(process.cwd());

function read(relPath) {
  return fs.readFileSync(path.join(ROOT, relPath), "utf8");
}

function fail(message, details = {}) {
  console.error(JSON.stringify({ ok: false, message, details }, null, 2));
  process.exit(1);
}

function assertContains(file, pattern, message) {
  const content = read(file);
  if (!pattern.test(content)) fail(message, { file, pattern: String(pattern) });
}

function assertNotContains(file, pattern, message) {
  const content = read(file);
  if (pattern.test(content)) fail(message, { file, pattern: String(pattern) });
}

function pageModesFromRuntimeSource() {
  const content = read("frontend/apps/web/src/app/pageMode.ts");
  const match = content.match(/export const PAGE_MODES = \[([^\]]+)\] as const;/s);
  if (!match) fail("PAGE_MODES must be exported from pageMode.ts");
  const modes = Array.from(match[1].matchAll(/'([^']+)'/g)).map((item) => item[1]);
  if (!modes.length) fail("PAGE_MODES must not be empty");
  return modes;
}

function walkFiles(dir, result = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === "dist" || entry.name === "dist-dev" || entry.name === "node_modules") continue;
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walkFiles(fullPath, result);
    } else if (/\.(vue|ts|tsx|js|jsx|mjs)$/.test(entry.name)) {
      result.push(fullPath);
    }
  }
  return result;
}

const shellFiles = [
  "frontend/apps/web/src/views/ActionView.vue",
  "frontend/apps/web/src/pages/ListPage.vue",
  "frontend/apps/web/src/pages/KanbanPage.vue",
  "frontend/apps/web/src/views/RecordView.vue",
  "frontend/apps/web/src/pages/ModelListPage.vue",
  "frontend/apps/web/src/views/PlaceholderView.vue",
];

const regionFiles = [
  {
    file: "frontend/apps/web/src/components/page/PageHeader.vue",
    markers: [/sc-product-page-header/],
  },
  {
    file: "frontend/apps/web/src/components/template/PageHeader.vue",
    markers: [/sc-product-page-header/],
  },
  {
    file: "frontend/apps/web/src/pages/ListPage.vue",
    markers: [/sc-product-page-toolbar/, /sc-product-summary-strip/, /sc-product-feedback-layer/, /sc-product-main-surface/],
  },
  {
    file: "frontend/apps/web/src/pages/KanbanPage.vue",
    markers: [/sc-product-page-toolbar/, /sc-product-main-surface/],
  },
  {
    file: "frontend/apps/web/src/views/RecordView.vue",
    markers: [/sc-product-page-header/, /sc-product-primary-actions/, /sc-product-main-surface/],
  },
  {
    file: "frontend/apps/web/src/pages/ContractFormPage.vue",
    markers: [/sc-product-main-surface/],
  },
  {
    file: "frontend/apps/web/src/views/BusinessConfigSurfaceView.vue",
    markers: [/sc-product-page-header/, /sc-product-main-surface/],
  },
  {
    file: "frontend/apps/web/src/views/MenuConfigView.vue",
    markers: [/sc-product-page-header/, /sc-product-main-surface/],
  },
];

const pageModeFiles = [
  { file: "frontend/apps/web/src/views/ActionView.vue", mode: "list" },
  { file: "frontend/apps/web/src/pages/ListPage.vue", mode: "list" },
  { file: "frontend/apps/web/src/pages/KanbanPage.vue", mode: "list" },
  { file: "frontend/apps/web/src/views/RecordView.vue", mode: "detail" },
  { file: "frontend/apps/web/src/pages/ModelListPage.vue", mode: "list" },
  { file: "frontend/apps/web/src/views/PlaceholderView.vue", mode: "workspace" },
  { file: "frontend/apps/web/src/pages/ContractFormPage.vue", mode: "form" },
  { file: "frontend/apps/web/src/views/BusinessConfigSurfaceView.vue", mode: "admin" },
  { file: "frontend/apps/web/src/views/MenuConfigView.vue", mode: "admin" },
];

const ALLOWED_PAGE_MODES = pageModesFromRuntimeSource();

assertContains(
  "frontend/apps/web/src/styles/product-patterns.css",
  /--sc-product-workspace-gap:\s*0px;/,
  "product workspace gap token must be defined at product level",
);
assertContains(
  "frontend/apps/web/src/styles/product-patterns.css",
  /--sc-product-workspace-stack-gap:\s*12px;/,
  "product workspace stack gap token must be defined at product level",
);
assertContains(
  "frontend/apps/web/src/styles/product-patterns.css",
  /\.sc-product-workspace\s*\{\s*gap:\s*var\(--sc-product-workspace-gap\);/s,
  "product workspace class must use product workspace gap token",
);
assertContains(
  "frontend/apps/web/src/styles/product-patterns.css",
  /\.sc-product-workspace-stack\s*\{\s*row-gap:\s*var\(--sc-product-workspace-stack-gap\);/s,
  "product workspace stack class must use product stack gap token",
);
for (const marker of [
  "sc-product-page-header",
  "sc-product-page-toolbar",
  "sc-product-summary-strip",
  "sc-product-main-surface",
  "sc-product-primary-actions",
  "sc-product-feedback-layer",
]) {
  assertContains(
    "frontend/apps/web/src/styles/product-patterns.css",
    new RegExp(`\\.${marker}\\b`),
    `${marker} must be defined as a product page region marker`,
  );
}

for (const file of shellFiles) {
  assertContains(file, /sc-page/, "page shell must opt into product page surface");
  assertContains(file, /sc-product-workspace-stack/, "page shell must opt into product stack spacing");
  assertNotContains(file, /\.page\s*\{[^}]*\bgap:\s*(6px|16px);/s, "page shell must not hard-code legacy page gap");
}

for (const { file, markers } of regionFiles) {
  for (const marker of markers) {
    assertContains(file, marker, "page structure region must opt into product semantic marker");
  }
}

for (const { file, mode } of pageModeFiles) {
  assertContains(
    file,
    new RegExp(`data-product-page-mode=["']${mode}["']`),
    "page shell must expose its product page mode in DOM",
  );
}

for (const filePath of walkFiles(path.join(ROOT, "frontend/apps/web/src"))) {
  const relPath = path.relative(ROOT, filePath);
  const content = fs.readFileSync(filePath, "utf8");
  for (const match of content.matchAll(/data-product-page-mode=["']([^"']+)["']/g)) {
    const mode = match[1];
    if (!ALLOWED_PAGE_MODES.includes(mode)) {
      fail("data-product-page-mode must use a canonical product page mode", {
        file: relPath,
        mode,
        allowed: ALLOWED_PAGE_MODES,
      });
    }
  }
}

assertContains(
  "frontend/apps/web/src/app/pageMode.ts",
  /export type PageMode = typeof PAGE_MODES\[number\];/,
  "PageMode union must be derived from PAGE_MODES",
);
assertNotContains(
  "frontend/apps/web/src/app/pageMode.ts",
  /return 'ledger';/,
  "ledger is a layout kind, not a product page mode",
);

assertContains(
  "frontend/apps/web/src/pages/ContractFormPage.vue",
  /'sc-page'/,
  "business form shell must opt into product page surface",
);
assertContains(
  "frontend/apps/web/src/pages/ContractFormPage.vue",
  /'sc-panel'/,
  "business form main panel must use product panel surface",
);
assertContains(
  "frontend/apps/web/src/views/BusinessConfigSurfaceView.vue",
  /sc-product-workspace/,
  "business config workspace must use product workspace class",
);
assertContains(
  "frontend/apps/web/src/views/MenuConfigView.vue",
  /sc-product-workspace/,
  "menu config workspace must use product workspace class",
);

console.log(JSON.stringify({
  ok: true,
  schema_version: "product_page_structure_guard.v1",
  shell_files: shellFiles.length,
  region_files: regionFiles.length,
  page_mode_files: pageModeFiles.length,
}));
