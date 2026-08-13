"""Uso: run_python.bat tools/validar_con_datos_reales.py

Corre un chequeo de humo (smoke test) contra los datos reales que haya en
data/{año}/ — uno por cada año disponible. No reemplaza a la suite de
tests (que usa dataframes sintéticos y corre siempre, incluso sin datos);
existe porque varios bugs reales de esta sesión NO los detectaron los
tests sintéticos y solo aparecieron contra datos de verdad:

- la cantidad de columnas de condiciones de vivienda cambia de 12 (2019)
  a 4 (2024) — un test sintético que arma el dataframe a mano no
  reproduce ese recorte real si no se acuerda de hacerlo a propósito.
- el formato de archivo cambia de .sav (hasta 2023) a .csv combinado
  (2024 en adelante) — dos loaders distintos, cada uno con su propia
  forma de romperse.
- funciones que necesitan la base **nacional** completa (departamento,
  19 categorías) en vez de la base filtrada a Montevideo — fácil de
  confundir, y un dataframe sintético de prueba no distingue una de otra
  si no se arma con cuidado.

No se prueban las 47 métricas del catálogo una por una a propósito —esa
lista cambia seguido y mantenerla sincronizada acá sería el mismo tipo de
comentario/lista que se desactualiza solo. En cambio, este script ejercita
el pipeline completo (carga → preprocesamiento → una función real de cada
bloque temático que toca datos nacionales) para las categorías de riesgo
de arriba. Si hay datos de FIES/Empleo/Seguridad para el año, también se
ejercitan.

Si no hay ningún año en data/, termina con un aviso claro en vez de
fallar — no es un error, es el estado normal de un clone limpio.
"""

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
warnings.filterwarnings("ignore")

import pandas as pd  # noqa: E402

from encuesta_hogares import analysis, config, data_loader, preprocessing, visualization  # noqa: E402


