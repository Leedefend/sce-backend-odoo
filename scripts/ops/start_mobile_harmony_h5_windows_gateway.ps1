param(
    [string]$H5Root = "$env:USERPROFILE\sce-mobile-harmony-h5",
    [int]$H5Port = 8092,
    [int]$BackendProxyPort = 8071,
    [string]$BackendHost = "127.0.0.1",
    [int]$BackendPort = 18069
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $H5Root)) {
    throw "H5 root not found: $H5Root. Run pnpm -C frontend/apps/mobile build:h5:harmony:windows first."
}

function Stop-ListeningPort {
    param([int]$Port)

    $connections = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

$python = (Get-Command python -ErrorAction Stop).Source
$gatewayRoot = Join-Path $env:TEMP "sce-mobile-harmony-gateway"
New-Item -ItemType Directory -Force -Path $gatewayRoot | Out-Null

$proxyScript = Join-Path $gatewayRoot "tcp_proxy.py"
@'
import socket
import socketserver
import sys
import threading

listen_port = int(sys.argv[1])
target_host = sys.argv[2]
target_port = int(sys.argv[3])


class ProxyHandler(socketserver.BaseRequestHandler):
    def handle(self):
        upstream = socket.create_connection((target_host, target_port))

        def pipe(src, dst):
            try:
                while True:
                    data = src.recv(65536)
                    if not data:
                        break
                    dst.sendall(data)
            finally:
                try:
                    dst.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                dst.close()

        threading.Thread(target=pipe, args=(self.request, upstream), daemon=True).start()
        pipe(upstream, self.request)


class ThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


with ThreadingTCPServer(("0.0.0.0", listen_port), ProxyHandler) as server:
    print(f"backend proxy: 0.0.0.0:{listen_port} -> {target_host}:{target_port}", flush=True)
    server.serve_forever()
'@ | Set-Content -Encoding UTF8 -Path $proxyScript

Stop-ListeningPort -Port $H5Port
Stop-ListeningPort -Port $BackendProxyPort

Start-Process -FilePath $python -ArgumentList @("-m", "http.server", "$H5Port", "--bind", "0.0.0.0", "--directory", $H5Root) -WindowStyle Minimized
Start-Process -FilePath $python -ArgumentList @($proxyScript, "$BackendProxyPort", $BackendHost, "$BackendPort") -WindowStyle Minimized

$ips = Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -ne "WellKnown" } |
    Select-Object -ExpandProperty IPAddress

Write-Host "Harmony H5 gateway started."
foreach ($ip in $ips) {
    Write-Host "H5:      http://$ip`:$H5Port"
    Write-Host "Backend: http://$ip`:$BackendProxyPort"
}
