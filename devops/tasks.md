# Tareas — Persona D (DevOps & Demo Master)

> Abre esta carpeta en Claude Code con `claude` desde `devops/`.
> Marca cada tarea con `[x]` al terminarla.

---

## Bloque 1 — Viernes 19:00–22:00 (Setup + primer deploy)

- [x] **Corregir docker-compose.yml**: build contexts apuntaban a `../apps/api` y `../apps/web` inexistentes → corregido a `../../backend` y `../../frontend`. Volumen de datos montado en `/data` (no `/app/data`) porque `config.py` resuelve `repo_root = /` en Docker.
- [x] **Crear `frontend/nginx.conf`**: proxy `/api/` → `http://api:8000/` + SPA fallback
- [x] **Actualizar `frontend/Dockerfile`**: copia nginx.conf + ARG VITE_API_BASE_URL
- [x] **Crear `Dockerfile` en raíz**: para Railway (build context = repo root), crea `/data/*` dirs vacíos
- [x] **Corregir `railway.json`**: `dockerfilePath` era `apps/api/Dockerfile` → `Dockerfile`
- [x] **Corregir `devops/demo/snapshot.py`**: `parents[1]` → `parents[2]` para llegar a repo root
- [x] **README.md en la raíz** del repo
- [ ] **Crear cuenta en Railway**: https://railway.app (free tier)
- [ ] **Crear proyecto en Vercel** para el frontend
- [ ] **Definir variables en Railway**: `ANTHROPIC_API_KEY`, `DEMO_OFFLINE=0`
- [ ] **Confirmar paleta y nombre** con Persona A antes del topbar

---

## Bloque 2 — Sábado 09:00–14:00 (URL pública H1)

- [ ] **Deploy Railway**:
  ```powershell
  cd <repo_root>
  .\devops\infra\deploy.ps1   # ← script interactivo que guía el proceso
  # O manualmente:
  railway login; railway init; railway up
  ```
- [ ] **Deploy Vercel**:
  ```powershell
  cd frontend
  vercel --prod
  # VITE_API_BASE_URL=<URL Railway> en Vercel dashboard
  ```
- [ ] **Verificar H1 end-to-end**:
  ```powershell
  python devops/demo/qa_check.py https://<railway-url>
  ```
- [ ] **Compartir URL pública** con el equipo
- [ ] **QA de B**: probar `/docs` en Railway URL

---

## Bloque 3 — Sábado 14:00–22:00 (Integración + prewarm)

- [x] **`devops/demo/prewarm.py`**: 73 barrios × 24h × 4 modos = 7.008 req, rate limit 10 req/s, tqdm, asyncio, configurable por URL
- [x] **`devops/demo/qa_check.py`**: QA script que bate todos los endpoints y reporta status
- [x] **`devops/requirements.txt`**: httpx + tqdm para los scripts devops
- [ ] **Smoke QA transversal** cuando A y C integren:
  - Mapa carga datos reales (no stub sin geometría)
  - Click barrio → texto natural (no fallback de plantilla)
  - Cambiar modo → ranking cambia
- [ ] **Revisar cambios de B** (schemas.py) → avisar a A si rompen api.ts
- [ ] **Revisar cambios de C** (schema Parquet) → avisar a B si rompen store.py

---

## Sábado 22:00 — Operaciones críticas (NO saltarse)

- [ ] **Generar snapshot fallback**:
  ```powershell
  python devops/demo/snapshot.py
  # Verifica que data/processed/demo_snapshot.parquet existe
  ```
- [ ] **Lanzar pre-warm**:
  ```powershell
  pip install -r devops/requirements.txt
  python devops/demo/prewarm.py https://<railway-url>
  # ~12 min — 7.008 llamadas → cache garantizado mañana
  ```
- [ ] **Probar modo offline**:
  ```powershell
  $env:DEMO_OFFLINE=1; cd backend; uvicorn app.main:app --port 8000
  python devops/demo/qa_check.py  # debe responder sin red
  ```
- [ ] **Grabar vídeo** siguiendo `devops/demo/guion.md` → `devops/demo/recording.mp4`

---

## Bloque 4 — Domingo 09:00–14:00 (Ensayos + deploy final)

- [ ] **Verificar Parquet en Railway**: si la URL de Railway no tiene el parquet real de C, sube a S3/R2 o usa Railway persistent volumes
- [ ] **Comprobar `/health`** en producción: todos en `"ok"`
- [ ] **Ensayo #1 (09:30)**: 3 min, cronometrar, anotar problemas
- [ ] **Ensayo #2 (11:00)**: con correcciones
- [ ] **Ensayo #3 (13:00)**: simulación completa + preguntas de jurado
- [x] **Security review**: sin `.env` en el repo, `ANTHROPIC_API_KEY` solo en dashboards

---

## Criterio de "done"

- [ ] URL pública accesible desde móvil
- [ ] `DEMO_OFFLINE=1` funciona sin red (snapshot listo)
- [ ] Vídeo de 3 min grabado como plan B
- [ ] 3 ensayos completados sin errores
- [ ] Guion dominado: hook → UFI vivo → slider → modos → tramos → cierre
