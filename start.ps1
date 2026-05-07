$root = $PSScriptRoot

$backendCmd = "Set-Location '$root\backend'; py -3.11 -m uvicorn app.main:app --reload --port 8000"
$frontendCmd = "Set-Location '$root\frontend'; npm run dev"

Start-Process powershell -ArgumentList @("-NoExit", "-Command", $backendCmd)
Start-Sleep 3
Start-Process powershell -ArgumentList @("-NoExit", "-Command", $frontendCmd)
Start-Sleep 5
Start-Process "http://localhost:3000"
