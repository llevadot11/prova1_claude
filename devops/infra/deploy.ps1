# =============================================================================
# UFI Barcelona — Script de Deploy
# =============================================================================
#
# USO (ejecutar desde la RAIZ del repo):
#   .\devops\infra\deploy.ps1                   → deploy completo (Railway + Vercel)
#   .\devops\infra\deploy.ps1 -Local            → docker-compose local
#   .\devops\infra\deploy.ps1 -Backend          → solo Railway (API)
#   .\devops\infra\deploy.ps1 -Frontend         → solo Vercel (front)
#   .\devops\infra\deploy.ps1 -Score            → regenerar Parquet UFI y committear
#   .\devops\infra\deploy.ps1 -QA <railway_url> → solo QA sobre una URL
#
# REQUISITOS (solo deploy cloud):
#   - railway login   (npm install -g @railway/cli)
#   - vercel login    (npm install -g vercel)
#   - .env en raiz con ANTHROPIC_API_KEY
#
# =============================================================================

param(
    [switch]$Local,
    [switch]$Backend,
    [switch]$Frontend,
    [switch]$Score,
    [string]$QA = ""
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $ROOT

# ─── helpers ─────────────────────────────────────────────────────────────────

function Write-Step { param($msg) Write-Host "`n► $msg" -ForegroundColor Cyan }
function Write-OK   { param($msg) Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function Write-Fail { param($msg) Write-Host "  ✗ $msg" -ForegroundColor Red; exit 1 }

function Require-Command {
    param($cmd, $hint)
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Fail "$cmd no encontrado. Instala con: $hint"
    }
    Write-OK "$cmd disponible"
}

function Wait-Health {
    param($url, [int]$retries = 15, [int]$delay = 8)
    Write-Step "Esperando health en $url/health ..."
    for ($i = 1; $i -le $retries; $i++) {
        try {
            $r = Invoke-RestMethod "$url/health" -TimeoutSec 5
            if ($r) { Write-OK "Servicio UP"; return }
        } catch {}
        Write-Host "  Intento $i/$retries — esperando ${delay}s..." -ForegroundColor DarkGray
        Start-Sleep $delay
    }
    Write-Fail "El servicio no respondio tras $retries intentos."
}

# ─── modo -QA ────────────────────────────────────────────────────────────────

if ($QA -ne "") {
    Write-Step "QA rapido sobre $QA"
    Require-Command python "instala Python 3.11"
    python devops/demo/qa_check.py $QA
    exit 0
}

# ─── modo -Score: regenerar Parquet y committear ─────────────────────────────

if ($Score) {
    Write-Step "Regenerando ufi_latest.parquet ..."
    Require-Command python "instala Python 3.11"
    Set-Location "$ROOT/data-ml"
    python -m ml.score
    if ($LASTEXITCODE -ne 0) { Write-Fail "ml.score fallo" }
    Set-Location $ROOT
    Write-OK "Parquet generado"

    Write-Step "Committeando datos procesados al repo..."
    git add data/processed/ufi_latest.parquet `
            data/processed/barrios.geojson `
            data/processed/tramos.geojson `
            data/processed/mapping_barrios.csv
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm"
    git commit -m "data: actualizar ufi_latest.parquet y GeoJSONs [$ts]"
    git push origin main
    Write-OK "Datos pusheados. Railway los incluira en el proximo deploy."
    exit 0
}

# ─── modo -Local ─────────────────────────────────────────────────────────────

if ($Local) {
    Write-Step "Arrancando con docker-compose (local)..."
    Require-Command docker "https://docs.docker.com/get-docker/"

    if (Test-Path "$ROOT/.env") {
        Get-Content "$ROOT/.env" | ForEach-Object {
            if ($_ -match "^([^#=]+)=(.*)$") {
                [System.Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim())
            }
        }
        Write-OK ".env cargado"
    } else {
        Write-Warn ".env no encontrado — ANTHROPIC_API_KEY puede faltar (explicaciones usaran fallback)"
    }

    Set-Location "$ROOT/devops/infra"
    docker compose up --build
    exit 0
}

# ─── deploy cloud (Railway + Vercel) ─────────────────────────────────────────

$doBackend  = $Backend  -or (-not $Frontend)
$doFrontend = $Frontend -or (-not $Backend)

Write-Host "`n╔══════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║   UFI Barcelona — Deploy a la nube   ║" -ForegroundColor Magenta
Write-Host "╚══════════════════════════════════════╝`n" -ForegroundColor Magenta

# ── 1. Prerequisitos ──────────────────────────────────────────────────────────
Write-Step "Comprobando prerequisitos..."
if ($doBackend)  { Require-Command railway "npm install -g @railway/cli" }
if ($doFrontend) { Require-Command vercel  "npm install -g vercel" }
Require-Command git "https://git-scm.com"

if (-not (Test-Path "$ROOT/.env")) {
    Write-Warn ".env no encontrado — asegurate de tener ANTHROPIC_API_KEY en Railway dashboard"
} else {
    Write-OK ".env presente"
}

# ── 2. Verificar datos criticos ───────────────────────────────────────────────
Write-Step "Verificando datos procesados (se incluyen en la imagen Docker)..."
$needed = @(
    "data/processed/ufi_latest.parquet",
    "data/processed/barrios.geojson",
    "data/processed/tramos.geojson",
    "data/processed/mapping_barrios.csv"
)
$missing = $needed | Where-Object { -not (Test-Path "$ROOT/$_") }
if ($missing) {
    Write-Warn "Faltan datos procesados:"
    $missing | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    Write-Fail "Ejecuta primero: .\devops\infra\deploy.ps1 -Score"
}
Write-OK "Datos procesados presentes"

# ── 3. Verificar git status ───────────────────────────────────────────────────
Write-Step "Verificando git status..."
$dirty = git status --porcelain
if ($dirty) {
    Write-Warn "Hay cambios sin committear (Railway/Vercel suben archivos LOCALES, no el commit)."
} else {
    Write-OK "Working tree limpio"
}

# ── 4. Deploy Railway (backend) ───────────────────────────────────────────────
$railwayUrl = ""

if ($doBackend) {
    Write-Step "Desplegando backend en Railway..."

    $rWho = railway whoami 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Fail "No logueado en Railway. Ejecuta: railway login" }
    Write-OK "Railway: $rWho"

    # Usa el Dockerfile raiz (contiene el backend + datos procesados)
    railway up --detach
    if ($LASTEXITCODE -ne 0) { Write-Fail "railway up fallo" }
    Write-OK "Build enviado a Railway (puede tardar 2-3 min)"

    Start-Sleep 10
    $domainOut = railway domain 2>&1
    $railwayUrl = ($domainOut | Select-String "https://[^\s]+" | ForEach-Object { $_.Matches[0].Value }) | Select-Object -First 1
    if (-not $railwayUrl) {
        $railwayUrl = Read-Host "  URL de Railway (ej: https://ufi-xxx.up.railway.app)"
    }
    Write-OK "URL Railway: $railwayUrl"
    Wait-Health $railwayUrl
}

# ── 5. Deploy Vercel (frontend) ───────────────────────────────────────────────
$vercelUrl = ""

if ($doFrontend) {
    Write-Step "Desplegando frontend en Vercel..."

    if (-not $railwayUrl) {
        $railwayUrl = Read-Host "  URL del backend Railway (ej: https://ufi-xxx.up.railway.app)"
    }

    $vWho = vercel whoami 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Fail "No logueado en Vercel. Ejecuta: vercel login" }
    Write-OK "Vercel: $vWho"

    Set-Location "$ROOT/frontend"

    # Construye con la URL de Railway inyectada en VITE_API_BASE_URL
    # Vercel la usa en build-time para que los fetch vayan directo al backend
    vercel --prod --yes --env "VITE_API_BASE_URL=$railwayUrl"
    if ($LASTEXITCODE -ne 0) { Write-Fail "vercel deploy fallo" }

    $vercelOut = vercel ls --prod 2>&1
    $vercelUrl = ($vercelOut | Select-String "https://[^\s]+" | ForEach-Object { $_.Matches[0].Value }) | Select-Object -First 1
    if ($vercelUrl) { Write-OK "URL Vercel: $vercelUrl" }
    Set-Location $ROOT
}

