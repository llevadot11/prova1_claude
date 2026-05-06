"""Naturalización de explicaciones con Claude Haiku 4.5 + cache estricto.

Cache key = (barrio_id, hora_redondeada, top3_family_signature).
Persona D lanza pre-warm el sábado por la noche para 73 × 24h × 4 modos.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime

from app import cache
from app.config import settings
from app.schemas import BarrioDetail, ExplainResponse

EXPLAIN_TTL = 60 * 60 * 24  # 24h

SYSTEM_PROMPT = (
    "Eres un asistente que explica en castellano, en una sola frase corta y "
    "natural, por qué un barrio de Barcelona tendrá fricción urbana alta o "
    "baja. Recibes el barrio, la hora, el modo de usuario y las 3 familias "
    "que más contribuyen al score con sus valores crudos. Devuelve SOLO la "
    "frase, sin saludos, sin justificar la metodología."
)


def _signature(detail: BarrioDetail) -> str:
    top3 = sorted(detail.contribuciones, key=lambda c: -c.contribution_pct)[:3]
    families = "|".join(c.family for c in top3)
    hour = detail.at.replace(minute=0, second=0, microsecond=0).isoformat()
    raw_blob = json.dumps(detail.raw, sort_keys=True)
    h = hashlib.sha1(f"{detail.barrio_id}|{hour}|{detail.mode}|{families}|{raw_blob}".encode()).hexdigest()
    return h[:16]


async def explain(detail: BarrioDetail) -> ExplainResponse:
    key = f"explain:{_signature(detail)}"
    cached = cache.get(key)
    if cached is not None:
        return ExplainResponse(
            barrio_id=detail.barrio_id,
            at=detail.at,
            mode=detail.mode,
            text=cached,
            cached=True,
        )

    text = await _generate(detail)
    cache.put(key, text, EXPLAIN_TTL)
    return ExplainResponse(
        barrio_id=detail.barrio_id,
        at=detail.at,
        mode=detail.mode,
        text=text,
        cached=False,
    )


async def _generate(detail: BarrioDetail) -> str:
    if settings.demo_offline or not settings.anthropic_api_key:
        return _fallback_template(detail)

    # Lazy import — no rompe arranque sin la lib.
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    top3 = sorted(detail.contribuciones, key=lambda c: -c.contribution_pct)[:3]
    user_payload = {
        "barrio": detail.barrio_name,
        "hora": detail.at.isoformat(),
        "modo": detail.mode,
        "ufi": detail.ufi,
        "top3": [
            {"family": c.family, "contribution_pct": round(c.contribution_pct, 1)}
            for c in top3
        ],
        "valores": detail.raw,
    }
    msg = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}],
    )
    return msg.content[0].text.strip()


def _fallback_template(detail: BarrioDetail) -> str:
    top3 = sorted(detail.contribuciones, key=lambda c: -c.contribution_pct)[:3]
    families_es = {
        "trafico": "el tráfico",
        "accidentes": "el riesgo histórico de accidentes",
        "aire": "la calidad del aire",
        "meteo": "la meteo",
        "sensibilidad": "la concentración de puntos sensibles",
    }
    razones = ", ".join(families_es[c.family] for c in top3)
    return (
        f"{detail.barrio_name} tendrá un UFI {detail.ufi:.0f} a las "
        f"{detail.at.strftime('%H:%M')}: principalmente por {razones}."
    )
