# deploy.ps1 — Guía de deploy Railway (backend) + Vercel (frontend)
# Ejecutar desde la raíz del repo.
#
# Prerequisitos:
#   npm install -g @railway/cli vercel
#
# Uso:
#   .\devops\infra\deploy.ps1

$ErrorActionPreference = "Stop"
$REPO_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host ""
Write-Host "=== UFI Barcelona — Deploy Script ===" -ForegroundColor Cyan
Write-Host ""

# ── 1. Verificar CLIs ────────────────────────────────────────────────────────
function Check-CLI($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Host "❌ '$name' no encontrado. Instala con: npm install -g @railway/cli vercel" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ $name disponible" -ForegroundColor Green
}

Check-CLI "railway"
Check-CLI "vercel"
Write-Host ""

# ── 2. Railway (backend) ─────────────────────────────────────────────────────
Write-Host "=== BACKEND — Railway ===" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Login en Railway..."
railway login

Write-Host "2. Inicializando proyecto Railway (solo primera vez)..."
Set-Location $REPO_ROOT
railway init

Write-Host ""
Write-Host "3. Variables de entorno que debes añadir en Railway dashboard:"
Write-Host "   https://railway.app  → tu proyecto → Variables" -ForegroundColor Gray
Write-Host ""
Write-Host "   ANTHROPIC_API_KEY = sk-ant-..."  -ForegroundColor Magenta
Write-Host "   DEMO_OFFLINE      = 0"           -ForegroundColor Magenta
Write-Host ""
Write-Host "   (Pulsa Enter cuando las hayas añadido)"
$null = Read-Host

Write-Host "4. Desplegando backend..."
railway up

$RAILWAY_URL = railway domain 2>$null
if ($RAILWAY_URL) {
    Write-Host ""
    Write-Host "✅ Backend desplegado en: https://$RAILWAY_URL" -ForegroundColor Green
    Write-Host "   Verifica: curl https://$RAILWAY_URL/health"
} else {
    Write-Host "⚠️  No se pudo obtener la URL automáticamente. Cópiala del dashboard de Railway." -ForegroundColor Yellow
    $RAILWAY_URL = Read-Host "Pega aquí la URL de Railway (sin https://)"
}

Write-Host ""

# ── 3. Vercel (frontend) ─────────────────────────────────────────────────────
Write-Host "=== FRONTEND — Vercel ===" -ForegroundColor Yellow
Write-Host ""
Write-Host "Añade esta variable en Vercel dashboard antes de continuar:"
Write-Host "  Vercel project → Settings → Environment Variables" -ForegroundColor Gray
Write-Host ""
Write-Host "  VITE_API_BASE_URL = https://$RAILWAY_URL" -ForegroundColor Magenta
Write-Host ""
Write-Host "(Pulsa Enter cuando la hayas añadido)"
$null = Read-Host

Set-Location "$REPO_ROOT\frontend"
Write-Host "Desplegando frontend en Vercel..."
vercel --prod

Write-Host ""
Write-Host "=== DEPLOY COMPLETADO ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Verifica end-to-end:"
Write-Host "  1. curl https://$RAILWAY_URL/health"
Write-Host "  2. Abre la URL de Vercel en el móvil"
Write-Host "  3. python devops/demo/qa_check.py https://$RAILWAY_URL"
Write-Host ""
