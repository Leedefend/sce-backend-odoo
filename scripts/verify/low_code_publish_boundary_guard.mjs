#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import ts from '../../frontend/apps/web/node_modules/typescript/lib/typescript.js';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const webRoot = path.join(root, 'frontend/apps/web/src');
const scanRoots = [
  path.join(webRoot, 'views/BusinessConfigSurfaceView.vue'),
  path.join(webRoot, 'views/MenuConfigView.vue'),
  path.join(webRoot, 'views/businessConfigSurface'),
  path.join(webRoot, 'views/menuConfig'),
  path.join(webRoot, 'pages/contractForm/useFormConfigSaveRuntime.ts'),
];
const unifiedPublisher = 'views/businessConfigSurface/useBusinessConfigDraftSession.ts';
const allowedPublishLiteral = new Set([
  'views/businessConfigSurface/useBusinessConfigRemediationLifecycle.ts',
]);

function filesAt(target) {
  if (!fs.existsSync(target)) return [];
  const stat = fs.statSync(target);
  if (stat.isFile()) return [target];
  return fs.readdirSync(target, { withFileTypes: true }).flatMap((entry) => filesAt(path.join(target, entry.name)));
}
function scriptText(file) {
  const raw = fs.readFileSync(file, 'utf8');
  if (!file.endsWith('.vue')) return raw;
  return [...raw.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)].map((match) => match[1]).join('\n');
}
function analyzeSource(source, fileName) {
  const ast = ts.createSourceFile(fileName, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const errors = [];
  let nodeCount = 0;
  let importCount = 0;
  const facts = {
    changedStageConditions: 0,
    lengthStageConditions: 0,
    publishValidationThrows: false,
    publishResultChecks: new Set(),
  };
  function walk(node, functionName = '') {
    nodeCount += 1;
    let activeFunction = functionName;
    if (ts.isFunctionDeclaration(node) && node.name) activeFunction = node.name.text;
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.initializer
      && (ts.isArrowFunction(node.initializer) || ts.isFunctionExpression(node.initializer))) activeFunction = node.name.text;
    if (ts.isImportDeclaration(node)) {
      importCount += 1;
      const names = node.importClause?.namedBindings && ts.isNamedImports(node.importClause.namedBindings)
        ? node.importClause.namedBindings.elements.map((item) => item.name.text) : [];
      if (names.includes('publishBusinessConfigChangeSet') && fileName !== unifiedPublisher) {
        errors.push(`${fileName}: only unified draft session may import publishBusinessConfigChangeSet`);
      }
    }
    if (ts.isPropertyAssignment(node) && node.name.getText(ast) === 'publish' && node.initializer.kind === ts.SyntaxKind.TrueKeyword
      && !allowedPublishLiteral.has(fileName)) {
      errors.push(`${fileName}: formal editor contains direct publish:true`);
    }
    if (activeFunction.toLowerCase().includes('preview') && ts.isCallExpression(node)) {
      const callee = node.expression.getText(ast).toLowerCase();
      if (callee.includes('publish')) errors.push(`${fileName}:${activeFunction} preview path calls ${callee}`);
    }
    if (ts.isIfStatement(node)) {
      const condition = node.expression.getText(ast);
      const body = node.thenStatement.getText(ast);
      if (body.includes('stageUnifiedDraftItem')) {
        if (condition.includes('.length')) facts.lengthStageConditions += 1;
        if (/\b(?:list|search|pivot|graph)Changed\b/.test(condition)) facts.changedStageConditions += 1;
      }
      if (activeFunction === 'publishDraft' && /validated\.state\s*!==\s*['"]ready['"]/.test(condition)) {
        facts.publishValidationThrows = body.includes('throw ');
      }
    }
    if (activeFunction === 'publishDraft' && ts.isBinaryExpression(node)) {
      const expression = node.getText(ast);
      if (/\.state\s*!==\s*['"]published['"]/.test(expression)) facts.publishResultChecks.add('state');
      if (/publishResult\.ok\s*!==\s*true/.test(expression)) facts.publishResultChecks.add('ok');
      if (/publishResult\.runtime_verified\s*!==\s*true/.test(expression)) facts.publishResultChecks.add('runtime_verified');
    }
    ts.forEachChild(node, (child) => walk(child, activeFunction));
  }
  walk(ast);
  if (facts.lengthStageConditions) errors.push(`${fileName}: changed-but-empty draft staging depends on array length`);
  return { errors, nodeCount, importCount, facts: { ...facts, publishResultChecks: [...facts.publishResultChecks] } };
}

function loadPublishLifecycle() {
  const source = fs.readFileSync(path.join(webRoot, 'views/businessConfigSurface/useBusinessConfigPublishLifecycle.ts'), 'utf8');
  const output = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const loaded = { exports: {} };
  Function('module', 'exports', output)(loaded, loaded.exports);
  return loaded.exports.useBusinessConfigPublishLifecycle;
}

async function explicitEmptyRoundtripBehavior() {
  const errors = [];
  const messages = [];
  let writeCalls = 0;
  const ref = (value) => ({ value });
  const namesToText = (names) => (Array.isArray(names) ? names : []).join('\n');
  const normalizeNamesText = (value) => String(value || '').split(/[\n,，]+/).map((item) => item.trim()).filter(Boolean).join('\n');
  const refs = {
    currentModel: ref('res.partner'), listSearchBusy: ref(false), error: ref(''), scopeAction: ref(11), scopeView: ref(22), scopeRole: ref('config_admin'),
    listSearchAudit: ref(null), listColumnsText: ref(''), searchFiltersText: ref(''), searchGroupByText: ref(''),
    listSearchBase: ref({ list: '', filter: '', group: '' }), activeListSearchEditor: ref('list'), requestedListSearchTab: ref('list'),
    analysisPanelOpen: ref(false), approvalPanelOpen: ref(false), listSearchPanelOpen: ref(false),
    analysisAudit: ref(null), pivotMeasuresText: ref(''), pivotDimensionsText: ref(''), graphMeasuresText: ref(''), graphDimensionsText: ref(''),
    graphType: ref('bar'), analysisBase: ref({ pivotMeasures: '', pivotDimensions: '', graphMeasures: '', graphDimensions: '', graphType: 'bar' }),
    activeAnalysisEditor: ref('pivotMeasure'), requestedAnalysisTab: ref('pivotMeasure'), listSearchSaving: ref(false),
  };
  const explicitListSearch = {
    has_business_list_config: true, has_business_search_config: true,
    business_config_list_columns: [], business_config_search_filters: [], business_config_search_group_by: [],
    suggested_list_columns: ['name'], suggested_search_filters: ['state'], suggested_search_group_by: ['company_id'],
  };
  const explicitAnalysis = {
    has_business_analysis_config: true, has_business_pivot_config: true, has_business_graph_config: true,
    pivot_measures: [], pivot_dimensions: [], graph_measures: [], graph_dimensions: [], graph_type: 'bar',
    suggested_pivot_measures: ['amount_total'], suggested_pivot_dimensions: ['company_id'],
    suggested_graph_measures: ['amount_total'], suggested_graph_dimensions: ['state'], suggested_graph_type: 'line',
  };
  const deps = {
    ...refs, namesToText, normalizeNamesText, clearMessage() {}, setMessage(text, detail) { messages.push([text, detail]); },
    async focusActiveEditorPanel() {}, async auditBusinessListSearchConfig() { return explicitListSearch; },
    async auditBusinessAnalysisConfig() { return explicitAnalysis; },
    stageUnifiedDraftItem() { writeCalls += 1; }, publishDraft() { writeCalls += 1; }, rollbackPublished() { writeCalls += 1; },
    discardDraft() { writeCalls += 1; }, previewDraft() { writeCalls += 1; }, openImpactDialog() { writeCalls += 1; },
  };
  const lifecycle = loadPublishLifecycle()(deps);
  await lifecycle.loadListSearchConfig();
  const listDirty = [refs.listColumnsText.value, refs.searchFiltersText.value, refs.searchGroupByText.value]
    .some((value, index) => normalizeNamesText(value) !== Object.values(refs.listSearchBase.value)[index]);
  if (refs.listColumnsText.value || refs.searchFiltersText.value || refs.searchGroupByText.value) {
    errors.push('explicit empty list/search contract was replaced with suggestions');
  }
  if (listDirty) errors.push('explicit empty list/search reopen became dirty');
  if (messages.length) errors.push('explicit empty list/search reopen displayed generated suggestion message');

  await lifecycle.loadAnalysisConfig();
  const analysisDirty = normalizeNamesText(refs.pivotMeasuresText.value) !== refs.analysisBase.value.pivotMeasures
    || normalizeNamesText(refs.pivotDimensionsText.value) !== refs.analysisBase.value.pivotDimensions
    || normalizeNamesText(refs.graphMeasuresText.value) !== refs.analysisBase.value.graphMeasures
    || normalizeNamesText(refs.graphDimensionsText.value) !== refs.analysisBase.value.graphDimensions
    || refs.graphType.value !== refs.analysisBase.value.graphType;
  if (refs.pivotMeasuresText.value || refs.pivotDimensionsText.value || refs.graphMeasuresText.value || refs.graphDimensionsText.value) {
    errors.push('explicit empty analysis contract was replaced with suggestions');
  }
  if (analysisDirty) errors.push('explicit empty analysis reopen became dirty');
  if (messages.length) errors.push('explicit empty analysis reopen displayed generated suggestion message');
  if (writeCalls) errors.push('opening explicit empty editors caused a write operation');

  deps.auditBusinessListSearchConfig = async () => ({
    ...explicitListSearch,
    has_business_list_config: false,
    has_business_search_config: false,
  });
  messages.length = 0;
  await loadPublishLifecycle()(deps).loadListSearchConfig();
  if (refs.listColumnsText.value !== 'name' || refs.searchFiltersText.value !== 'state' || refs.searchGroupByText.value !== 'company_id') {
    errors.push('absent list/search contracts did not expose suggestions');
  }
  if (messages[0]?.[0] !== '建议配置，尚未保存') errors.push('absent contract suggestions are not marked unsaved');
  if (writeCalls) errors.push('opening absent-contract suggestions caused a write operation');
  return { errors, writeCalls, explicitEmptyPreserved: errors.length === 0 };
}

const files = [...new Set(scanRoots.flatMap(filesAt))]
  .filter((file) => /\.(?:ts|vue)$/.test(file))
  .map((file) => path.relative(webRoot, file));
const results = files.map((file) => analyzeSource(scriptText(path.join(webRoot, file)), file));
const negativePublish = analyzeSource('function save(){ api({ publish: true }); }', 'views/BusinessConfigSurfaceView.vue').errors.length > 0;
const negativePreview = analyzeSource('function previewDraft(){ publishBusinessConfigChangeSet(); }', 'views/example.ts').errors.length > 0;
const negativeEmptyStage = analyzeSource("function save(){ if (columns.length) stageUnifiedDraftItem({}); }", 'views/example.ts').errors.length > 0;
const draftSession = results[files.indexOf(unifiedPublisher)];
const publishStateGuard = Boolean(draftSession?.facts?.publishValidationThrows)
  && ['state', 'ok', 'runtime_verified'].every((key) => draftSession.facts.publishResultChecks.includes(key));
const lifecycle = results[files.indexOf('views/businessConfigSurface/useBusinessConfigPublishLifecycle.ts')];
const changedEmptyGuard = Number(lifecycle?.facts?.changedStageConditions || 0) >= 4
  && Number(lifecycle?.facts?.lengthStageConditions || 0) === 0;
const roundtripBehavior = await explicitEmptyRoundtripBehavior();
const report = {
  guard: 'low_code_publish_boundary_guard', parser: `typescript-${ts.version}`, scanned_files: files.length,
  ast_nodes: results.reduce((sum, row) => sum + row.nodeCount, 0), imports: results.reduce((sum, row) => sum + row.importCount, 0),
  assertions: 13,
  behavior_guards: {
    publish_state: publishStateGuard,
    changed_empty_stage: changedEmptyGuard,
    explicit_empty_roundtrip: roundtripBehavior.explicitEmptyPreserved,
    editor_open_write_count: roundtripBehavior.writeCalls,
  },
  negative_self_tests: { direct_publish_true: negativePublish, preview_calls_publish: negativePreview, changed_empty_uses_length: negativeEmptyStage },
  errors: results.flatMap((row) => row.errors).concat(roundtripBehavior.errors),
};
if (!negativePublish) report.errors.push('negative self-test accepted editor publish:true');
if (!negativePreview) report.errors.push('negative self-test accepted preview-to-publish call');
if (!negativeEmptyStage) report.errors.push('negative self-test accepted changed-but-empty length gate');
if (!publishStateGuard) report.errors.push('unified publisher does not require ready/published/ok/runtime verification states');
if (!changedEmptyGuard) report.errors.push('editor staging does not preserve changed-but-empty configuration');
process.stdout.write(`${JSON.stringify(report)}\n`);
process.exitCode = report.errors.length ? 1 : 0;
