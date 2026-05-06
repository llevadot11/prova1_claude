from app.schemas import ModePreset

MODES: dict[str, ModePreset] = {
    "default": ModePreset(
        id="default",
        label="Por defecto",
        description="Equilibrio general entre tráfico, aire, meteo, accidentes y sensibilidad.",
        weights={
            "trafico": 0.30,
            "accidentes": 0.25,
            "aire": 0.20,
            "meteo": 0.15,
            "sensibilidad": 0.10,
        },
    ),
    "familiar": ModePreset(
        id="familiar",
        label="Familiar",
        description="Pondera más la calidad del aire y los entornos con colegios y hospitales.",
        weights={
            "trafico": 0.20,
            "accidentes": 0.20,
            "aire": 0.30,
            "meteo": 0.10,
            "sensibilidad": 0.20,
        },
    ),
    "runner": ModePreset(
        id="runner",
        label="Runner",
        description="Maximiza el peso del aire y meteo (calor, viento) y minimiza el tráfico.",
        weights={
            "trafico": 0.10,
            "accidentes": 0.15,
            "aire": 0.40,
            "meteo": 0.30,
            "sensibilidad": 0.05,
        },
    ),
    "movilidad_reducida": ModePreset(
        id="movilidad_reducida",
        label="Movilidad reducida",
        description="Pondera densidad de tráfico, calidad del aire y proximidad a hospitales.",
        weights={
            "trafico": 0.30,
            "accidentes": 0.20,
            "aire": 0.20,
            "meteo": 0.10,
            "sensibilidad": 0.20,
        },
    ),
}
