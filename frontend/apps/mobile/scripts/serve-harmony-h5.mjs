import { createReadStream, existsSync, statSync } from 'node:fs';
import { createServer } from 'node:http';
import { extname, join, normalize, resolve } from 'node:path';
import { networkInterfaces } from 'node:os';

const root = resolve(process.cwd(), 'dist/build/h5');
const host = process.env.SC_MOBILE_HARMONY_HOST || '0.0.0.0';
const port = Number(process.env.SC_MOBILE_HARMONY_PORT || '8091');

const contentTypes = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2',
};

function contentType(file) {
  return contentTypes[extname(file)] || 'application/octet-stream';
}

function lanUrls() {
  const urls = [];
  for (const entries of Object.values(networkInterfaces())) {
    for (const entry of entries || []) {
      if (entry.family === 'IPv4' && !entry.internal) {
        urls.push(`http://${entry.address}:${port}`);
      }
    }
  }
  return urls;
}

if (!existsSync(join(root, 'index.html'))) {
  console.error(`harmony_h5 build output not found: ${root}`);
  process.exit(1);
}

const server = createServer((request, response) => {
  const requestPath = decodeURIComponent((request.url || '/').split('?')[0]);
  const relativePath = requestPath === '/' ? 'index.html' : requestPath.replace(/^\/+/, '');
  const filePath = normalize(join(root, relativePath));
  if (!filePath.startsWith(root) || !existsSync(filePath) || !statSync(filePath).isFile()) {
    response.writeHead(404);
    response.end('not found');
    return;
  }
  response.writeHead(200, { 'content-type': contentType(filePath) });
  createReadStream(filePath).pipe(response);
});

server.listen(port, host, () => {
  console.log(`harmony_h5 server: http://127.0.0.1:${port}`);
  for (const url of lanUrls()) {
    console.log(`harmony_h5 LAN: ${url}`);
  }
});
