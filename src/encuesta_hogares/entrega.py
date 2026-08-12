"""Utilidades para la entrega final del informe: no perder en silencio un
informe generado antes cuando se vuelve a correr el mismo año.

Nace de un hueco real: `notebooks/Informe_ECH_{año}.*` y la copia en
Descargas siempre tienen el mismo nombre - volver a correr el mismo año
(por error, o para probar otra selección de métricas) pisaba el
resultado anterior sin ningún aviso ni forma de recuperarlo.
"""

from __future__ import annotations

from pathlib import Path


def respaldar_si_existe(ruta: Path | str) -> Path | None:
    """Si ya existe un archivo en `ruta`, lo renombra a "<nombre> (anterior)"
    antes de que el llamador lo sobrescriba. Guarda una sola versión
    anterior (no acumula historial infinito): si ya había un "(anterior)"
    de una corrida más vieja todavía, se reemplaza por este. Devuelve la
    ruta del respaldo, o `None` si no había nada que respaldar."""
    ruta = Path(ruta)
    if not ruta.exists():
        return None
    respaldo = ruta.with_name(f"{ruta.stem} (anterior){ruta.suffix}")
    respaldo.unlink(missing_ok=True)
    ruta.rename(respaldo)
    return respaldo
