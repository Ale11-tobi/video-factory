$S3fdModelDir = "Wav2Lip\face_detection\detection\sfd"
New-Item -ItemType Directory -Force -Path $S3fdModelDir | Out-Null
$S3fdModel = "$S3fdModelDir\s3fd.pth"
if (-not (Test-Path $S3fdModel)) {
    Write-Host "Downloading S3FD model..."
    Invoke-WebRequest -Uri "https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth" -OutFile $S3fdModel
}
Write-Host "Done downloading S3FD!"
