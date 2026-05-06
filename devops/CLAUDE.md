# Persona D — DevOps, Integración & Demo Master

**Tu carpeta**: `devops/`
**Tu misión**: que el viernes a las 22:00 haya una URL pública. Y que el domingo a las 18:00 la demo no falle.

---

## Tu rol en el equipo

Eres el pegamento. No haces features, haces que todo funcione junto. Mantienes la URL pública, generas el snapshot de fallback, practicas la demo, y eres el reviewer que avisa cuando algo rompería la integración.

---

## Stack

| Herramienta | Para qué |
|---|---|
| Docker + docker-compose | Entorno local reproducible |
| Vercel CLI | Deploy del frontend (gratuito) |
| Railway CLI | Deploy del backend (gratuito, acepta Dockerfile) |
| PowerShell | Scripts de seed, snapshot, pre-warm |

---

## Comandos

```powershell
# Arrancar todo local
cd devops/infra; docker-compose up --build

# Deploy Railway (primera vez)
railway login; railway init; railway up

# Deploy Vercel (primera vez)
cd frontend; vercel --prod

# Generar snapshot fallback (sábado 22:00 OBLIGATORIO)
python devops/demo/snapshot.py

# Pre-warm cache de explicaciones (sábado 22:00)
python devops/demo/prewarm.py

# Modo demo offline (para probar fallback)
$env:DEMO_OFFLINE=1; cd backend; uvicorn app.main:app --port 8000
```

---

## Estructura de ficheros

```
devops/
  infra/
    docker-compose.yml   Backend :8000 + Frontend :3000 local.
    railway.json         Config de deploy Railway.
  demo/
    snapshot.py          Copia ufi_latest.parquet → demo_snapshot.parquet.
    prewarm.py           Itera 73 barrios × 24h × 4 modos → llena cache Claude.
    guion.md             Guion de demo de 3 minutos.
    snapshots/           .parquets datados (en .gitignore).
  tasks.md               ← TU LISTA DE TAREAS
  skills.md              ← Subagentes y skills útiles
```

---

## Hitos que tú controlas

| Cuándo | Hito | Acción |
|---|---|---|
| Vie 22:00 | H0: pipeline end-to-end | Confirmar que front llama al back y pinta datos |
| Sáb 14:00 | H1: URL pública | Railway + Vercel levantados con MVP heurístico |
| Sáb 22:00 | H2: producto completo | **Generar snapshot + lanzar pre-warm** |
| Dom 14:00 | Code freeze | 3 ensayos completos de la demo de 3 min |

---

## Responsabilidades de reviewer transversal

- Revisar PRs / cambios de A y C antes de que rompan el contrato de la API.
- Si B cambia `schemas.py`, verificar que A actualiza `api.ts`.
- Si C cambia el schema del Parquet, verificar que B actualiza `store.py`.
- Mantener `.env.example` actualizado si alguien añade variables.
- Monitorear `/health` periódicamente durante el hackathon.

---

## Plan B (NO llegar sin esto al domingo)

1. `DEMO_OFFLINE=1` en `.env` → la app sirve del snapshot, sin APIs externas.
2. `devops/demo/snapshots/` tiene el `.parquet` datado del sábado 22:00.
3. Vídeo grabado de la app funcionando en `devops/demo/recording.mp4`.
4. Captura de pantalla para las slides si la URL pública no carga.

---

## Subagents que puedes pedir a Claude Code

Ver [skills.md](skills.md). Resumen:
- `general-purpose` → *"Escribe el script prewarm.py que llame a /explain para los 73 barrios × 24h × 4 modos"*
- `Explore` → *"¿Cómo configurar Railway para variables de entorno en tiempo de deploy?"*
- `claude-code-guide` → dudas sobre docker-compose, Vercel, Railway
- `security-review` skill → revisar que no hay claves expuestas en ningún fichero antes del deploy
