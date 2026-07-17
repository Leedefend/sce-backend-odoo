#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { launchChromium } from './playwright_runtime.mjs';

const ROOT = process.cwd();
const PHASE = process.env.FE_PRO_04WR3_PHASE || 'final';
const OUTPUT_ROOT = path.join(ROOT, 'artifacts/frontend-professional/fe-pro-04wr3');
const OUTPUT = path.join(OUTPUT_ROOT, PHASE);
const REPORT = path.join(OUTPUT_ROOT, `${PHASE}-report.json`);
const FORM_SECTION = path.join(ROOT, 'frontend/apps/web/src/components/template/FormSection.vue');
const WIDTHS = [639, 680, 1239, 1240, 1920];
const COLUMNS = [1, 2, 3];
const SPANS = ['compact', 'normal', 'wide', 'full'];

function check(value, message) {
  if (!value) throw new Error(message);
}

function productionStyle() {
  const source = fs.readFileSync(FORM_SECTION, 'utf8');
  const match = source.match(/<style scoped>([\s\S]*?)<\/style>/);
  check(match, 'FormSection scoped style not found');
  return match[1];
}

function expectedTrackCount(columns, width) {
  if (width < 680 || columns === 1) return 1;
  if (columns === 3 && width >= 1240) return 3;
  return 2;
}

function expectedSpan(columns, span, width) {
  const tracks = expectedTrackCount(columns, width);
  if (span === 'full') return tracks;
  if (span === 'wide') return Math.min(2, tracks);
  return 1;
}

function fixtureMarkup(columns, span, width) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>
    :root { --sc-app-border: #cbd5e1; --sc-app-text-primary: #0f172a; --sc-app-focus-ring: #93c5fd; }
    * { box-sizing: border-box; }
    body { margin: 0; padding: 24px; font: 14px sans-serif; color: #0f172a; background: #f8fafc; }
    .fixture { width: ${width}px; max-width: 100%; padding: 20px; background: white; border: 1px solid #cbd5e1; }
    .field { min-height: 64px; padding: 12px; background: #eff6ff; border: 1px solid #93c5fd; }
    ${productionStyle()}
  </style></head><body>
    <section class="template-form-section fixture">
      <div id="grid" class="template-form-section-grid template-form-section-grid--columns-${columns}">
        <div id="field" class="field field--${span}">${columns} column contract / ${span}</div>
      </div>
    </section>
  </body></html>`;
}

async function measure(page, columns, span, width) {
  await page.setViewportSize({ width: Math.max(390, width + 48), height: 240 });
  await page.setContent(fixtureMarkup(columns, span, width), { waitUntil: 'domcontentloaded' });
  return page.evaluate(({ declaredColumns, declaredSpan, containerWidth }) => {
    const grid = document.querySelector('#grid');
    const field = document.querySelector('#field');
    const gridStyle = getComputedStyle(grid);
    const fieldStyle = getComputedStyle(field);
    const gridRect = grid.getBoundingClientRect();
    const fieldRect = field.getBoundingClientRect();
    const computedTracks = (gridStyle.gridTemplateColumns.match(/-?\d+(?:\.\d+)?px/g) || []).length;
    return {
      declared_columns: declaredColumns,
      field_span: declaredSpan,
      container_width: containerWidth,
      computed_grid_template_columns: gridStyle.gridTemplateColumns,
      computed_track_count: computedTracks,
      field_grid_column_start: fieldStyle.gridColumnStart,
      field_grid_column_end: fieldStyle.gridColumnEnd,
      field_width: Number(fieldRect.width.toFixed(2)),
      grid_width: Number(gridRect.width.toFixed(2)),
      overflow: Number(Math.max(0, fieldRect.right - gridRect.right, grid.scrollWidth - grid.clientWidth).toFixed(2)),
    };
  }, { declaredColumns: columns, declaredSpan: span, containerWidth: width });
}

async function captureFixture(page, style, entry) {
  await page.setViewportSize(entry.viewport);
  const available = entry.viewport.width === 390 ? 342 : entry.viewport.width === 1440 ? 1096 : 1576;
  await page.setContent(fixtureMarkup(entry.columns, entry.span, available), { waitUntil: 'domcontentloaded' });
  const screenshot = path.join(OUTPUT, `${entry.key}.png`);
  await page.screenshot({ path: screenshot, fullPage: true });
  return { ...entry, screenshot: path.relative(ROOT, screenshot), production_style_sha: style.length };
}

async function main() {
  fs.mkdirSync(OUTPUT, { recursive: true });
  const style = productionStyle();
  const browser = await launchChromium({ headless: true });
  try {
    const page = await browser.newPage();
    const matrix = [];
    for (const width of WIDTHS) {
      for (const columns of COLUMNS) {
        for (const span of SPANS) {
          const row = await measure(page, columns, span, width);
          row.expected_track_count = expectedTrackCount(columns, width);
          row.expected_span = expectedSpan(columns, span, width);
          row.implicit_track_count = Math.max(0, row.computed_track_count - row.expected_track_count);
          row.pass = row.implicit_track_count === 0 && row.field_width <= row.grid_width + 1 && row.overflow <= 1;
          matrix.push(row);
        }
      }
    }
    const screenshots = [];
    for (const entry of [
      { key: 'columns-1-wide-1440', columns: 1, span: 'wide', viewport: { width: 1440, height: 900 } },
      { key: 'columns-1-full-1440', columns: 1, span: 'full', viewport: { width: 1440, height: 900 } },
      { key: 'columns-2-wide-1440', columns: 2, span: 'wide', viewport: { width: 1440, height: 900 } },
      { key: 'columns-3-wide-1920', columns: 3, span: 'wide', viewport: { width: 1920, height: 1080 } },
      { key: 'columns-1-wide-390', columns: 1, span: 'wide', viewport: { width: 390, height: 844 } },
    ]) screenshots.push(await captureFixture(page, style, entry));
    const report = {
      schema_version: 'frontend_form_grid_span_matrix.v1',
      phase: PHASE,
      git_sha: process.env.GIT_SHA || '',
      form_section_blob: process.env.FORM_SECTION_BLOB || '',
      matrix,
      screenshots,
      failures: matrix.filter((row) => !row.pass),
    };
    fs.writeFileSync(REPORT, `${JSON.stringify(report, null, 2)}\n`);
    if (PHASE === 'final') check(report.failures.length === 0, `layout failures=${report.failures.length}`);
    console.log(`[frontend_form_grid_span_browser] ${PHASE === 'final' ? 'PASS' : 'CAPTURED'} rows=${matrix.length} failures=${report.failures.length}`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(`[frontend_form_grid_span_browser] FAIL ${error.stack || error.message}`);
  process.exitCode = 2;
});