def _cargar_hogares_y_personas(anio: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    carpeta = config.DATA_DIR / anio
    if list(carpeta.glob(f"ECH_{anio}.csv")):
        return data_loader.load_hogares_personas_csv(anio)
    h_path = sorted(carpeta.glob("H_*.sav"))[0]
    p_path = sorted(carpeta.glob("P_*.sav"))[0]
    return data_loader.load_hogares(h_path), data_loader.load_personas(p_path)


def validar_anio(anio: str) -> None:
    print(f"\n{'=' * 60}\nAÑO {anio}\n{'=' * 60}")
    hogares, personas = _cargar_hogares_y_personas(anio)
    print(f"Hogares (nacional): {len(hogares)} — departamentos: {hogares['departamento'].nunique()}")
    assert hogares["departamento"].nunique() > 1, "se esperaban varios departamentos en la base nacional"

    # --- Vivienda: la cantidad de carencias cambia de año a año ---
    hogares_cond = preprocessing.decode_condiciones_vivienda(hogares)
    n_carencias = sum(1 for c in config.CONDICIONES_VIVIENDA_COLUMNS.values() if c in hogares_cond.columns)
    print(f"Carencias de vivienda disponibles: {n_carencias}")
    assert n_carencias > 0, "ningún año debería quedarse sin ninguna columna de vivienda"
    resultado = analysis.precariedad_estructural(hogares_cond)
    assert 0 <= resultado["pct_con_carencia"] <= 100
    assert visualization.plot_precariedad_estructural(resultado) is not None

    # --- Territorio: índice compuesto sobre la base nacional (no Montevideo) ---
    hogares_cond["pobre"] = hogares_cond["pobre"] == 1.0
    pobreza_depto = analysis.pct_pobres_por(hogares_cond, "departamento").set_index("departamento")
    estrato_depto = analysis.estrato_promedio_por(hogares, "departamento").set_index("departamento")
    precariedad_depto = analysis.precariedad_estructural_por(hogares_cond, "departamento").set_index("departamento")
    componentes = pd.DataFrame({
        "pct_pobreza": pobreza_depto["pct_pobres"],
        "pct_precariedad": precariedad_depto["pct_precariedad"],
        "estrato_promedio": estrato_depto["estrato_promedio"],
    }).dropna()
    indice = analysis.indice_desarrollo_territorial(componentes, invertir=["pct_pobreza", "pct_precariedad"])
    assert indice["indice"].between(0, 1).all()
    assert visualization.plot_indice_desarrollo_territorial(indice) is not None
    print(f"Índice territorial: OK ({len(indice)} departamentos)")

    # --- Brecha Digital / Hogares: filtro a Montevideo + variables decodificadas ---
    hogares_mdeo = preprocessing.prepare_hogares_montevideo(hogares)
    hogares_ext = preprocessing.prepare_hogares_extendido(hogares_mdeo)
    resumen_conectividad = analysis.resumen_conectividad(hogares_ext)
    assert resumen_conectividad.total_hogares > 0
    assert 0 <= resumen_conectividad.pct_con_cable <= 100
    print(f"Montevideo: {resumen_conectividad.total_hogares} hogares, {resumen_conectividad.pct_con_cable}% con cable (ponderado)")

    pobres = analysis.pct_pobres_indigentes(hogares_ext)
    assert 0 <= pobres["pct_pobres"] <= 100
    print(f"Pobreza (ponderada): {pobres['pct_pobres']}% — sin ponderar sería {round(hogares_ext['pobre'].mean() * 100, 2)}%")

    brecha = analysis.brecha_digital_por_nivel_economico(hogares_ext)
    assert visualization.plot_brecha_digital(brecha) is not None

    penetracion_barrio = preprocessing.compute_penetracion_por_barrio(hogares_mdeo)
    assert penetracion_barrio["pct_abonados"].between(0, 100).all()
    print(f"Penetración por barrio: OK ({len(penetracion_barrio)} barrios, ponderado)")

    penetracion_nacional = preprocessing.compute_penetracion_nacional(hogares)
    assert penetracion_nacional["pct_cable"].between(0, 100).all()
    print(f"Penetración nacional por departamento: OK ({len(penetracion_nacional)} departamentos, ponderado)")

    # --- Métricas 3, 9, 11: sin función de análisis propia hasta esta corrida ---
    hogares_ext["calidad_conexion"] = preprocessing.clasificar_calidad_conexion(hogares_ext)
    calidad = analysis.calidad_conexion_por(hogares_ext, "nivel_economico")
    assert calidad.sum(axis=1).round(0).between(99, 101).all()
    assert visualization.plot_calidad_conexion_por(calidad, "nivel económico") is not None

    hogares_abonados = preprocessing.merge_penetracion(hogares_mdeo, penetracion_barrio)
    suscripcion_vs_economico = analysis.suscripcion_vs_nivel_economico(hogares_abonados)
    assert visualization.plot_heatmap_suscripcion_vs_economico(suscripcion_vs_economico) is not None

    streaming = analysis.streaming_vs_cable(hogares_ext)
    assert visualization.plot_streaming_vs_cable(streaming) is not None
    print("Calidad de conexión / suscripción vs. nivel económico / streaming vs. cable: OK (ponderado)")

    # --- Hogares: composición vía Personas, requiere el merge completo ---
    tipo_hogar = preprocessing.clasificar_tipo_hogar(personas, hogares)
    resumen_tipos = analysis.tipos_hogar_resumen(tipo_hogar)
    assert abs(resumen_tipos["pct_hogares"].sum() - 100.0) < 0.5
    jefatura = analysis.tasa_jefatura_femenina(tipo_hogar)
    assert 0 <= jefatura["pct_jefatura_femenina"] <= 100
    print(f"Tipos de hogar: OK ({len(resumen_tipos)} categorías) — jefatura femenina: {jefatura['pct_jefatura_femenina']}%")

    disponibles = config.datos_disponibles(anio)
    print(f"Datos opcionales disponibles: {disponibles}")

    if disponibles["fies"]:
        fies = data_loader.load_fies(config.fies_file(anio))
        fies_clasificado = preprocessing.prepare_fies(fies)
        prevalencia = analysis.prevalencia_inseguridad_alimentaria(fies_clasificado)
        assert 0 <= prevalencia["moderada_o_severa"] <= 100
        print(f"FIES: OK (inseguridad moderada o severa: {prevalencia['moderada_o_severa']}%)")

    if disponibles["empleo"]:
        empleo = preprocessing.prepare_empleo(data_loader.load_empleo(anio))
        assert empleo["mes"].nunique() == 12, "el panel de empleo tiene que traer los 12 meses"
        tasas = analysis.tasas_actividad_empleo_desempleo(empleo)
        assert 0 <= tasas["tasa_desempleo"] <= 100
        print(f"Empleo: OK (tasa de desempleo promedio anual: {tasas['tasa_desempleo']}%)")

    if disponibles["seguridad"]:
        victimizacion = data_loader.load_victimizacion(anio)
        largo = preprocessing.melt_delitos(preprocessing.prepare_victimizacion(victimizacion))
        assert len(largo) > 0
        print(f"Seguridad/Victimización: OK ({len(largo)} filas tipo_delito x persona)")

    print(f"\n[OK] Año {anio}: validación completa sin errores")


def main() -> int:
    anios = sorted(p.name for p in config.DATA_DIR.iterdir() if p.is_dir() and p.name.isdigit()) if config.DATA_DIR.exists() else []
    anios = [a for a in anios if list((config.DATA_DIR / a).glob("H_*.sav")) or list((config.DATA_DIR / a).glob(f"ECH_{a}.csv"))]

    if not anios:
        print("No hay datos en data/ todavía — no es un error, es el estado normal de un clone limpio.")
        print("Este script solo tiene sentido correrlo una vez que haya al menos un año descargado.")
        return 0

    for anio in anios:
        validar_anio(anio)

    print(f"\n\n[OK] VALIDACIÓN COMPLETA: {', '.join(anios)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
