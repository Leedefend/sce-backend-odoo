import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const WEB_APP_ROOT = path.resolve(SCRIPT_DIR, "../..");

function readSource(relPath) {
  return fs.readFileSync(path.join(WEB_APP_ROOT, relPath), "utf8");
}

export function readPageModes() {
  const content = readSource("src/app/pageMode.ts");
  const match = content.match(/export const PAGE_MODES = \[([^\]]+)\] as const;/s);
  if (!match) throw new Error("PAGE_MODES must be exported from pageMode.ts");
  const modes = Array.from(match[1].matchAll(/'([^']+)'/g)).map((item) => item[1]);
  if (!modes.length) throw new Error("PAGE_MODES must not be empty");
  return modes;
}

export function readProductPageRegionClasses() {
  const content = readSource("src/app/productPageStructure.ts");
  const match = content.match(/export const PRODUCT_PAGE_REGION_CLASSES = \{([\s\S]+?)\} as const;/);
  if (!match) throw new Error("PRODUCT_PAGE_REGION_CLASSES must be exported from productPageStructure.ts");
  const classes = Object.fromEntries(
    Array.from(match[1].matchAll(/([a-zA-Z0-9_]+):\s*'([^']+)'/g)).map((item) => [item[1], item[2]]),
  );
  if (!Object.keys(classes).length) throw new Error("PRODUCT_PAGE_REGION_CLASSES must not be empty");
  return classes;
}
