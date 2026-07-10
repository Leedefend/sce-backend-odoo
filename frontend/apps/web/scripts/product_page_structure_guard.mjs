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

const shellFiles = [
  "frontend/apps/web/src/views/ActionView.vue",
  "frontend/apps/web/src/pages/ListPage.vue",
  "frontend/apps/web/src/pages/KanbanPage.vue",
  "frontend/apps/web/src/views/RecordView.vue",
  "frontend/apps/web/src/pages/ModelListPage.vue",
  "frontend/apps/web/src/views/PlaceholderView.vue",
];

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

for (const file of shellFiles) {
  assertContains(file, /sc-page/, "page shell must opt into product page surface");
  assertContains(file, /sc-product-workspace-stack/, "page shell must opt into product stack spacing");
  assertNotContains(file, /\.page\s*\{[^}]*\bgap:\s*(6px|16px);/s, "page shell must not hard-code legacy page gap");
}

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
}));
