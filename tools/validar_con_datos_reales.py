"""Uso: ./run_python.bat tools/validar_con_datos_reales.py

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

No se listan las 43 métricas del catálogo una por una — esa lista cambia
seguido y mantenerla sincronizada acá sería el mismo tipo de
comentario/lista que se desactualiza solo. En cambio, se invoca la
función de `analysis.py` que sostiene cada una contra datos reales
(muchas métricas comparten la misma función genérica con distinto
argumento de agrupación, así que son bastantes menos de 47 llamadas) y se
verifican invariantes genéricos (porcentajes entre 0 y 100, categorías
mutuamente excluyentes sumando ~100%, sin valores nulos donde no
corresponde) — no solo que el pipeline cargue sin explotar. Antes de esta
versión, 31 de las 47 métricas no tenían ninguna función real invocada
acá, y esa brecha no la detectaba ni la suite sintética ni "no tira
error": números mal calculados podían pasar sin que nada lo notara.
`test_verificacion_catalogo.py::test_toda_metrica_del_manifiesto_tiene_su_funcion_validada_con_datos_reales`
falla si en el futuro se agrega una métrica nueva al catálogo cuya
función no se ejercita en este archivo.

Si hay datos de FIES/Empleo/Seguridad para el año, también se ejercitan.
Si una columna específica de un año no está disponible (ej. situación
ocupacional en 2025), se avisa explícitamente que esa parte no se pudo
verificar en vez de saltearla en silencio.

Si no hay ningún año en data/, termina con un aviso claro en vez de
fallar — no es un error, es el estado normal de un clone limpio.
"""

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
warnings.filterwarnings("ignore")

import nbformat  # noqa: E402
import pandas as pd  # noqa: E402
from nbclient import NotebookClient  # noqa: E402
from nbclient.exceptions import CellExecutionError  # noqa: E402

from encuesta_hogares import (  # noqa: E402
    analysis,
    config,
    data_loader,
    notebook_builder,
    preprocessing,
    verificacion_catalogo,
    visualization,
)


