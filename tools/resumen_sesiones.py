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

También es donde aparecen las sugerencias que el agente fue dejando
sobre métricas a medida que valdría la pena incorporar al catálogo
permanente (`bitacora.sugerir_catalogo`, paso 6.5 del agente) — nunca se
las pregunta a la persona en el momento (esa consola corre en segundo
plano y casi nadie la abre), quedan acá para que el dueño del proyecto
las revise cuando tenga tiempo.
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
        if r.sugerencias_catalogo:
            print("  sugerencias para el catálogo permanente (ver 'Curación del catálogo'):")
            for s in r.sugerencias_catalogo:
                print(f"    - {s.get('metrica', '?')}: {s.get('motivo', '')}")
        if r.reejecuciones:
            print("  re-ejecuciones del notebook (cada una cuesta ~2 min — si un motivo se repite entre sesiones, es un defecto del builder a arreglar):")
            for re_ejec in r.reejecuciones:
                print(f"    - [{re_ejec['timestamp']}] {re_ejec.get('motivo', 'sin motivo registrado')}")
        if r.pasos_medidos:
            print("  pasos medidos (de mayor a menor duración):")
            for paso in r.pasos_medidos:
                print(f"    {paso['nombre']}: {paso['duracion_segundos']}s")
        if r.checkpoints_paso5:
            print("  paso 5 (construir el informe) - puntos de control:")
            for cp in r.checkpoints_paso5:
                if cp["segundos_desde_el_anterior"] is None:
                    print(f"    {cp['etapa']}")
                else:
                    print(f"    +{cp['segundos_desde_el_anterior']}s  {cp['etapa']}")
        print()


if __name__ == "__main__":
    main()
