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
const report = {
  guard: 'low_code_publish_boundary_guard', parser: `typescript-${ts.version}`, scanned_files: files.length,
  ast_nodes: results.reduce((sum, row) => sum + row.nodeCount, 0), imports: results.reduce((sum, row) => sum + row.importCount, 0),
  assertions: 8,
  behavior_guards: { publish_state: publishStateGuard, changed_empty_stage: changedEmptyGuard },
  negative_self_tests: { direct_publish_true: negativePublish, preview_calls_publish: negativePreview, changed_empty_uses_length: negativeEmptyStage },
  errors: results.flatMap((row) => row.errors),
};
if (!negativePublish) report.errors.push('negative self-test accepted editor publish:true');
if (!negativePreview) report.errors.push('negative self-test accepted preview-to-publish call');
if (!negativeEmptyStage) report.errors.push('negative self-test accepted changed-but-empty length gate');
if (!publishStateGuard) report.errors.push('unified publisher does not require ready/published/ok/runtime verification states');
if (!changedEmptyGuard) report.errors.push('editor staging does not preserve changed-but-empty configuration');
process.stdout.write(`${JSON.stringify(report)}\n`);
process.exitCode = report.errors.length ? 1 : 0;
