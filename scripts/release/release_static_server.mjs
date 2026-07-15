import { createReadStream, statSync } from 'node:fs'
import { createServer, request as httpRequest } from 'node:http'
import { extname, join, normalize } from 'node:path'

const root = process.env.STATIC_ROOT
const port = Number(process.env.STATIC_PORT || 5175)
const proxy = new URL(process.env.API_PROXY_TARGET || 'http://127.0.0.1:18082')
if (!root) throw new Error('STATIC_ROOT is required')

const contentTypes = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.svg': 'image/svg+xml' }

createServer((req, res) => {
  if ((req.url || '').startsWith('/api/')) {
    const upstream = httpRequest({ hostname: proxy.hostname, port: proxy.port, method: req.method, path: req.url, headers: { ...req.headers, host: proxy.host } }, (up) => {
      res.writeHead(up.statusCode || 502, up.headers)
      up.pipe(res)
    })
    upstream.on('error', () => { res.writeHead(502, { 'content-type': 'application/json' }); res.end('{"error":"upstream unavailable"}') })
    req.pipe(upstream)
    return
  }
  const raw = decodeURIComponent((req.url || '/').split('?')[0])
  let candidate = normalize(join(root, raw === '/' ? 'index.html' : raw))
  if (!candidate.startsWith(normalize(root))) candidate = join(root, 'index.html')
  try { if (!statSync(candidate).isFile()) candidate = join(root, 'index.html') } catch { candidate = join(root, 'index.html') }
  res.writeHead(200, { 'content-type': contentTypes[extname(candidate)] || 'application/octet-stream', 'cache-control': candidate.endsWith('index.html') ? 'no-cache' : 'public, max-age=31536000, immutable', 'x-content-type-options': 'nosniff' })
  createReadStream(candidate).pipe(res)
}).listen(port, '127.0.0.1', () => process.stdout.write(`[release.static] listening on ${port}\n`))
