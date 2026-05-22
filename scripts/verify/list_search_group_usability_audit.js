#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

const requireBase = fs.existsSync(path.join(process.cwd(), 'frontend/apps/web/package.json'))
  ? path.join(process.cwd(), 'frontend/apps/web/package.json')
  : path.join(process.cwd(), 'package.json');
const requireFromRoot = createRequire(requireBase);
const { chromium } = requireFromRoot('playwright');

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5174';
const DB_NAME = process.env.DB_NAME || 'sc_prod_sim';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ACTION_ID = Number(process.env.ACTION_ID || 506);
const MENU_ID = Number(process.env.MENU_ID || 353);
const SEARCH_TERM = process.env.SEARCH_TERM || 'Role Smoke User';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'list-search-group-usability', ts);
const FAVORITE_NAME = process.env.FAVORITE_NAME || `LSG-AUDIT-${ts}`;

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function clean(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function attachConsoleCapture(page) {
  page.__consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') page.__consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => {
    page.__consoleErrors.push(err.message);
  });
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  const dbInput = inputs.nth(2);
  if (await dbInput.count().catch(() => 0)) {
    const disabled = await dbInput.isDisabled().catch(() => false);
    if (!disabled) await dbInput.fill(DB_NAME);
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), null, { timeout: 30000 });
}