# ── 6. QA automatico ─────────────────────────────────────────────────────────
if ($railwayUrl) {
    Write-Step "QA automatico sobre Railway..."
    python devops/demo/qa_check.py $railwayUrl
}

# ── 7. Pre-warm (opcional, ~12 min) ──────────────────────────────────────────
if ($railwayUrl) {
    Write-Warn "Pre-warm de cache Claude no lanzado (ejecuta cuando quieras):"
    Write-Host "  python devops/demo/prewarm.py $railwayUrl" -ForegroundColor DarkGray
}

# ── 8. Resumen final ──────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║        DEPLOY COMPLETADO  ✓          ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Green
if ($railwayUrl) { Write-Host "  API:    $railwayUrl" -ForegroundColor White }
if ($vercelUrl)  { Write-Host "  Front:  $vercelUrl"  -ForegroundColor White }
Write-Host ""
Write-Host "  Checklist post-deploy:" -ForegroundColor DarkGray
Write-Host "  [ ] Abre $vercelUrl en movil y verifica que el mapa carga" -ForegroundColor DarkGray
Write-Host "  [ ] Sabado 22:00 → .\devops\infra\deploy.ps1 -Score  (actualizar Parquet)" -ForegroundColor DarkGray
Write-Host "  [ ] Sabado 22:00 → python devops/demo/snapshot.py" -ForegroundColor DarkGray
Write-Host "  [ ] Sabado 22:00 → python devops/demo/prewarm.py $railwayUrl" -ForegroundColor DarkGray
Write-Host "  [ ] Domingo 14:00 → 3 ensayos de demo" -ForegroundColor DarkGray
Write-Host ""
