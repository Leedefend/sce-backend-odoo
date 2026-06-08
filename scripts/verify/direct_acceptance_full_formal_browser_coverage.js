const { chromium } = require('playwright');
const fs = require('fs');

const base = process.env.BASE_URL || 'http://1.95.85.92:18081';
const db = process.env.DB || 'sc_demo';
const login = process.env.LOGIN || 'wutao';
const password = process.env.PASSWORD || '123456';
const outPath = process.env.OUT || '/tmp/direct_acceptance_full_formal_browser_coverage.json';

const pairs = [
  { name: '材料计划', formal: { actionId: 525, menuId: 403, model: 'project.material.plan' }, acceptance: { actionId: 915, menuId: 749, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '报价单', formal: { actionId: 968, menuId: 778, model: 'sc.material.rfq' }, acceptance: { actionId: 916, menuId: 750, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '入库', formal: { actionId: 529, menuId: 496, model: 'sc.material.inbound' }, acceptance: { actionId: 917, menuId: 751, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '方单', formal: { actionId: 963, menuId: 779, model: 'sc.labor.usage' }, acceptance: { actionId: 919, menuId: 754, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '零星用工', formal: { actionId: 964, menuId: 780, model: 'sc.labor.usage' }, acceptance: { actionId: 920, menuId: 755, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '分包方单', formal: { actionId: 969, menuId: 785, model: 'sc.subcontract.request' }, acceptance: { actionId: 922, menuId: 757, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '机械台班记录', formal: { actionId: 970, menuId: 782, model: 'sc.equipment.usage' }, acceptance: { actionId: 924, menuId: 759, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '租入', formal: { actionId: 903, menuId: 783, model: 'sc.material.rental.order' }, acceptance: { actionId: 935, menuId: 761, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '还租', formal: { actionId: 904, menuId: 784, model: 'sc.material.rental.order' }, acceptance: { actionId: 936, menuId: 762, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '管理人员工资表', formal: { actionId: 647, menuId: 355, model: 'sc.hr.payroll.document' }, acceptance: { actionId: 928, menuId: 765, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '油卡登记', formal: { actionId: 906, menuId: 787, model: 'sc.legacy.fuel.card.fact' }, acceptance: { actionId: 937, menuId: 766, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '充值登记', formal: { actionId: 907, menuId: 788, model: 'sc.legacy.fuel.card.recharge.fact' }, acceptance: { actionId: 938, menuId: 767, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '加油登记', formal: { actionId: 908, menuId: 789, model: 'sc.legacy.fuel.card.refuel.fact' }, acceptance: { actionId: 939, menuId: 768, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '施工日志（新）', formal: { actionId: 701, menuId: 415, model: 'sc.construction.diary' }, acceptance: { actionId: 934, menuId: 776, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '施工合同', formal: { actionId: 971, menuId: 777, model: 'construction.contract.income' }, acceptance: { actionId: 909, menuId: 743, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '项目费用报销单', formal: { actionId: 773, menuId: 569, model: 'sc.expense.claim' }, acceptance: { actionId: 927, menuId: 764, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '支付申请', formal: { actionId: 780, menuId: 786, model: 'payment.request' }, acceptance: { actionId: 929, menuId: 769, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '工程进度收款', formal: { actionId: 949, menuId: 803, model: 'sc.receipt.income' }, acceptance: { actionId: 940, menuId: 770, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '往来单位付款', formal: { actionId: 781, menuId: 551, model: 'sc.payment.execution' }, acceptance: { actionId: 930, menuId: 771, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '进项上报', formal: { actionId: 760, menuId: 531, model: 'sc.invoice.registration' }, acceptance: { actionId: 932, menuId: 773, model: 'sc.legacy.direct.acceptance.fact' } },
  { name: '总包进项上报', formal: { actionId: 758, menuId: 529, model: 'sc.invoice.registration' }, acceptance: { actionId: 933, menuId: 774, model: 'sc.legacy.direct.acceptance.fact' } },
];

const aggregateTargets = [
  { name: '支出合同执行', actionId: 752, menuId: 490, model: 'construction.contract.expense', expectedTotal: 1566 },
  { name: '收入合同结算', actionId: 753, menuId: 486, model: 'sc.settlement.order', expectedTotal: 37 },
  { name: '支出合同结算', actionId: 754, menuId: 491, model: 'sc.settlement.order', expectedTotal: 3225 },
];

function unwrap(body) {
  return body && body.data && typeof body.data === 'object' ? body.data : body;
}

function records(data) {
  return Array.isArray(data?.records) ? data.records : (Array.isArray(data?.rows) ? data.rows : []);
}

function total(data) {
  return Number(data?.total ?? data?.total_count ?? data?.count ?? records(data).length);
}

function norm(value) {
  if (Array.isArray(value)) return value.map(norm).join(' / ').replace(/\s+/g, ' ').trim();
  if (value && typeof value === 'object') return JSON.stringify(value, Object.keys(value).sort());
  return String(value ?? '').replace(/\s+/g, ' ').trim();
}

function extractColumns(contract) {
  const data = unwrap(contract.body || contract);
  const tree = data?.views?.tree || data?.ui_contract?.views?.tree || data?.source?.views?.tree;
  let cols = [];
  if (Array.isArray(tree?.columns_schema)) {
    cols = tree.columns_schema.map((c) => ({ field: String(c.name || ''), label: String(c.label || c.string || c.name || '') }));
  } else if (Array.isArray(tree?.columns)) {
    cols = tree.columns.map((c) => typeof c === 'string' ? { field: c, label: c } : { field: String(c.name || ''), label: String(c.label || c.string || c.name || '') });
  }
  return cols.filter((c) => c.field && c.field !== 'id');
}

function fingerprint(row, cols) {
  return cols.map((c) => norm(row?.[c.field])).join('|');
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, locale: 'zh-CN' });
  await page.goto(`${base}/login?db=${db}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.locator('input').nth(0).fill(login);
  await page.locator('input[type="password"]').fill(password);
  const dbInput = page.locator('input').nth(2);
  if (await dbInput.isEnabled().catch(() => false)) await dbInput.fill(db);
  await page.locator('button[type="submit"]').click();
  await page.waitForTimeout(2000);
  const token = await page.evaluate(() => sessionStorage.getItem(Object.keys(sessionStorage).find((k) => k.startsWith('sc_auth_token')) || '') || '');
  if (!token) throw new Error('login failed');

  async function intent(intentName, params) {
    return await page.evaluate(async ({ intentName, params, token, db }) => {
      const res = await fetch(`/api/v1/intent?db=${encodeURIComponent(db)}&_t=${Date.now()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Odoo-DB': db, Authorization: `Bearer ${token}` },
        body: JSON.stringify({ intent: intentName, params, meta: { startup_chain_bypass: true, force_refresh: true } }),
      });
      const body = await res.json();
      return { status: res.status, ok: res.ok && body.ok !== false, body };
    }, { intentName, params, token, db });
  }

  async function probe(side) {
    const contract = await intent('load_contract', { model: side.model, view_type: 'tree', action_id: side.actionId, menu_id: side.menuId });
    const cols = extractColumns(contract);
    const data = unwrap(contract.body);
    const head = data?.head || data?.ui_contract?.head || {};
    const list = await intent('api.data', {
      op: 'list',
      model: side.model,
      fields: ['id', ...cols.map((c) => c.field)],
      domain: head.domain || [],
      domain_raw: head.domain_raw || '',
      context: { ...(head.context || {}), action_id: side.actionId, menu_id: side.menuId },
      limit: 50,
      offset: 0,
      need_total: true,
      order: data?.views?.tree?.order || '',
    });
    const listData = unwrap(list.body);
    return {
      contractOk: contract.ok,
      listOk: list.ok,
      status: { contract: contract.status, list: list.status },
      cols,
      labels: cols.map((c) => c.label),
      total: total(listData),
      rows: records(listData).slice(0, 50),
      domain: head.domain_raw || head.domain || '',
      error: contract.body?.error || list.body?.error || null,
    };
  }

  const pairResults = [];
  for (const pair of pairs) {
    console.log(`PAIR ${pair.name}`);
    const formal = await probe(pair.formal);
    const acceptance = await probe(pair.acceptance);
    const commonLabels = acceptance.labels.filter((label) => formal.labels.includes(label));
    const fCols = commonLabels.map((label) => formal.cols[formal.labels.indexOf(label)]);
    const aCols = commonLabels.map((label) => acceptance.cols[acceptance.labels.indexOf(label)]);
    const formalWindow = formal.rows.map((row) => fingerprint(row, fCols)).sort();
    const acceptanceWindow = acceptance.rows.map((row) => fingerprint(row, aCols)).sort();
    const missingRows = acceptanceWindow.filter((fp) => !formalWindow.includes(fp)).slice(0, 10);
    const extraRows = formalWindow.filter((fp) => !acceptanceWindow.includes(fp)).slice(0, 10);
    const labelOrderSame = JSON.stringify(formal.labels) === JSON.stringify(acceptance.labels);
    const countSame = formal.total === acceptance.total;
    const rowWindowSame = missingRows.length === 0 && extraRows.length === 0;
    pairResults.push({
      name: pair.name,
      ok: formal.contractOk && formal.listOk && acceptance.contractOk && acceptance.listOk && labelOrderSame && countSame && rowWindowSame,
      formal: { ...pair.formal, total: formal.total, labels: formal.labels, domain: formal.domain, first: formal.rows[0] || null, error: formal.error },
      acceptance: { ...pair.acceptance, total: acceptance.total, labels: acceptance.labels, domain: acceptance.domain, first: acceptance.rows[0] || null, error: acceptance.error },
      diffs: {
        labelOrderSame,
        missingLabels: acceptance.labels.filter((label) => !formal.labels.includes(label)),
        extraLabels: formal.labels.filter((label) => !acceptance.labels.includes(label)),
        countSame,
        rowWindowSame,
        missingRows,
        extraRows,
      },
    });
  }

  const aggregateResults = [];
  for (const target of aggregateTargets) {
    console.log(`AGG ${target.name}`);
    const actual = await probe(target);
    aggregateResults.push({
      ...target,
      ok: actual.contractOk && actual.listOk && actual.total === target.expectedTotal,
      total: actual.total,
      labels: actual.labels,
      domain: actual.domain,
      first: actual.rows[0] || null,
      error: actual.error,
    });
  }

  const all = [...pairResults, ...aggregateResults];
  const summary = {
    total: all.length,
    ok: all.filter((r) => r.ok).length,
    failed: all.filter((r) => !r.ok).length,
    failedNames: all.filter((r) => !r.ok).map((r) => r.name),
    pairTotal: pairResults.length,
    aggregateTotal: aggregateResults.length,
  };
  fs.writeFileSync(outPath, JSON.stringify({ summary, pairResults, aggregateResults }, null, 2));
  console.log(JSON.stringify({
    summary,
    failures: all.filter((r) => !r.ok).map((r) => ({
      name: r.name,
      formalTotal: r.formal?.total ?? r.total,
      acceptanceTotal: r.acceptance?.total,
      expectedTotal: r.expectedTotal,
      diffs: r.diffs,
      formalLabels: r.formal?.labels ?? r.labels,
      acceptanceLabels: r.acceptance?.labels,
      error: r.error || r.formal?.error || r.acceptance?.error,
    })),
    outPath,
  }, null, 2));
  await browser.close();
})();