async function openList(page, extra = '') {
  const suffix = extra ? `&${extra.replace(/^\?/, '').replace(/^&/, '')}` : '';
  await page.goto(`${FRONTEND_URL}/a/${ACTION_ID}?menu_id=${MENU_ID}&action_id=${ACTION_ID}${suffix}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForListReady(page);
}

async function waitForListReady(page) {
  await page.locator('.template-layout-shell, .page').first().waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.body?.textContent || '');
    return !text.includes('正在加载列表') && !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
}

async function waitForGroupFacet(page, label) {
  await page.waitForFunction((targetLabel) => {
    const facets = Array.from(document.querySelectorAll('.search-facet'));
    return facets.some((node) => {
      if (!(node instanceof HTMLElement)) return false;
      const rect = node.getBoundingClientRect();
      const visible = rect.width > 0 && rect.height > 0;
      const enabled = !(node instanceof HTMLButtonElement) || !node.disabled;
      return visible && enabled && String(node.textContent || '').includes(targetLabel);
    }) || facets.some((node) => {
      if (!(node instanceof HTMLElement)) return false;
      const rect = node.getBoundingClientRect();
      const enabled = !(node instanceof HTMLButtonElement) || !node.disabled;
      return rect.width > 0 && rect.height > 0 && enabled;
    });
  }, label, { timeout: 20000 });
}

async function snapshot(page) {
  return page.evaluate(() => {
    const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const flatRows = Array.from(document.querySelectorAll('section.table > table > tbody > tr'));
    const groupedBlocks = Array.from(document.querySelectorAll('.grouped-table .group-block'));
    const groupRows = Array.from(document.querySelectorAll('.grouped-table tbody tr'));
    const groupPages = groupedBlocks.map((block, index) => {
      const buttons = Array.from(block.querySelectorAll('.group-page-btn'));
      return {
        index,
        label: normalize(block.querySelector('.group-head p')?.textContent || ''),
        count_text: normalize(block.querySelector('.group-head span')?.textContent || ''),
        page_text: normalize(block.querySelector('.group-page')?.textContent || ''),
        row_count: block.querySelectorAll('tbody tr').length,
        prev_disabled: buttons[0] instanceof HTMLButtonElement ? buttons[0].disabled : true,
        next_disabled: buttons[1] instanceof HTMLButtonElement ? buttons[1].disabled : true,
      };
    });
    const searchDropdown = document.querySelector('.search-dropdown');
    const dropdownSections = Array.from(document.querySelectorAll('.search-dropdown-section')).map((section) => ({
      title: normalize(section.querySelector('.search-dropdown-title')?.textContent || ''),
      items: Array.from(section.querySelectorAll('.search-menu-item, .custom-group-select option'))
        .map((node) => normalize(node.textContent || ''))
        .filter(Boolean),
    }));
    const searchInput = document.querySelector('.native-searchbox input[type="search"]');
    const plainSearchInput = document.querySelector('.list-plain-search input[type="search"]');
    const flatHeaders = Array.from(document.querySelectorAll('section.table > table > thead th')).map((node) => normalize(node.textContent || ''));
    const sortableColumns = Array.from(document.querySelectorAll('section.table > table > thead th.cell-sortable')).map((node) => ({
      name: node.getAttribute('data-column') || '',
      label: normalize(node.textContent || ''),
      sorted: node.classList.contains('is-sorted'),
      width: Math.round(node.getBoundingClientRect().width),
    })).filter((row) => row.name);
    const flatFirstRowCells = Array.from(document.querySelectorAll('section.table > table > tbody > tr:first-child td')).map((node) => normalize(node.textContent || ''));
    const footerRows = Array.from(document.querySelectorAll('section.table > table > tfoot tr')).map((row) =>
      Array.from(row.querySelectorAll('th,td')).map((node) => normalize(node.textContent || ''))
    );
    const rowNumberCell = document.querySelector('section.table > table > tbody > tr:first-child td.cell-row-number');
    const rowNumberStyle = rowNumberCell ? window.getComputedStyle(rowNumberCell) : null;
    const headerCell = document.querySelector('section.table > table > thead th');
    const headerStyle = headerCell ? window.getComputedStyle(headerCell) : null;
    const pageSizeInputs = Array.from(document.querySelectorAll('.pagination-input--size')).map((node) => node.value || '');
    const firstGroup = groupedBlocks[0] || null;
    const groupedHeaders = firstGroup
      ? Array.from(firstGroup.querySelectorAll('table thead th')).map((node) => normalize(node.textContent || ''))
      : [];
    const groupedRowNumbers = groupRows
      .map((row) => normalize(row.querySelector('td')?.textContent || ''))
      .filter(Boolean);
    return {
      url: window.location.href,
      search_value: searchInput ? searchInput.value : '',
      plain_search_value: plainSearchInput ? plainSearchInput.value : '',
      facet_texts: Array.from(document.querySelectorAll('.search-facet')).map((node) => normalize(node.textContent || '')).filter(Boolean),
      facets: Array.from(document.querySelectorAll('.search-facet')).map((node) => ({
        text: normalize(node.textContent || ''),
        disabled: node instanceof HTMLButtonElement ? node.disabled : false,
      })),
      search_menu_enabled: !document.querySelector('.search-menu-toggle')?.disabled,
      dropdown_open: Boolean(searchDropdown),
      dropdown_sections: dropdownSections,
      flat_table_count: document.querySelectorAll('section.table > table').length,
      flat_row_count: flatRows.length,
      flat_headers: flatHeaders,
      sortable_columns: sortableColumns,
      flat_first_row_cells: flatFirstRowCells,
      footer_rows: footerRows,
      page_size_inputs: pageSizeInputs,
      row_number_style: {
        position: rowNumberStyle?.position || '',
        left: rowNumberStyle?.left || '',
        text_align: rowNumberStyle?.textAlign || '',
      },
      header_style: {
        position: headerStyle?.position || '',
        top: headerStyle?.top || '',
      },
      grouped_table_count: document.querySelectorAll('.grouped-table').length,
      group_block_count: groupedBlocks.length,
      group_row_count: groupRows.length,
      grouped_headers: groupedHeaders,
      grouped_row_numbers: groupedRowNumbers,
      group_pages: groupPages,
      group_toolbar_text: normalize(document.querySelector('.grouped-toolbar')?.textContent || ''),
      pagination_text: normalize(document.querySelector('.pagination-actions--top')?.textContent || ''),
      footer_text: normalize(document.querySelector('section.table > table > tfoot')?.textContent || ''),
      footer_stat_count: document.querySelectorAll('section.table > table > tfoot td.footer-number').length,
      visible_error: normalize(document.querySelector('.status-panel.error, .validation-error')?.textContent || ''),
      visible_empty: normalize(document.querySelector('.status-panel.info')?.textContent || ''),
      text_sample: normalize(document.body?.textContent || '').slice(0, 1200),
    };
  });
}

async function openSearchMenu(page) {
  const toggle = page.locator('.search-menu-toggle').first();
  await toggle.waitFor({ timeout: 10000 });
  if (!(await page.locator('.search-dropdown').count())) {
    await toggle.click();
  }
  await page.locator('.search-dropdown').waitFor({ timeout: 10000 });
}

async function openCustomFilterPanel(page) {
  await openSearchMenu(page);
  const button = page.locator('.search-dropdown-section').filter({ hasText: /筛选/ }).first()
    .locator('button.custom-entry')
    .filter({ hasText: /自定义筛选|添加/ })
    .first();
  await button.waitFor({ state: 'visible', timeout: 10000 });
  await button.click();
  await page.locator('.custom-search-panel').first().waitFor({ state: 'visible', timeout: 10000 });
}

async function selectUsableCustomFilter(page) {
  const panel = page.locator('.custom-search-panel').first();
  const fieldSelect = panel.locator('select').nth(0);
  const fieldOptions = await fieldSelect.locator('option').evaluateAll((options) => options.map((node) => ({
    value: node.getAttribute('value') || '',
    text: String(node.textContent || '').trim(),
  })));
  const field = fieldOptions.find((row) => row.value && /状态|阶段|项目名称|名称/.test(row.text))
    || fieldOptions.find((row) => row.value);
  if (!field) return null;
  await fieldSelect.selectOption(field.value);
  await page.waitForTimeout(100);

  const selects = panel.locator('select');
  const selectCount = await selects.count();
  let value = '';
  if (selectCount >= 3) {
    const valueSelect = selects.nth(2);
    const valueOptions = await valueSelect.locator('option').evaluateAll((options) => options.map((node) => ({
      value: node.getAttribute('value') || '',
      text: String(node.textContent || '').trim(),
    })));
    const selectedValue = valueOptions.find((row) => row.value && /在建|进行|草稿|筹备|启用|是/.test(row.text))
      || valueOptions.find((row) => row.value);
    if (!selectedValue) return null;
    value = selectedValue.value;
    await valueSelect.selectOption(selectedValue.value);
  } else {
    const input = panel.locator('input').first();
    value = SEARCH_TERM;
    await input.fill(value);
  }
  return {
    field: field.value,
    label: field.text,
    value,
  };
}

async function applyFirstGroup(page) {
  await openSearchMenu(page);
  const groupSection = page.locator('.search-dropdown-section').filter({ hasText: /分组/ }).first();
  const buttons = groupSection.locator('button.search-menu-item');
  const count = await buttons.count();
  for (let index = 0; index < count; index += 1) {
    const label = clean(await buttons.nth(index).textContent());
    if (!label || /添加自定义分组/.test(label)) continue;
    await buttons.nth(index).click();
    await page.waitForFunction(() => new URL(window.location.href).searchParams.has('group_by'), null, { timeout: 10000 });
    await waitForListReady(page);
    await page.waitForFunction(() => document.querySelectorAll('.grouped-table .group-block').length > 0, null, { timeout: 20000 });
    await waitForGroupFacet(page, label);
    return label;
  }
  const select = groupSection.locator('select.custom-group-select').first();
  if (await select.count()) {
    const values = await select.locator('option').evaluateAll((options) => options.map((node) => ({
      value: node.getAttribute('value') || '',
      text: String(node.textContent || '').trim(),
    })));
    const option = values.find((row) => row.value);
    if (option) {
      await select.selectOption(option.value);
      await page.waitForFunction(() => new URL(window.location.href).searchParams.has('group_by'), null, { timeout: 10000 });
      await waitForListReady(page);
      await page.waitForFunction(() => document.querySelectorAll('.grouped-table .group-block').length > 0, null, { timeout: 20000 });
      await waitForGroupFacet(page, option.text || option.value);
      return option.text || option.value;
    }
  }
  return '';
}

async function applyFirstCustomGroup(page) {
  await openSearchMenu(page);
  const groupSection = page.locator('.search-dropdown-section').filter({ hasText: /分组/ }).first();
  const select = groupSection.locator('select.custom-group-select').first();
  await select.waitFor({ state: 'visible', timeout: 10000 });
  const values = await select.locator('option').evaluateAll((options) => options.map((node) => ({
    value: node.getAttribute('value') || '',
    text: String(node.textContent || '').trim(),
  })));
  const option = values.find((row) => row.value);
  if (!option) return null;
  await select.selectOption(option.value);
  await page.waitForFunction(() => new URL(window.location.href).searchParams.has('group_by'), null, { timeout: 10000 });
  await waitForListReady(page);
  await page.waitForFunction(() => document.querySelectorAll('.grouped-table .group-block').length > 0, null, { timeout: 20000 });
  await waitForGroupFacet(page, option.text || option.value);
  return option;
}

async function saveCurrentSearchAsFavorite(page, name) {
  const result = { attempted: false, saved_visible: false, error: '' };
  try {
    await openSearchMenu(page);
    const favoriteSection = page.locator('.search-dropdown-section').filter({ hasText: /收藏/ }).first();
    const saveButton = favoriteSection.locator('button.custom-entry').filter({ hasText: /加入收藏|保存当前搜索|收藏/ }).first();
    await saveButton.waitFor({ state: 'visible', timeout: 10000 });
    await saveButton.click();
    const panel = favoriteSection.locator('.custom-search-panel').first();
    await panel.waitFor({ state: 'visible', timeout: 10000 });
    await panel.locator('input').first().fill(name);
    await panel.locator('button').filter({ hasText: /^保存$/ }).first().click();
    result.attempted = true;
    await waitForListReady(page).catch(() => {});
    await page.waitForFunction(() => document.querySelectorAll('.custom-search-panel').length === 0, null, { timeout: 10000 }).catch(() => {});
    await page.waitForTimeout(2500);
    await openSearchMenu(page);
    result.saved_visible = await page.waitForFunction((favoriteName) => {
      const dropdown = document.querySelector('.search-dropdown');
      return Boolean(dropdown && String(dropdown.textContent || '').includes(favoriteName));
    }, name, { timeout: 20000 }).then(() => true).catch(() => false);
    if (!result.saved_visible) {
      await page.reload({ waitUntil: 'domcontentloaded', timeout: 45000 }).catch(() => {});
      await waitForListReady(page).catch(() => {});
      await openSearchMenu(page);
      result.saved_visible = await page.waitForFunction((favoriteName) => {
        const dropdown = document.querySelector('.search-dropdown');
        return Boolean(dropdown && String(dropdown.textContent || '').includes(favoriteName));
      }, name, { timeout: 20000 }).then(() => true).catch(() => false);
    }
  } catch (err) {
    result.error = err instanceof Error ? err.message : String(err);
  }
  return result;
}

async function clearFacetByLabel(page, label) {
  const debug = [];
  let clicked = false;
  for (let attempt = 0; attempt < 5; attempt += 1) {
    await waitForGroupFacet(page, label).catch(() => {});
    await page.evaluate((targetLabel) => {
      const facets = Array.from(document.querySelectorAll('.search-facet'));
      const targetNode = facets.find((node) => String(node.textContent || '').includes(targetLabel)) || facets[0];
      if (targetNode instanceof HTMLElement) {
        targetNode.scrollIntoView({ block: 'center', inline: 'center' });
      }
    }, label).catch(() => {});
    await page.waitForTimeout(200);
    const facetState = await page.evaluate((targetLabel) => {
      const facets = Array.from(document.querySelectorAll('.search-facet')).filter((node) => {
        if (!(node instanceof HTMLElement)) return false;
        const rect = node.getBoundingClientRect();
        const enabled = !(node instanceof HTMLButtonElement) || !node.disabled;
        return rect.width > 0 && rect.height > 0 && enabled;
      });
      const targetNode = facets.find((node) => String(node.textContent || '').includes(targetLabel)) || facets[0];
      if (!(targetNode instanceof HTMLElement)) {
        return { count: facets.length, texts: facets.map((node) => String(node.textContent || '').trim()), box: null };
      }
      const rect = targetNode.getBoundingClientRect();
      return {
        count: facets.length,
        texts: facets.map((node) => String(node.textContent || '').trim()),
        box: {
          x: rect.left + rect.width / 2,
          y: rect.top + rect.height / 2,
          left: rect.left,
          top: rect.top,
          width: rect.width,
          height: rect.height,
        },
      };
    }, label).catch(() => null);
    debug.push({
      attempt,
      before_url: page.url(),
      facet_state: facetState,
    });
    if (facetState?.box) {
      await page.mouse.click(facetState.box.x, facetState.box.y).then(() => {
        clicked = true;
      }).catch(() => {
        clicked = false;
      });
    }
    const facet = page.locator('.search-facet:visible').filter({ hasText: label }).first();
    const fallbackFacet = page.locator('.search-facet:visible').first();
    const target = (await facet.count().catch(() => 0)) ? facet : fallbackFacet;
    if (!clicked && await target.count().catch(() => 0)) {
      await target.click({ force: true, timeout: 10000 }).then(() => {
        clicked = true;
      }).catch(() => {
        clicked = false;
      });
    }
    if (!clicked) {
      clicked = await page.evaluate((targetLabel) => {
        const buttons = Array.from(document.querySelectorAll('.search-facet')).filter((node) => {
          if (!(node instanceof HTMLElement)) return false;
          const rect = node.getBoundingClientRect();
          const enabled = !(node instanceof HTMLButtonElement) || !node.disabled;
          return rect.width > 0 && rect.height > 0 && enabled;
        });
        const targetNode = buttons.find((node) => String(node.textContent || '').includes(targetLabel)) || buttons[0];
        if (!(targetNode instanceof HTMLElement)) return false;
        if (targetNode instanceof HTMLButtonElement && targetNode.disabled) return false;
        targetNode.click();
        return true;
      }, label);
    }
    if (!clicked) {
      await page.waitForTimeout(500);
      continue;
    }
    const cleared = await page.waitForFunction((targetLabel) => {
      const buttons = Array.from(document.querySelectorAll('.search-facet'));
      return !new URL(window.location.href).searchParams.has('group_by')
        && !buttons.some((node) => String(node.textContent || '').includes(targetLabel));
    }, label, { timeout: 5000 }).then(() => true).catch(() => false);
    debug[debug.length - 1].after_url = page.url();
    debug[debug.length - 1].clicked = clicked;
    debug[debug.length - 1].cleared = cleared;
    if (cleared) break;
  }
  if (!clicked) return { cleared: false, clicked: false, debug };
  await page.waitForFunction((targetLabel) => {
    const buttons = Array.from(document.querySelectorAll('.search-facet'));
    return !buttons.some((node) => String(node.textContent || '').includes(targetLabel));
  }, label, { timeout: 15000 }).catch(() => {});
  await waitForListReady(page).catch(() => {});
  const cleared = await page.evaluate((targetLabel) => {
    const buttons = Array.from(document.querySelectorAll('.search-facet'));
    return !buttons.some((node) => String(node.textContent || '').includes(targetLabel));
  }, label);
  return { cleared, clicked, debug };
}

async function clickSortableColumn(page, columnName) {
  await page.locator(`section.table > table > thead th.cell-sortable[data-column="${columnName}"] .column-sort-btn`).first().click();
}

async function dragColumn(page, sourceColumn, targetColumn) {
  await page.evaluate(({ sourceColumn: source, targetColumn: target }) => {
    const escape = window.CSS && typeof window.CSS.escape === 'function'
      ? window.CSS.escape
      : (value) => String(value).replace(/"/g, '\\"');
    const sourceNode = document.querySelector(`section.table > table > thead th.cell-sortable[data-column="${escape(source)}"]`);
    const targetNode = document.querySelector(`section.table > table > thead th.cell-sortable[data-column="${escape(target)}"]`);
    if (!sourceNode || !targetNode) return false;
    const dataTransfer = new DataTransfer();
    sourceNode.dispatchEvent(new DragEvent('dragstart', { bubbles: true, cancelable: true, dataTransfer }));
    targetNode.dispatchEvent(new DragEvent('dragover', { bubbles: true, cancelable: true, dataTransfer }));
    targetNode.dispatchEvent(new DragEvent('drop', { bubbles: true, cancelable: true, dataTransfer }));
    sourceNode.dispatchEvent(new DragEvent('dragend', { bubbles: true, cancelable: true, dataTransfer }));
    return true;
  }, { sourceColumn, targetColumn });
}

async function selectFirstBusinessCellText(page) {
  return page.evaluate(() => {
    const row = document.querySelector('section.table > table > tbody > tr');
    const cells = row ? Array.from(row.querySelectorAll('td')) : [];
    const target = cells.find((cell) => String(cell.textContent || '').trim() && !cell.querySelector('input,button,select,textarea'));
    if (!target) return { selectedText: '', clicked: false };
    const textNode = Array.from(target.childNodes).find((node) => node.nodeType === Node.TEXT_NODE && String(node.textContent || '').trim())
      || target.firstChild;
    const range = document.createRange();
    range.selectNodeContents(textNode || target);
    const selection = window.getSelection();
    selection?.removeAllRanges();
    selection?.addRange(range);
    const beforeUrl = window.location.href;
    target.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
    return {
      selectedText: String(selection?.toString() || '').trim(),
      beforeUrl,
      afterUrl: window.location.href,
      clicked: true,
    };
  });
}

async function resizeColumn(page, columnName, delta) {
  const selector = `section.table > table > thead th.cell-sortable[data-column="${columnName}"] .column-resize-handle`;
  const handle = page.locator(selector).first();
  await handle.waitFor({ state: 'visible', timeout: 10000 });
  const box = await handle.boundingBox();
  if (!box) return false;
  const x = box.x + box.width / 2;
  const y = box.y + box.height / 2;
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.move(x + delta, y, { steps: 8 });
  await page.mouse.up();
  return true;
}

async function verifyStickyHeader(page) {
  return page.evaluate(() => {
    const headerRow = document.querySelector('section.table > table > thead');
    const header = document.querySelector('section.table > table > thead th');
    const rowNumber = document.querySelector('section.table > table > tbody > tr:first-child td.cell-row-number');
    const beforeTop = headerRow ? headerRow.getBoundingClientRect().top : null;
    const scrollers = Array.from(document.querySelectorAll('*')).filter((node) => {
      const style = window.getComputedStyle(node);
      return /(auto|scroll)/.test(`${style.overflowY} ${style.overflow}`) && node.scrollHeight > node.clientHeight + 20;
    });
    const tableTopBefore = document.querySelector('section.table')?.getBoundingClientRect().top ?? null;
    const targetScroller = scrollers.find((node) => {
      const rect = node.getBoundingClientRect();
      return rect.top <= (tableTopBefore || 0) && rect.bottom >= Math.min(window.innerHeight, (tableTopBefore || 0) + 80);
    }) || document.scrollingElement || document.documentElement;
    const beforeScrollTop = targetScroller.scrollTop;
    targetScroller.scrollTop = beforeScrollTop + 420;
    const afterTop = headerRow ? headerRow.getBoundingClientRect().top : null;
    const tableTopAfter = document.querySelector('section.table')?.getBoundingClientRect().top ?? null;
    const headerRowStyle = headerRow ? window.getComputedStyle(headerRow) : null;
    const headerStyle = header ? window.getComputedStyle(header) : null;
    const rowStyle = rowNumber ? window.getComputedStyle(rowNumber) : null;
    return {
      beforeTop,
      afterTop,
      tableTopBefore,
      tableTopAfter,
      scrollContainerTag: targetScroller === document.scrollingElement ? 'document' : String(targetScroller.className || targetScroller.tagName || ''),
      beforeScrollTop,
      afterScrollTop: targetScroller.scrollTop,
      headerRowPosition: headerRowStyle?.position || '',
      headerRowTop: headerRowStyle?.top || '',
      headerCellTop: header ? header.getBoundingClientRect().top : null,
      headerPosition: headerStyle?.position || '',
      headerTop: headerStyle?.top || '',
      rowNumberPosition: rowStyle?.position || '',
      rowNumberLeft: rowStyle?.left || '',
      rowNumberTextAlign: rowStyle?.textAlign || '',
    };
  });
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ locale: 'zh-CN', viewport: { width: 1440, height: 980 } });
  const page = await context.newPage();
  attachConsoleCapture(page);
  const summary = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    action_id: ACTION_ID,
    menu_id: MENU_ID,
    artifact_dir: outDir,
    checks: [],
  };

  try {
    await login(page);
    await openList(page);
    const initial = await snapshot(page);
    await page.screenshot({ path: path.join(outDir, '01_initial.png'), fullPage: true }).catch(() => {});

    await openSearchMenu(page);
    const menuOpen = await snapshot(page);
    summary.checks.push({
      path_id: 'LSG-P01',
      name: 'search dropdown exposes backend filter/group/favorite sections',
      status: menuOpen.dropdown_open
        && menuOpen.dropdown_sections.some((row) => /筛选/.test(row.title))
        && menuOpen.dropdown_sections.some((row) => /分组/.test(row.title))
        && menuOpen.dropdown_sections.some((row) => /收藏/.test(row.title))
        ? 'pass'
        : 'fail',
      initial,
      menu_open: menuOpen,
    });

    const searchInput = page.locator('.native-searchbox input[type="search"]').first();
    await searchInput.fill(SEARCH_TERM);
    await page.waitForTimeout(800);
    const afterSearchDraft = await snapshot(page);
    const searchSubmit = page.locator('.toolbar-search-submit').first();
    await searchSubmit.click();
    await page.waitForFunction((term) => {
      const url = new URL(window.location.href);
      const body = String(document.body?.textContent || '');
      return url.searchParams.get('search') === term && !body.includes('正在加载列表');
    }, SEARCH_TERM, { timeout: 20000 });
    await waitForListReady(page);
    const afterSearch = await snapshot(page);
    summary.checks.push({
      path_id: 'LSG-P02',
      name: 'search input waits for explicit confirmation before syncing route and reloading',
      status: afterSearchDraft.search_value === SEARCH_TERM
        && !new URL(afterSearchDraft.url).searchParams.has('search')
        && afterSearch.search_value === SEARCH_TERM
        && new URL(afterSearch.url).searchParams.get('search') === SEARCH_TERM
        && !afterSearch.visible_error
        ? 'pass'
        : 'fail',
      after_search_draft: afterSearchDraft,
      after_search: afterSearch,
    });

    const clearSearch = page.locator('.toolbar-search-clear').first();
    if (await clearSearch.count()) {
      await clearSearch.click();
      await page.waitForFunction(() => !new URL(window.location.href).searchParams.has('search'), null, { timeout: 10000 });
      await waitForListReady(page);
    }
    const afterClearSearch = await snapshot(page);
    summary.checks.push({
      path_id: 'LSG-P03',
      name: 'clear search removes route search and restores non-empty list',
      status: afterClearSearch.search_value === ''
        && !new URL(afterClearSearch.url).searchParams.has('search')
        && afterClearSearch.flat_row_count > 0
        && !afterClearSearch.visible_error
        ? 'pass'
        : 'fail',
      after_clear_search: afterClearSearch,
    });
    summary.checks.push({
      path_id: 'LSG-P00',
      name: 'flat list first column is page-local row number',
      status: afterClearSearch.flat_headers.includes('序号')
        && afterClearSearch.flat_first_row_cells[afterClearSearch.flat_headers.indexOf('序号')] === '1'
        && afterClearSearch.flat_row_count > 0
        ? 'pass'
        : 'fail',
      after_clear_search: afterClearSearch,
    });

    const sortColumn = (afterClearSearch.sortable_columns || []).find((row) => row.name === 'name')
      || (afterClearSearch.sortable_columns || [])[0];
    let afterHeaderSortAsc = null;
    let afterHeaderSortDesc = null;
    if (sortColumn) {
      await clickSortableColumn(page, sortColumn.name);
      await page.waitForFunction((columnName) => {
        const url = new URL(window.location.href);
        return String(url.searchParams.get('order') || '').startsWith(`${columnName} `);
      }, sortColumn.name, { timeout: 20000 });
      await waitForListReady(page);
      afterHeaderSortAsc = await snapshot(page);
      await clickSortableColumn(page, sortColumn.name);
      await page.waitForFunction(({ columnName, previousUrl }) => {
        const url = new URL(window.location.href);
        return window.location.href !== previousUrl && String(url.searchParams.get('order') || '').startsWith(`${columnName} `);
      }, { columnName: sortColumn.name, previousUrl: afterHeaderSortAsc.url }, { timeout: 20000 });
      await waitForListReady(page);
      afterHeaderSortDesc = await snapshot(page);
    }
    summary.checks.push({
      path_id: 'LSG-P13',
      name: 'clicking a list column header toggles backend order route and reloads without error',
      status: sortColumn
        && afterHeaderSortAsc
        && afterHeaderSortDesc
        && new URL(afterHeaderSortAsc.url).searchParams.get('order') === `${sortColumn.name} asc`
        && new URL(afterHeaderSortDesc.url).searchParams.get('order') === `${sortColumn.name} desc`
        && !afterHeaderSortDesc.visible_error
        ? 'pass'
        : 'fail',
      sort_column: sortColumn,
      after_sort_asc: afterHeaderSortAsc,
      after_sort_desc: afterHeaderSortDesc,
    });

    await openList(page);
    const beforeColumnDrag = await snapshot(page);
    const dragColumns = (beforeColumnDrag.sortable_columns || []).filter((row) => row.name);
    let afterColumnDrag = null;
    if (dragColumns.length >= 2) {
      await dragColumn(page, dragColumns[0].name, dragColumns[1].name);
      await page.waitForTimeout(800);
      afterColumnDrag = await snapshot(page);
    }
    summary.checks.push({
      path_id: 'LSG-P14',
      name: 'dragging list columns changes visible column order and keeps row-number column fixed',
      status: dragColumns.length >= 2
        && afterColumnDrag
        && afterColumnDrag.flat_headers.includes('序号')
        && afterColumnDrag.sortable_columns[0]?.name === dragColumns[1].name
        && afterColumnDrag.sortable_columns[1]?.name === dragColumns[0].name
        && !afterColumnDrag.visible_error
        ? 'pass'
        : 'fail',
      before_drag: beforeColumnDrag,
      after_drag: afterColumnDrag,
    });

    await openList(page);
    const footerSnapshot = await snapshot(page);
    summary.checks.push({
      path_id: 'LSG-P15',
      name: 'list table footer aligns current-page and grand-total summaries under data columns',
      status: footerSnapshot.footer_text.includes('当前页合计')
        && footerSnapshot.footer_text.includes('总计')
        && footerSnapshot.footer_rows.length >= 2
        && footerSnapshot.footer_rows.every((row) => row.length === footerSnapshot.flat_headers.length)
        && !footerSnapshot.visible_error
        ? 'pass'
        : 'fail',
      footer_snapshot: footerSnapshot,
    });

    await openList(page);
    const beforeTextSelection = await snapshot(page);
    const selectionResult = await selectFirstBusinessCellText(page);
    await page.waitForTimeout(300);
    const afterTextSelection = await snapshot(page);
    summary.checks.push({
      path_id: 'LSG-P16',
      name: 'selecting text in list cells does not trigger row navigation',
      status: selectionResult.clicked
        && Boolean(selectionResult.selectedText)
        && selectionResult.beforeUrl === selectionResult.afterUrl
        && afterTextSelection.url === beforeTextSelection.url
        && !afterTextSelection.visible_error
        ? 'pass'
        : 'fail',
      before_selection: beforeTextSelection,
      selection_result: selectionResult,
      after_selection: afterTextSelection,
    });

    await openList(page);
    const beforeResize = await snapshot(page);
    const resizeColumnSpec = (beforeResize.sortable_columns || [])[0];
    let resizePerformed = false;
    let afterResize = null;
    if (resizeColumnSpec) {
      resizePerformed = await resizeColumn(page, resizeColumnSpec.name, 80);
      await page.waitForTimeout(900);
      afterResize = await snapshot(page);
    }
    summary.checks.push({
      path_id: 'LSG-P17',
      name: 'dragging a column resize handle changes the visible column width',
      status: resizeColumnSpec
        && resizePerformed
        && afterResize
        && (afterResize.sortable_columns || []).some((row) => row.name === resizeColumnSpec.name && row.width >= resizeColumnSpec.width + 40)
        && !afterResize.visible_error
        ? 'pass'
        : 'fail',
      resize_column: resizeColumnSpec,
      before_resize: beforeResize,
      after_resize: afterResize,
    });

    await openList(page);
    const beforeSticky = await snapshot(page);
    const stickyResult = await verifyStickyHeader(page);
    const afterSticky = await snapshot(page);
    summary.checks.push({
      path_id: 'LSG-P18',
      name: 'table header stays sticky while row-number column remains fixed left and centered',
      status: beforeSticky.flat_row_count > 0
        && stickyResult.afterScrollTop > stickyResult.beforeScrollTop
        && stickyResult.headerRowPosition === 'sticky'
        && stickyResult.headerRowTop === '0px'
        && stickyResult.headerPosition === 'sticky'
        && stickyResult.headerTop === '0px'
        && stickyResult.afterTop !== null
        && stickyResult.afterTop >= 0
        && stickyResult.afterTop <= Math.max(2, stickyResult.beforeTop)
        && stickyResult.rowNumberPosition === 'sticky'
        && Number.parseFloat(stickyResult.rowNumberLeft || '0') >= 0
        && stickyResult.rowNumberTextAlign === 'center'
        && !afterSticky.visible_error
        ? 'pass'
        : 'fail',
      before_sticky: beforeSticky,
      sticky_result: stickyResult,
      after_sticky: afterSticky,
    });

    await openList(page);
    const plainSearchInput = page
      .locator('.list-plain-search input[type="search"], .native-searchbox input[type="search"]')
      .first();
    await plainSearchInput.fill(SEARCH_TERM);
    await plainSearchInput.press('Enter');
    await page.waitForFunction((term) => {
      const url = new URL(window.location.href);
      const body = String(document.body?.textContent || '');
      return url.searchParams.get('search') === term && !body.includes('正在加载列表');
    }, SEARCH_TERM, { timeout: 20000 });
    await waitForListReady(page);
    const afterPlainSearch = await snapshot(page);
    summary.checks.push({
      path_id: 'LSG-P19',
      name: 'list search accepts user input without changing existing search menu/group controls',
      status: (afterPlainSearch.plain_search_value === SEARCH_TERM || afterPlainSearch.search_value === SEARCH_TERM)
        && new URL(afterPlainSearch.url).searchParams.get('search') === SEARCH_TERM
        && afterPlainSearch.search_menu_enabled
        && !afterPlainSearch.visible_error
        ? 'pass'
        : 'fail',
      after_plain_search: afterPlainSearch,
    });

    await openList(page);
    const beforePageSize = await snapshot(page);
    const pageSizeInput = page.locator('.pagination-input--size').first();
    await pageSizeInput.fill('5');
    await pageSizeInput.press('Enter');
    await page.waitForFunction(() => {
      const body = String(document.body?.textContent || '');
      return !body.includes('正在加载列表') && document.querySelectorAll('section.table > table > tbody > tr').length <= 5;
    }, null, { timeout: 20000 });
    await waitForListReady(page);
    const afterPageSize = await snapshot(page);
    summary.checks.push({
      path_id: 'LSG-P20',
      name: 'pagination accepts user-entered page size and reloads current page',
      status: beforePageSize.flat_row_count > 0
        && afterPageSize.page_size_inputs.includes('5')
        && afterPageSize.flat_row_count > 0
        && afterPageSize.flat_row_count <= Math.min(5, beforePageSize.flat_row_count)
        && !afterPageSize.visible_error
        ? 'pass'
        : 'fail',
      before_page_size: beforePageSize,
      after_page_size: afterPageSize,
    });

    const groupLabel = await applyFirstGroup(page);
    const afterGroup = await snapshot(page);
    const groupedNumbers = afterGroup.grouped_row_numbers.map((value) => Number(value));
    const groupedContinuous = groupedNumbers.length > 0
      && groupedNumbers.every((value, index) => value === index + 1);
    summary.checks.push({
      path_id: 'LSG-P04',
      name: 'group selection shows grouped result and syncs group_by route',
      status: Boolean(groupLabel)
        && Boolean(new URL(afterGroup.url).searchParams.get('group_by'))
        && afterGroup.grouped_table_count === 1
        && afterGroup.group_block_count > 0
        && afterGroup.grouped_headers[0] === '序号'
        && groupedContinuous
        && !afterGroup.visible_error
        ? 'pass'
        : 'fail',
      group_label: groupLabel,
      after_group: afterGroup,
    });

    summary.checks.push({
      path_id: 'LSG-P05',
      name: 'grouped view does not render a duplicate flat table under grouped results',
      status: afterGroup.grouped_table_count === 1 && afterGroup.flat_table_count === 0 ? 'pass' : 'fail',
      after_group: afterGroup,
    });

    const groupClearResult = await clearFacetByLabel(page, groupLabel);
    const clickedGroupFacet = Boolean(groupClearResult.clicked);
    if (groupClearResult.cleared) {
      await page.waitForFunction(() => !new URL(window.location.href).searchParams.has('group_by'), null, { timeout: 10000 }).catch(() => {});
      await waitForListReady(page).catch(() => {});
    }
    const afterClearGroup = await snapshot(page);
    if (afterClearGroup.grouped_table_count > 0) {
      await page.screenshot({ path: path.join(outDir, '02_after_group_clear_failure.png'), fullPage: true }).catch(() => {});
    }
    summary.checks.push({
      path_id: 'LSG-P06',
      name: 'clear group removes grouped route state and restores flat table',
      status: !new URL(afterClearGroup.url).searchParams.has('group_by')
        && afterClearGroup.grouped_table_count === 0
        && afterClearGroup.flat_table_count === 1
        && afterClearGroup.flat_row_count > 0
        ? 'pass'
        : 'fail',
      after_clear_group: afterClearGroup,
      clicked_group_facet: clickedGroupFacet,
      clear_debug: groupClearResult.debug,
    });

    await openList(page);
    await openCustomFilterPanel(page);
    const customFilterOpen = await snapshot(page);
    const cancelButton = page.locator('.custom-search-panel button').filter({ hasText: /^取消$/ }).first();
    await cancelButton.click();
    await page.waitForFunction(() => document.querySelectorAll('.custom-search-panel').length === 0, null, { timeout: 10000 });
    const afterCustomFilterCancel = await snapshot(page);
    summary.checks.push({
      path_id: 'LSG-P07',
      name: 'custom filter panel can be opened and cancelled without mutating route',
      status: customFilterOpen.dropdown_open
        && customFilterOpen.dropdown_sections.some((row) => row.title.includes('筛选'))
        && afterCustomFilterCancel.url === customFilterOpen.url
        && !afterCustomFilterCancel.visible_error
        ? 'pass'
        : 'fail',
      custom_filter_open: customFilterOpen,
      after_cancel: afterCustomFilterCancel,
    });

    await openCustomFilterPanel(page);
    const customFilterSpec = await selectUsableCustomFilter(page);
    if (customFilterSpec) {
      const addButton = page.locator('.custom-search-panel button').filter({ hasText: /^添加$/ }).first();
      await addButton.click();
      await waitForListReady(page);
      await page.waitForFunction(() => {
        const body = String(document.body?.textContent || '');
        return !body.includes('正在加载列表');
      }, null, { timeout: 20000 });
    }
    const afterCustomFilterApply = await snapshot(page);
    summary.checks.push({
      path_id: 'LSG-P08',
      name: 'custom filter apply creates visible facet and reloads list without error',
      status: Boolean(customFilterSpec)
        && afterCustomFilterApply.facet_texts.some((text) => text.includes(customFilterSpec.label) || text.includes('自定义'))
        && !afterCustomFilterApply.visible_error
        ? 'pass'
        : 'fail',
      custom_filter_spec: customFilterSpec,
      after_apply: afterCustomFilterApply,
    });

    await openList(page);
    const recoveryInitial = await snapshot(page);
    const recoveryGroupLabel = await applyFirstGroup(page);
    const recoveryGrouped = await snapshot(page);
    await page.reload({ waitUntil: 'domcontentloaded', timeout: 45000 });
    await waitForListReady(page);
    await page.waitForFunction(() => document.querySelectorAll('.grouped-table .group-block').length > 0, null, { timeout: 20000 });
    const afterGroupReload = await snapshot(page);
    await page.goBack({ waitUntil: 'domcontentloaded', timeout: 45000 }).catch(() => null);
    await waitForListReady(page).catch(() => {});
    const afterBack = await snapshot(page);
    summary.checks.push({
      path_id: 'LSG-P09',
      name: 'grouped list survives browser reload and back navigation stays recoverable',
      status: Boolean(recoveryGroupLabel)
        && recoveryGrouped.grouped_table_count === 1
        && afterGroupReload.grouped_table_count === 1
        && afterGroupReload.group_block_count > 0
        && !afterBack.visible_error
        && !afterBack.text_sample.includes('页面加载失败')
        ? 'pass'
        : 'fail',
      recovery_initial: recoveryInitial,
      group_label: recoveryGroupLabel,
      recovery_grouped: recoveryGrouped,
      after_group_reload: afterGroupReload,
      after_back: afterBack,
    });

    await openList(page);
    const customGroupOption = await applyFirstCustomGroup(page);
    const afterCustomGroup = await snapshot(page);
    const customGroupFacetLabel = customGroupOption?.text
      || customGroupOption?.value
      || afterCustomGroup.facet_texts[0]
      || '';
    const customGroupClearResult = customGroupOption
      ? await clearFacetByLabel(page, customGroupFacetLabel)
      : { cleared: false, clicked: false, debug: [] };
    const customGroupCleared = Boolean(customGroupClearResult.cleared);
    const afterClearCustomGroup = await snapshot(page);
    if (afterClearCustomGroup.grouped_table_count > 0) {
      await page.screenshot({ path: path.join(outDir, '03_after_custom_group_clear_failure.png'), fullPage: true }).catch(() => {});
    }
    summary.checks.push({
      path_id: 'LSG-P10',
      name: 'custom group selector applies grouped view and can be cleared',
      status: Boolean(customGroupOption)
        && Boolean(new URL(afterCustomGroup.url).searchParams.get('group_by'))
        && afterCustomGroup.grouped_table_count === 1
        && afterCustomGroup.group_block_count > 0
        && customGroupCleared
        && !new URL(afterClearCustomGroup.url).searchParams.has('group_by')
        && afterClearCustomGroup.flat_table_count === 1
        && !afterClearCustomGroup.visible_error
        ? 'pass'
        : 'fail',
      custom_group_option: customGroupOption,
      custom_group_facet_label: customGroupFacetLabel,
      after_custom_group: afterCustomGroup,
      after_clear_custom_group: afterClearCustomGroup,
      custom_group_cleared: customGroupCleared,
      clear_debug: customGroupClearResult.debug,
    });

    await openList(page);
    const pagingGroupLabel = await applyFirstGroup(page);
    const beforeGroupPage = await snapshot(page);
    const pageCandidate = (beforeGroupPage.group_pages || []).find((row) => row.next_disabled === false);
    let afterGroupPageNext = null;
    let afterGroupPagePrev = null;
    let groupPageNextClicked = false;
    let groupPagePrevClicked = false;
    if (pageCandidate) {
      const block = page.locator('.grouped-table .group-block').nth(pageCandidate.index);
      await block.locator('.group-page-btn').nth(1).click();
      groupPageNextClicked = true;
      await page.waitForFunction(({ index, previousPageText }) => {
        const url = new URL(window.location.href);
        const blocks = Array.from(document.querySelectorAll('.grouped-table .group-block'));
        const target = blocks[index];
        const pageText = String(target?.querySelector('.group-page')?.textContent || '').replace(/\s+/g, ' ').trim();
        return url.searchParams.has('group_page') && pageText && pageText !== previousPageText;
      }, { index: pageCandidate.index, previousPageText: pageCandidate.page_text }, { timeout: 20000 }).catch(() => {});
      await waitForListReady(page).catch(() => {});
      afterGroupPageNext = await snapshot(page);
      const nextPage = (afterGroupPageNext.group_pages || [])[pageCandidate.index];
      if (nextPage && nextPage.prev_disabled === false) {
        await block.locator('.group-page-btn').nth(0).click();
        groupPagePrevClicked = true;
        await page.waitForFunction((nextUrl) => window.location.href !== nextUrl, afterGroupPageNext.url, { timeout: 20000 }).catch(() => {});
        await waitForListReady(page).catch(() => {});
        afterGroupPagePrev = await snapshot(page);
      }
    }
    summary.checks.push({
      path_id: 'LSG-P11',
      name: 'grouped result supports per-group pagination with route state',
      status: Boolean(pagingGroupLabel)
        && Boolean(pageCandidate)
        && afterGroupPageNext
        && new URL(afterGroupPageNext.url).searchParams.has('group_page')
        && afterGroupPageNext.grouped_table_count === 1
        && afterGroupPageNext.group_block_count > 0
        && afterGroupPageNext.group_pages.some((row) => row.index === pageCandidate.index && row.page_text !== pageCandidate.page_text && row.prev_disabled === false)
        && afterGroupPagePrev
        && afterGroupPagePrev.grouped_table_count === 1
        && !afterGroupPagePrev.visible_error
        ? 'pass'
        : 'fail',
      group_label: pagingGroupLabel,
      page_candidate: pageCandidate,
      before_group_page: beforeGroupPage,
      after_next: afterGroupPageNext,
      after_prev: afterGroupPagePrev,
      group_page_next_clicked: groupPageNextClicked,
      group_page_prev_clicked: groupPagePrevClicked,
    });

    await openList(page, `search=${encodeURIComponent(SEARCH_TERM)}`);
    const favoriteSaveResult = await saveCurrentSearchAsFavorite(page, FAVORITE_NAME);
    const afterFavoriteSave = await snapshot(page);
    summary.checks.push({
      path_id: 'LSG-P12',
      name: 'saving current search creates a usable visible favorite filter',
      status: favoriteSaveResult.attempted
        && favoriteSaveResult.saved_visible
        && afterFavoriteSave.dropdown_open
        && afterFavoriteSave.dropdown_sections.some((section) => /收藏/.test(section.title) && section.items.some((item) => item.includes(FAVORITE_NAME)))
        && !afterFavoriteSave.visible_error
        ? 'pass'
        : 'fail',
      favorite_name: FAVORITE_NAME,
      favorite_save_result: favoriteSaveResult,
      cleanup_hint: `ENV=prod-sim DB_NAME=${DB_NAME} make odoo.shell.exec # unlink ir.filters name=${FAVORITE_NAME}`,
      after_favorite_save: afterFavoriteSave,
    });

    summary.console_errors = page.__consoleErrors || [];
  } finally {
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }

  summary.pass = summary.checks.every((row) => row.status === 'pass') && (summary.console_errors || []).length === 0;
  writeJson('summary.json', summary);
  console.log(`[list_search_group_usability_audit] artifacts=${outDir}`);
  console.log(JSON.stringify({
    pass: summary.pass,
    checks: summary.checks.map((row) => ({ path_id: row.path_id, name: row.name, status: row.status })),
    console_errors: (summary.console_errors || []).length,
  }, null, 2));
  if (!summary.pass) process.exit(1);
}

main().catch((err) => {
  const summary = {
    pass: false,
    error: err instanceof Error ? err.message : String(err),
    error_stack: err instanceof Error ? err.stack : '',
    artifact_dir: outDir,
  };
  writeJson('summary.json', summary);
  console.error(JSON.stringify(summary, null, 2));
  process.exit(1);
});
