# Skills & Subagents — Persona D (DevOps & Demo Master)

> Cómo sacarle el máximo partido a Claude Code desde tu carpeta.
> Abre Claude Code con `claude` desde `devops/`.

---

## Subagentes que puedes lanzar

### `general-purpose` — scripts y automatizaciones
```
Ejemplos:

"Escribe devops/demo/prewarm.py.
 Objetivo: llenar la cache SQLite del backend con todas las explicaciones
 antes de la demo para que no haya latencia de Claude.
 - Hace GET /explain/{barrio_id}?at={iso}&mode={mode}
   para los 73 barrios × próximas 24 horas × 4 modos = 7008 llamadas
 - Rate limit: máximo 10 req/s (asyncio Semaphore)
 - Target URL: variable de entorno RAILWAY_URL
 - Barra de progreso con tqdm
 - Si una falla, la loguea y sigue"

"Escribe un script devops/check_deploy.py que verifica que el deploy
 de Railway está bien antes de la demo:
 - GET /health y verifica que todos los campos son 'ok'
 - GET /ufi y verifica que devuelve 73 barrios
 - GET /explain/BAR-001 y verifica que el texto no es el fallback de plantilla
 - Imprime ✅ o ❌ por cada check"
```

### `Explore` — entender infra y configs
```
"¿Cómo configuro variables de entorno secretas en Railway sin que aparezcan en el repo?"
"¿Qué hace la opción `restart_policy` en docker-compose?"
"¿Cómo sirve Vercel ficheros estáticos y cómo configuro el redirect para SPA?"
"¿Qué diferencia hay entre RAILWAY_URL y la URL del proyecto en Railway?"
```

### `claude-code-guide` — dudas de infra
```
"¿Cómo hago que docker-compose use las variables del .env raíz?"
"¿Cómo configuro en Vercel que todas las rutas que no sean /api caigan en index.html?"
"¿Cómo depuro un error 500 en Railway sin acceso SSH?"
```

### `security-review` skill (slash command)
**Invoca con `/security-review` antes del deploy final**:
- Verifica que no hay `.env` commiteado
- Verifica que no hay `ANTHROPIC_API_KEY` hardcodeada
- Verifica que CORS no acepta `*` en producción
- Revisa `.gitignore`

---

## Slash commands útiles

| Comando | Cuándo usarlo |
|---|---|
| `/review` | Cuando revisas un PR de A, B o C antes de mergear. |
| `/security-review` | **Obligatorio** antes del deploy final en Railway/Vercel. |
| `/simplify` | Si el docker-compose o un script está demasiado complejo. |

---

## Patrones de prompt para review transversal

### Revisar un cambio de A
```
"Persona A hizo cambios en App.tsx y src/api.ts.
 ¿El cambio en api.ts sigue siendo compatible con el schema de backend/app/schemas.py?
 Aquí está el diff: [pega]"
```

### Revisar un cambio de C (schema del Parquet)
```
"Persona C dice que añadió la columna score_eventos al ufi_latest.parquet.
 ¿Hay algún lugar en backend/app/store.py donde esto pueda romper algo?
 ¿Necesita B actualizar el código?"
```

### Preparar el guion de demo
```
"Lee devops/demo/guion.md y dame feedback:
 - ¿Los 3 minutos están bien distribuidos?
 - ¿Hay algún paso que sea difícil de ejecutar en vivo?
 - ¿Qué pregunta del jurado debería anticipar?"
```

---

## Checklist del sábado 22:00 (NO saltarse)

Ejecuta esto exactamente en este orden:

```powershell
# 1. Asegurarse de que el Parquet real de C está en el servidor de Railway
#    (pedir a C que confirme con `ls data/processed/`)

# 2. Verificar deploy
python devops/check_deploy.py

# 3. Generar snapshot
python devops/demo/snapshot.py

# 4. Pre-warm (puede tardar 10-15 min)
python devops/demo/prewarm.py

# 5. Probar modo offline
$env:DEMO_OFFLINE=1
cd backend; uvicorn app.main:app --port 8000
# Abrir en browser y verificar que funciona

# 6. Grabar vídeo
# OBS Studio o cualquier grabador de pantalla, 3 minutos siguiendo guion.md
```

---

## Reglas para no perder tiempo

1. **No esperes a que el código esté perfecto para hacer el primer deploy**. Despliega el stub el viernes mismo.
2. **La URL pública es la que usan A, B y C para probar**. Cuanto antes mejor.
3. **El prewarm es crítico**: sin él, `/explain` tarda 2-3s en demo en lugar de 50ms.
4. **Graba el vídeo el sábado**. Si el domingo falla algo, el vídeo salva la demo.
5. **Tú eres el guardián del contrato**: si A o C cambian algo que puede romper B, tú lo detectas primero.
