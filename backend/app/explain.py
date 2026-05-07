"""Naturalización de explicaciones con Claude Haiku 4.5 + cache estricto.

Cache key = (barrio_id, hora_redondeada, top3_family_signature).
Persona D lanza pre-warm el sábado por la noche para 73 × 24h × 4 modos.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import AsyncIterator

from app import cache
from app.config import settings
from app.schemas import BarrioDetail, ExplainResponse

logger = logging.getLogger(__name__)

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
    h = hashlib.sha1(
        f"{detail.barrio_id}|{hour}|{detail.mode}|{families}|{raw_blob}".encode()
    ).hexdigest()
    return h[:16]


def _build_user_payload(detail: BarrioDetail) -> str:
    top3 = sorted(detail.contribuciones, key=lambda c: -c.contribution_pct)[:3]
    return json.dumps(
        {
            "barrio": detail.barrio_name,
            "hora": detail.at.isoformat(),
            "modo": detail.mode,
            "ufi": detail.ufi,
            "top3": [
                {"family": c.family, "contribution_pct": round(c.contribution_pct, 1)}
                for c in top3
            ],
            "valores": detail.raw,
        },
        ensure_ascii=False,
    )


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

    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    try:
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
            messages=[{"role": "user", "content": _build_user_payload(detail)}],
        )
        return msg.content[0].text.strip()
    except Exception as exc:
        logger.warning("Anthropic API error, using fallback template: %s", exc)
        return _fallback_template(detail)


async def explain_stream(detail: BarrioDetail) -> AsyncIterator[str]:
    """Yields text chunks from Claude as they arrive. Falls back to full template on error.

    Also writes the full accumulated text to cache on success.
    """
    if settings.demo_offline or not settings.anthropic_api_key:
        yield _fallback_template(detail)
        return

    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    full_text = ""
    try:
        async with client.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": _build_user_payload(detail)}],
        ) as stream:
            async for chunk in stream.text_stream:
                full_text += chunk
                yield chunk
        key = f"explain:{_signature(detail)}"
        cache.put(key, full_text.strip(), EXPLAIN_TTL)
    except Exception as exc:
        logger.warning("Anthropic stream error, using fallback template: %s", exc)
        yield _fallback_template(detail)


def _fallback_template(detail: BarrioDetail) -> str:
    """Frase determinista cuando Claude no está disponible (demo offline o sin API key)."""
    top3 = sorted(detail.contribuciones, key=lambda c: -c.contribution_pct)[:3]
    _labels = {
        "trafico": "congestión de tráfico",
        "accidentes": "riesgo histórico de accidentes",
        "aire": "calidad del aire",
        "meteo": "condiciones meteorológicas",
        "sensibilidad": "densidad de puntos sensibles",
    }
    level = "alta" if detail.ufi >= 60 else "moderada" if detail.ufi >= 30 else "baja"
    hour = detail.at.strftime("%H:%M")
    if top3:
        main = _labels.get(top3[0].family, top3[0].family)
        second = (
            f" y {_labels.get(top3[1].family, top3[1].family)}"
            if len(top3) > 1 and top3[1].contribution_pct >= 15
            else ""
        )
        return (
            f"{detail.barrio_name} tendrá fricción urbana {level} a las {hour} "
            f"principalmente por {main}{second} (UFI {detail.ufi:.0f}/100)."
        )
    return f"{detail.barrio_name} presenta fricción urbana {level} a las {hour} (UFI {detail.ufi:.0f}/100)."
