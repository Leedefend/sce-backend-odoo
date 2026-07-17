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
    ts.forEachChild(node, (child) => walk(child, activeFunction));
  }
  walk(ast);
  return { errors, nodeCount, importCount };
}

const files = [...new Set(scanRoots.flatMap(filesAt))]
  .filter((file) => /\.(?:ts|vue)$/.test(file))
  .map((file) => path.relative(webRoot, file));
const results = files.map((file) => analyzeSource(scriptText(path.join(webRoot, file)), file));
const negativePublish = analyzeSource('function save(){ api({ publish: true }); }', 'views/BusinessConfigSurfaceView.vue').errors.length > 0;
const negativePreview = analyzeSource('function previewDraft(){ publishBusinessConfigChangeSet(); }', 'views/example.ts').errors.length > 0;
const report = {
  guard: 'low_code_publish_boundary_guard', parser: `typescript-${ts.version}`, scanned_files: files.length,
  ast_nodes: results.reduce((sum, row) => sum + row.nodeCount, 0), imports: results.reduce((sum, row) => sum + row.importCount, 0),
  assertions: 4, negative_self_tests: { direct_publish_true: negativePublish, preview_calls_publish: negativePreview },
  errors: results.flatMap((row) => row.errors),
};
if (!negativePublish) report.errors.push('negative self-test accepted editor publish:true');
if (!negativePreview) report.errors.push('negative self-test accepted preview-to-publish call');
process.stdout.write(`${JSON.stringify(report)}\n`);
process.exitCode = report.errors.length ? 1 : 0;
