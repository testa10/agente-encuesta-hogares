"""Configuración: rutas, nombres de archivo y mapeos de clasificación.

Los nombres de columna (HOGARES_COLUMNS, PERSONAS_COLUMNS,
CONDICIONES_VIVIENDA_COLUMNS) reflejan los códigos de variable de la ECH 2019.
Antes de usar datos de otro año, el agente (ver .claude/agents/narrativa-datos.md)
verifica con pyreadstat que esos códigos sigan existiendo y con el mismo
significado; si algo cambió, actualiza este archivo y lo deja documentado en
docs/METODOLOGIA.md.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


def _resolve_data_file(prefix: str, fallback_name: str) -> Path:
    """Busca en data/ el archivo más reciente que siga la convención de
    nombres del INE (ej. H_2024_Terceros.sav). Si hay más de un año
    disponible, usa el más nuevo. Si no hay ninguno todavía, devuelve una
    ruta de referencia (no falla al importar el módulo, solo al intentar
    leer el archivo).
    """
    candidatos = sorted(DATA_DIR.glob(f"{prefix}_*.sav"))
    return candidatos[-1] if candidatos else DATA_DIR / fallback_name


HOGARES_FILE = _resolve_data_file("H", "H_AAAA.sav")
PERSONAS_FILE = _resolve_data_file("P", "P_AAAA.sav")

# Columnas relevantes de la base de Hogares (H) y su nuevo nombre legible
HOGARES_COLUMNS = {
    "numero": "id_hogar",
    "nomdpto": "departamento",
    "nombarrio": "barrio",
    "d21_7": "tipo_abonado",     # 1 = con cable, 2 = sin cable
    "estred13": "estrato_tipo",  # estrato socioeconómico 1 (bajo) a 5 (alto)
    "d25": "total_personas",
    # --- Ampliación: brecha digital, pobreza e ingresos del hogar ---
    "d21_16": "tiene_internet",       # 1=Sí/2=No/99=Sin dato
    "d21_16_1": "internet_fija",
    "d21_16_2": "internet_movil",
    "d21_15": "tiene_pc",
    "d21_21": "tiene_streaming",
    "pobre06": "pobre",               # 0=No pobre, 1=Pobre
    "indigente06": "indigente",       # 0=No indigente, 1=Indigente
    "YSVL": "ingreso_hogar",          # ingreso del hogar sin valor locativo
    "ht3": "menores_14",
    "ht5": "ocupados_hogar",
}

# Variables de estado estructural de la vivienda (todas 1=Sí/2=No/99=Sin dato).
CONDICIONES_VIVIENDA_COLUMNS = {
    "c5_1": "humedad_techos",
    "c5_2": "goteras",
    "c5_3": "muros_agrietados",
    "c5_4": "puertas_ventanas_deterioradas",
    "c5_5": "grietas_pisos",
    "c5_6": "caida_revoque",
    "c5_7": "cielorraso_desprendido",
    "c5_8": "poca_luz_solar",
    "c5_9": "escasa_ventilacion",
    "c5_10": "se_inunda",
    "c5_11": "peligro_derrumbe",
    "c5_12": "humedad_cimientos",
}
HOGARES_COLUMNS.update(CONDICIONES_VIVIENDA_COLUMNS)

# Columnas relevantes de la base de Personas (P) y su nuevo nombre legible
PERSONAS_COLUMNS = {
    "numero": "id_hogar",
    "nper": "id_persona",
    "e26": "sexo",
    "e27": "edad",
    "PT1": "ingresos_personales",
    "pobpcoac": "condicion_actividad_cod",
    "e60": "tiene_celular_persona",  # 1=Sí/2=No/99=Sin dato
}

TIPO_ABONADO_LABELS = {1.0: "Con cable", 2.0: "Sin cable"}

NIVEL_ECONOMICO_LABELS = {
    1: "1-Bajo",
    2: "2-Medio-Bajo",
    3: "3-Medio",
    4: "4-Medio-Alto",
    5: "5-Alto",
}
NIVEL_ECONOMICO_DEFAULT = "6-No Definido"

SEXO_LABELS = {1: "1-Hombre", 2: "2-Mujer"}
SEXO_DEFAULT = "3-Otro"

EDAD_BINS = [0, 15, 65, float("inf")]
EDAD_LABELS = ["1-Niños-Jovenes", "2-Adultos", "3-Adultos_mayores"]

NIVEL_SUSCRIPCION_LABELS = ["1-Baja", "2-Media-Baja", "3-Media-Alta", "4-Alta"]

# Corrige un problema de codificación presente en las etiquetas de barrio del
# archivo .sav original: el caracter 'ñ' puede quedar guardado como '¦' (U+00A6).
MOJIBAKE_FIX = {"¦": "ñ"}

# Variables 1=Sí/2=No/99=Sin dato -> booleano (99 queda como NaN, no se asume).
SI_NO_MAP = {1.0: True, 2.0: False}

TECNOLOGIAS_LABELS = {
    "tiene_cable": "TV Cable",
    "tiene_internet": "Internet",
    "tiene_pc": "Computadora",
    "tiene_streaming": "Streaming",
}

# pobpcoac (Población por condición de actividad) colapsado a 3 grupos.
# La categoría 1 (Menores de 14 años) se excluye: no aplica a la fuerza laboral.
POBPCOAC_GRUPOS = {
    2.0: "Ocupados",
    3.0: "Desocupados",
    4.0: "Desocupados",
    5.0: "Desocupados",
    6.0: "Inactivos",
    7.0: "Inactivos",
    8.0: "Inactivos",
    9.0: "Inactivos",
    10.0: "Inactivos",
    11.0: "Inactivos",
}

CONDICION_VIVIENDA_LABELS = {
    "humedad_techos": "Humedad en techos",
    "goteras": "Goteras en techos",
    "muros_agrietados": "Muros agrietados",
    "puertas_ventanas_deterioradas": "Puertas/ventanas en mal estado",
    "grietas_pisos": "Grietas en pisos",
    "caida_revoque": "Caída de revoque",
    "cielorraso_desprendido": "Cielorrasos desprendidos",
    "poca_luz_solar": "Poca luz solar",
    "escasa_ventilacion": "Escasa ventilación",
    "se_inunda": "Se inunda cuando llueve",
    "peligro_derrumbe": "Peligro de derrumbe",
    "humedad_cimientos": "Humedad en cimientos",
}
