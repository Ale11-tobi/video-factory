$ErrorActionPreference = "Stop"

$startupFolder = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupFolder "ZeroTouchFactoryDaemon.vbs"

$currentDir = $PWD.Path
$pythonExe = Join-Path $currentDir "venv\Scripts\python.exe"

$vbsContent = @"
Set WshShell = CreateObject("WScript.Shell")
' Avvia il Daemon invisibile senza finestre nere
WshShell.Run "cmd /c cd /d `"$currentDir`" && `"$pythonExe`" core\factory_daemon.py", 0, False
"@

Set-Content -Path $shortcutPath -Value $vbsContent

Write-Host "✅ Configurazione Automatica completata!" -ForegroundColor Green
Write-Host "Ogni volta che accenderai il PC, il Factory Daemon si avvierà in modo invisibile." -ForegroundColor Cyan
Write-Host "Riceverai automaticamente su Telegram il link Cloudflare di oggi e i bottoni per interrogare lo Stato Lavori!" -ForegroundColor Cyan
Write-Host "File installato in: $shortcutPath" -ForegroundColor DarkGray
