"""Uso: ./run_python.bat tools/verificar_estructura_datos.py <anio>

Compara los archivos de datos de un año (data/{año}/...) contra las
columnas que config.py espera para Hogares, Personas, FIES, Empleo y
Seguridad/Victimización, y reporta:

- columnas que el código necesita y no están en el archivo (rompe algo -
  hay que revisar el diccionario de datos oficial del INE para ese año y
  actualizar config.py si el formato cambió de verdad).
- columnas del archivo que config.py todavía no usa (informativo, no es
  un error).
- para Empleo, además, si algún mes del panel tiene columnas distintas a
  los demás (rompería el promedio mes a mes sin que nadie lo note).

Pensado para correrse apenas se agregan los archivos de un año nuevo,
antes de arrancar cualquier análisis - así un cambio de formato del INE
se detecta en segundos, no en media hora de conversación a los tumbos
como pasó con el salto de 2019 (.sav) a 2024 (CSV combinado).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from encuesta_hogares import verificacion_estructura as ve  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: ./run_python.bat tools/verificar_estructura_datos.py <anio>")
        sys.exit(1)

    anio = sys.argv[1]
    resultados = ve.verificar_anio(anio)
    if not resultados:
        print(f"No se encontró ningún archivo de datos para el año {anio} en data/{anio}/")
        sys.exit(1)

    hubo_problema = False
    for r in resultados:
        estado = "OK" if r.ok else "FALTAN COLUMNAS"
        print(f"\n{r.nombre} [{estado}]")
        print(f"  archivo: {r.archivo}")
        if r.faltantes:
            hubo_problema = True
            print(f"  faltan {len(r.faltantes)} columnas que el código espera: {r.faltantes}")
        if r.no_mapeadas:
            muestra = r.no_mapeadas[:10]
            extra = f" (+{len(r.no_mapeadas) - 10} más)" if len(r.no_mapeadas) > 10 else ""
            print(f"  columnas del archivo sin usar todavía ({len(r.no_mapeadas)}): {muestra}{extra}")

    print()
    if hubo_problema:
        print(
            "Hay columnas esperadas que no aparecen - revisá el diccionario de "
            "datos oficial del INE para ese año antes de correr cualquier "
            "análisis, y actualizá config.py si el formato cambió de verdad."
        )
        sys.exit(1)

    print("Todas las columnas esperadas están presentes.")


if __name__ == "__main__":
    main()
