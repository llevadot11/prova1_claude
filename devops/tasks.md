# Tareas — Persona D (DevOps & Demo Master)

> Abre esta carpeta en Claude Code con `claude` desde `devops/`.
> Marca cada tarea con `[x]` al terminarla.

---

## Bloque 1 — Viernes 19:00–22:00 (Setup + primer deploy)

- [ ] **Verificar que docker-compose funciona**:
  ```powershell
  cd devops/infra
  docker-compose up --build
  # ¿Están los puertos :8000 y :3000 accesibles?
  ```
- [ ] **Crear cuenta en Railway** (si no existe): `https://railway.app`
  - Free tier permite 5$/mes gratis, suficiente para la demo
- [ ] **Crear proyecto en Vercel** para el frontend
- [ ] **Definir variables de entorno en Railway**:
  - `ANTHROPIC_API_KEY`
  - `DEMO_OFFLINE=0`
- [ ] **README.md en la raíz** del repo con: ¿qué hace el proyecto? ¿cómo arrancarlo?
- [ ] **Decidir paleta y nombre** del producto con A (antes de que A construya el topbar)

---

## Bloque 2 — Sábado 09:00–14:00 (URL pública H1)

- [ ] **Deploy Railway**:
  ```powershell
  cd <repo_root>
  railway login; railway init
  railway up
  # Copiar la URL generada
  ```
- [ ] **Deploy Vercel**:
  ```powershell
  cd frontend
  # Añadir VITE_API_BASE_URL=<URL de Railway> en Vercel dashboard
  vercel --prod
  ```
- [ ] **Verificar H1 end-to-end**:
  - URL Railway: `curl https://<railway>.up.railway.app/health`
  - URL Vercel: abrir en móvil, verificar que mapa carga
- [ ] **Compartir URL pública** con el equipo
- [ ] **QA de B**: probar todos los endpoints con curl o la UI de `/docs`

---

## Bloque 3 — Sábado 14:00–22:00 (Integración + script prewarm)

- [ ] **Escribir `demo/prewarm.py`**:
  - Itera 73 barrios × 24 horas × 4 modos = 7.008 llamadas a `/explain`
  - Con rate limit de 10 req/s y timeout 5s
  - Muestra barra de progreso (tqdm)
  - Llama a la URL de Railway (no local)
- [ ] **Smoke QA transversal** cuando A y C hayan integrado:
  - Abrir en navegador → mapa carga con datos reales
  - Click en barrio → aparece texto natural (no el fallback de plantilla)
  - Cambiar modo → ranking cambia
- [ ] **Revisar PR/cambios de B**: ¿`schemas.py` tiene cambios? → avisar a A
- [ ] **Revisar PR/cambios de C**: ¿el schema del Parquet cambió? → avisar a B
- [ ] **Actualizar `.env.example`** si alguien añadió variables

---

## Sábado 22:00 — Operaciones críticas (NO saltarse)

- [ ] **Generar snapshot fallback**:
  ```powershell
  cd <repo_root>
  python devops/demo/snapshot.py
  # Verifica que data/processed/demo_snapshot.parquet existe
  ```
- [ ] **Lanzar prewarm**:
  ```powershell
  python devops/demo/prewarm.py
  # 7k llamadas con cache hit garantizado mañana
  ```
- [ ] **Probar modo offline**:
  ```powershell
  $env:DEMO_OFFLINE=1; cd backend; uvicorn app.main:app --port 8000
  # ¿La app sigue funcionando sin red?
  ```
- [ ] **Grabar vídeo de la app** funcionando (backup para demo):
  - 3 minutos siguiendo el guion de `demo/guion.md`
  - Guardar en `devops/demo/recording.mp4`

---

## Bloque 4 — Domingo 09:00–14:00 (Ensayos + deploy final)

- [ ] **Asegurarse de que el deploy de Railway tiene el Parquet real** de C:
  - Si Railway no tiene acceso al Parquet (es un fichero local), subir a un bucket S3 gratuito (Cloudflare R2) o montar el Parquet directamente en el repo con git-lfs
  - Alternativa más simple: Railway con volumen persistente donde C sube el `.parquet`
- [ ] **Comprobar `/health`** en producción: todos los servicios en `"ok"`
- [ ] **Ensayo #1 (09:30)**: guion completo de 3 min. Cronometrar. Tomar nota de problemas.
- [ ] **Ensayo #2 (11:00)**: igual que antes, con correcciones del ensayo 1.
- [ ] **Ensayo #3 (13:00)**: simulación completa incluyendo preguntas del jurado.
- [ ] **Security review antes del deploy final**:
  - Ningún `.env` en el repositorio
  - `ANTHROPIC_API_KEY` solo en Vercel/Railway dashboard, nunca en código

---

## Criterio de "done" para la demo

- [ ] URL pública accesible desde móvil
- [ ] `DEMO_OFFLINE=1` funciona sin red (snapshot listo)
- [ ] Vídeo de 3 min grabado como plan B
- [ ] 3 ensayos de demo completados sin errores
- [ ] Guion dominado: hook → UFI vivo → slider → modos → tramos → cierre