def _cargar_hogares_y_personas(anio: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    carpeta = config.DATA_DIR / anio
    if config.hogares_csv_file(anio).exists():
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

    # --- Métrica 3: sin función de análisis propia hasta la corrida que agregó este manifiesto ---
    hogares_ext["calidad_conexion"] = preprocessing.clasificar_calidad_conexion(hogares_ext)
    calidad = analysis.calidad_conexion_por(hogares_ext, "nivel_economico")
    assert calidad.sum(axis=1).round(0).between(99, 101).all()
    assert visualization.plot_calidad_conexion_por(calidad, "nivel económico") is not None
    print("Calidad de conexión por nivel económico: OK (ponderado)")

    # --- Hogares: composición vía Personas, requiere el merge completo ---
    tipo_hogar = preprocessing.clasificar_tipo_hogar(personas, hogares)
    resumen_tipos = analysis.tipos_hogar_resumen(tipo_hogar)
    assert abs(resumen_tipos["pct_hogares"].sum() - 100.0) < 0.5
    jefatura = analysis.tasa_jefatura_femenina(tipo_hogar)
    assert 0 <= jefatura["pct_jefatura_femenina"] <= 100
    print(f"Tipos de hogar: OK ({len(resumen_tipos)} categorías) — jefatura femenina: {jefatura['pct_jefatura_femenina']}%")

    barrios_resumen = analysis.clasificacion_barrios_resumen(penetracion_barrio)
    assert barrios_resumen["cantidad_barrios"].sum() == len(penetracion_barrio)

    unipersonales_mayores = analysis.pct_unipersonales_mayores(tipo_hogar)
    assert 0 <= unipersonales_mayores["pct_unipersonales_mayores"] <= 100

    cat_a, cat_b = resumen_tipos["tipo_hogar"].iloc[0], resumen_tipos["tipo_hogar"].iloc[-1]
    diferencia_tipos = analysis.diferencia_entre_categorias(resumen_tipos, "tipo_hogar", cat_a, cat_b, "pct_hogares")
    assert -100 <= diferencia_tipos <= 100

    carencias_frecuentes = analysis.carencias_estructurales_mas_frecuentes(hogares_cond)
    assert carencias_frecuentes["pct_hogares"].between(0, 100).all() and len(carencias_frecuentes) == n_carencias
    print(
        "Barrios por nivel de suscripción / unipersonales mayores / diferencia entre tipos de hogar / "
        "carencias más frecuentes: OK"
    )

    # --- Brecha Digital por cohorte/jefatura/índice de acceso, Hacinamiento,
    # Razón de dependencia: necesitan columnas derivadas que se arman acá
    # mismo, siguiendo el mismo criterio que ya usa el notebook real.
    hogares_ext_con_jefe = hogares_ext.merge(
        tipo_hogar[["id_hogar", "jefe_sexo", "jefe_edad"]], on="id_hogar", how="left"
    )
    hogares_ext_con_jefe["cohorte"] = preprocessing.compute_cohorte_generacional(hogares_ext_con_jefe, int(anio))
    hogares_ext_con_jefe["indice_acceso_digital"] = preprocessing.compute_indice_acceso_digital(hogares_ext_con_jefe)

    brecha_cohorte = analysis.brecha_digital_por_cohorte(hogares_ext_con_jefe)
    assert brecha_cohorte["pct_penetracion"].between(0, 100).all()
    brecha_jefatura = analysis.brecha_digital_por_jefatura(hogares_ext_con_jefe)
    assert brecha_jefatura["pct_penetracion"].between(0, 100).all()
    indice_por_nivel = analysis.indice_acceso_digital_por(hogares_ext_con_jefe, "nivel_economico")
    assert indice_por_nivel["indice_promedio"].between(0, 4).all()
    if "tiene_tablet_ibirapita" in hogares_ext_con_jefe.columns:
        tablet_por_nivel = analysis.adopcion_tablet_ibirapita_por(hogares_ext_con_jefe, "nivel_economico")
        assert tablet_por_nivel["pct_con_tablet"].between(0, 100).all()
    print("Brecha digital por cohorte / jefatura / índice de acceso digital: OK (ponderado)")

    hogares_mdeo_hacinamiento = preprocessing.compute_hacinamiento(hogares_mdeo)
    hacinamiento_por_nivel = analysis.pct_hacinamiento_por(hogares_mdeo_hacinamiento, "nivel_economico")
    assert hacinamiento_por_nivel["pct_hacinamiento"].between(0, 100).all()
    print("Hacinamiento por nivel económico: OK")

    personas_con_depto = preprocessing.merge_personas(hogares, personas)
    dependencia_por_depto = analysis.razon_dependencia_por(personas_con_depto, "departamento")
    assert dependencia_por_depto["razon_dependencia"].dropna().ge(0).all()
    print(f"Razón de dependencia demográfica por departamento: OK ({len(dependencia_por_depto)} departamentos)")

    disponibles = config.datos_disponibles(anio)
    print(f"Datos opcionales disponibles: {disponibles}")

    if disponibles["fies"]:
        fies = data_loader.load_fies(config.fies_file(anio))
        fies_clasificado = preprocessing.prepare_fies(fies)
        prevalencia = analysis.prevalencia_inseguridad_alimentaria(fies_clasificado)
        assert 0 <= prevalencia["moderada_o_severa"] <= 100
        print(f"FIES: OK (inseguridad moderada o severa: {prevalencia['moderada_o_severa']}%)")

        inseguridad_por_region = analysis.inseguridad_alimentaria_por(fies_clasificado, "region")
        assert inseguridad_por_region["pct_inseguridad"].between(0, 100).all()
        print(f"FIES por región: OK ({len(inseguridad_por_region)} regiones)")

    if disponibles["empleo"]:
        empleo = preprocessing.prepare_empleo(data_loader.load_empleo(anio))
        assert empleo["mes"].nunique() == 12, "el panel de empleo tiene que traer los 12 meses"
        tasas = analysis.tasas_actividad_empleo_desempleo(empleo)
        assert 0 <= tasas["tasa_desempleo"] <= 100
        print(f"Empleo: OK (tasa de desempleo promedio anual: {tasas['tasa_desempleo']}%)")

        tasas_por_sexo = analysis.tasas_actividad_empleo_desempleo_por(empleo, "sexo_grupo")
        assert tasas_por_sexo[["tasa_actividad", "tasa_empleo", "tasa_desempleo"]].apply(
            lambda s: s.between(0, 100)
        ).all().all()
        sexos = tasas_por_sexo["sexo_grupo"].tolist()
        if len(sexos) >= 2:
            brecha_genero = analysis.brecha_por_grupo(tasas_por_sexo, "sexo_grupo", sexos[0], sexos[1])
            assert brecha_genero.abs().le(100).all()
        print("Empleo por sexo / brecha de género: OK")

        ocupados = empleo[empleo["condicion_actividad"] == "Ocupados"]
        if "es_informal" in ocupados.columns:
            informalidad_por_sexo = analysis.tasa_mensual_promedio_por(ocupados, "sexo_grupo", "es_informal")
            assert informalidad_por_sexo["pct_promedio"].between(0, 100).all()
            print("Informalidad por sexo: OK")
        else:
            print("Informalidad por sexo: sin verificar — 'es_informal' no está disponible este año")

        columna_sector = next((c for c in ("sit_ocup", "situacion_ocupacional") if c in ocupados.columns), None)
        if columna_sector:
            composicion_sector = analysis.composicion_categorica_por_mes_promedio(ocupados, "sexo_grupo", columna_sector)
            assert composicion_sector.sum(axis=1).round(0).between(99, 101).all()
            print("Situación ocupacional por sector y sexo: OK")
        else:
            print("Situación ocupacional por sector y sexo: sin verificar — columna no disponible este año")

    if disponibles["seguridad"]:
        victimizacion = data_loader.load_victimizacion(anio)
        largo = preprocessing.melt_delitos(preprocessing.prepare_victimizacion(victimizacion))
        assert len(largo) > 0
        print(f"Seguridad/Victimización: OK ({len(largo)} filas tipo_delito x persona)")

        victimizados = largo[largo["victimizado"]]
        comunicacion_por_delito = analysis.pct_ponderado_por(
            victimizados, "tipo_delito", "comunicacion_policia", "ponderador_victimizacion"
        )
        assert comunicacion_por_delito["pct"].between(0, 100).all()
        denuncia_por_delito = analysis.pct_ponderado_por(
            victimizados, "tipo_delito", "denuncia_formal", "ponderador_victimizacion"
        )
        assert denuncia_por_delito["pct"].between(0, 100).all()
        diferencia_comunicacion_denuncia = analysis.diferencia_entre_tablas(
            comunicacion_por_delito, denuncia_por_delito, "tipo_delito", "pct"
        )
        assert diferencia_comunicacion_denuncia.abs().le(100).all()
        print(f"Comunicación a la policía vs. denuncia formal, por tipo de delito: OK ({len(comunicacion_por_delito)} tipos)")

    print(f"\n[OK] Año {anio}: validación completa sin errores")


def validar_notebook_builder(anio: str) -> None:
    """Corre DE VERDAD el código que genera `notebook_builder.py` para
    todas las métricas del catálogo disponibles este año (no una
    reimplementación a mano de la misma lógica, como el resto de este
    archivo) — así, si una plantilla queda desincronizada de
    `analysis.py`/`visualization.py` (un parámetro renombrado, una
    función que ya no existe), esto revienta acá, en un chequeo que ya es
    parte del flujo esperado antes de publicar, no en un informe real de
    un usuario.

    Nace de la misma revisión que agregó `notebook_builder.py`: con solo
    un test de que "cada número del catálogo tiene una función" (ver
    `test_notebook_builder.py`) no alcanza — ese test no ejecuta nada
    contra datos reales, y un año concreto le faltaba una columna que
    otro sí tenía (ver SIT_OCUP/SECTOR_F más abajo). Solo cubre el año
    base — la comparación entre años quedó en código libre (ver el
    docstring de notebook_builder.py), no hay una plantilla que probar
    para eso acá.
    """
    print(f"\n--- notebook_builder: ejecutando las plantillas del catálogo para {anio} ---")
    disponibles = config.datos_disponibles(anio)
    catalogo = verificacion_catalogo.numeros_del_catalogo()
    no_disponibles_empleo = set(verificacion_catalogo.metricas_empleo_no_disponibles(anio))
    metricas = sorted(n for n in catalogo if n not in no_disponibles_empleo)
    if not disponibles["fies"]:
        metricas = [n for n in metricas if n not in range(22, 29)]
    if not disponibles["empleo"]:
        metricas = [n for n in metricas if n not in range(29, 37)]
    if not disponibles["seguridad"]:
        metricas = [n for n in metricas if n not in range(37, 44)]

    celdas = notebook_builder.construir_celdas_notebook(
        anio_base=int(anio),
        metricas=metricas,
        incluir_brecha_digital=True,
        incluir_fies=disponibles["fies"],
        incluir_empleo=disponibles["empleo"],
        incluir_seguridad=disponibles["seguridad"],
    )

    # Se ejecuta con un kernel de Jupyter de verdad (nbclient), no exec()
    # crudo en este mismo proceso: `fig.show()` de Plotly depende de los
    # hooks de display de IPython para renderizar — fuera de un kernel
    # real, cae a un camino distinto (print de HTML crudo a la consola)
    # que no es el que corre en un notebook real y que además puede
    # fallar por la codificación de la consola sin que sea un error de
    # verdad de la plantilla.
    ruta_tmp = config.PROJECT_ROOT / "notebooks" / f"_validacion_notebook_builder_{anio}.ipynb"
    notebook_builder.escribir_notebook(celdas, ruta_tmp)
    nb = nbformat.read(str(ruta_tmp), as_version=4)
    try:
        NotebookClient(nb, timeout=180, kernel_name="python3").execute()
    except CellExecutionError as e:
        raise AssertionError(f"notebook_builder rompió ejecutando el notebook de prueba para {anio}: {e}") from e
    finally:
        ruta_tmp.unlink(missing_ok=True)
        Path(str(ruta_tmp).replace(".ipynb", " (anterior).ipynb")).unlink(missing_ok=True)

    print(f"[OK] {len(metricas)} métricas del catálogo, plantillas ejecutadas sin error ({len(celdas)} celdas)")


def main() -> int:
    anios = sorted(p.name for p in config.DATA_DIR.iterdir() if p.is_dir() and p.name.isdigit()) if config.DATA_DIR.exists() else []
    anios = [a for a in anios if list((config.DATA_DIR / a).glob("H_*.sav")) or config.hogares_csv_file(a).exists()]

    if not anios:
        print("No hay datos en data/ todavía — no es un error, es el estado normal de un clone limpio.")
        print("Este script solo tiene sentido correrlo una vez que haya al menos un año descargado.")
        return 0

    for anio in anios:
        validar_anio(anio)

    for anio in anios:
        validar_notebook_builder(anio)

    print(f"\n\n[OK] VALIDACIÓN COMPLETA: {', '.join(anios)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
