"""Uso: ./run_python.bat tools/resumen_sesiones.py

Lee logs/bitacora.jsonl (si existe) y muestra un resumen legible de cada
sesión detectada: cuándo empezó y terminó, cuántos formularios se
mostraron, si hubo timeouts o errores, y cuánto tardó cada paso pesado
medido con bitacora.medir()/medir_comando() (carga de datos, ejecución
del notebook, conversión a PDF) - ordenado de mayor a menor duración,
para ver de un vistazo dónde se fue el tiempo de la corrida.

Pensado para cuando alguien sin conocimientos técnicos reporta que "algo
no funcionó": en vez de depender de que describa bien lo que vio, pedile
el archivo logs/bitacora.jsonl de su computadora y corré esto para
reconstruir la sesión con datos objetivos en vez de una descripción de
memoria.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from encuesta_hogares import bitacora  # noqa: E402


def main() -> None:
    eventos = bitacora.leer_eventos()
    if not eventos:
        print(f"No hay eventos registrados todavía en {bitacora.LOG_PATH}")
        return

    sesiones = bitacora.agrupar_en_sesiones(eventos)
    print(f"{len(sesiones)} sesión(es) encontradas en {bitacora.LOG_PATH}\n")
    for i, eventos_sesion in enumerate(sesiones, start=1):
        r = bitacora.resumir_sesion(eventos_sesion)
        print(f"Sesión {i}: {r.inicio} -> {r.fin}")
        print(
            f"  formularios mostrados: {r.formularios_mostrados}, "
            f"timeouts: {r.timeouts}, errores: {len(r.errores)}"
        )
        for err in r.errores:
            print(f"    [{err['timestamp']}] {err['tipo']}: {err.get('mensaje', '')}")
        if r.pasos_medidos:
            print("  pasos medidos (de mayor a menor duración):")
            for paso in r.pasos_medidos:
                print(f"    {paso['nombre']}: {paso['duracion_segundos']}s")
        print()


if __name__ == "__main__":
    main()
