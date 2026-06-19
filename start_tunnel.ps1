$ErrorActionPreference = "Stop"

$cloudflaredPath = ".\cloudflared.exe"
$downloadUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"

if (-not (Test-Path $cloudflaredPath)) {
    Write-Host "Scaricando Cloudflare Tunnel (cloudflared.exe)..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $downloadUrl -OutFile $cloudflaredPath
    Write-Host "Download completato!" -ForegroundColor Green
} else {
    Write-Host "Cloudflare Tunnel già presente nel sistema." -ForegroundColor Green
}

Write-Host "`nAvvio del Tunnel Segreto verso la Dashboard locale..." -ForegroundColor Yellow
Write-Host "Attendi qualche secondo e cerca il link verde che finisce con '.trycloudflare.com'`n" -ForegroundColor Yellow

# Avvia il tunnel sulla porta di default di Streamlit (8501)
& $cloudflaredPath tunnel --url http://localhost:8501
