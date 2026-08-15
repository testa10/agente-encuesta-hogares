"""El `Recolector` de `tools/validar_con_datos_reales.py`: junta todas las
fallas de una corrida en vez de cortar en la primera.

Nace del problema de fondo que tenía ese script: usaba `assert` sueltos,
así que la primera falla abortaba todo. Al cargar un año nuevo eso
obligaba a un ciclo de corregir → volver a correr → descubrir la
siguiente, un problema por corrida y varios minutos cada una — con los
datos de 2023 hicieron falta cuatro corridas completas para descubrir
cuatro problemas que ya estaban todos ahí desde la primera.

Se prueba acá y no corriendo el script de verdad porque ese necesita los
microdatos del INE, que no se versionan (ver data/README.md): en un clone
limpio, y en CI, no hay ningún año descargado.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

_RUTA = Path(__file__).resolve().parents[1] / "tools" / "validar_con_datos_reales.py"


def _cargar_modulo():
    """Importa el script de tools/ (que no es parte del paquete instalable)."""
    spec = importlib.util.spec_from_file_location("validar_con_datos_reales", _RUTA)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    return modulo


validar = _cargar_modulo()


class TestRecolector:
    def test_sigue_despues_de_una_falla_y_las_junta_todas(self):
        # El caso que motivó todo esto: tres problemas independientes
        # tienen que aparecer los tres en una sola corrida.
        rec = validar.Recolector()

        with rec.bloque("primero"):
            raise ValueError("algo salió mal")
        with rec.bloque("segundo"):
            assert False, "otra cosa distinta"
        with rec.bloque("tercero"):
            pass

        assert len(rec.fallas) == 2, "las dos fallas tienen que estar, no solo la primera"
        etiquetas = [e for e, _ in rec.fallas]
        assert etiquetas == ["primero", "segundo"]
        assert "algo salió mal" in rec.fallas[0][1]

    def test_un_bloque_que_pasa_no_registra_nada(self):
        rec = validar.Recolector()
        with rec.bloque("todo bien"):
            assert 1 + 1 == 2
        assert rec.fallas == []
        assert rec.omitidos == []

    def test_lo_que_depende_de_algo_que_fallo_queda_OMITIDO_y_no_FALLA(self):
        # Distinguirlos importa: si no, un solo problema real infla el
        # informe final con cinco "fallas" que en realidad son
        # consecuencias suyas, y se pierde cuál hay que arreglar.
        rec = validar.Recolector()
        hogares = None  # simula que su bloque falló antes

        with rec.bloque("dependiente"):
            rec.requiere(hogares=hogares)
            raise AssertionError("esto no debería llegar a ejecutarse")

        assert rec.fallas == [], "no es una falla nueva, es consecuencia de otra"
        assert len(rec.omitidos) == 1
        assert rec.omitidos[0][0] == "dependiente"
        assert "hogares" in rec.omitidos[0][1]

    def test_requiere_deja_pasar_cuando_todo_esta_disponible(self):
        rec = validar.Recolector()
        with rec.bloque("con todo"):
            rec.requiere(hogares="hay datos", personas="hay datos")
            paso = True
        assert paso is True
        assert rec.fallas == [] and rec.omitidos == []

    def test_informe_final_devuelve_1_si_hubo_fallas(self, capsys):
        rec = validar.Recolector()
        with rec.bloque("2030 · algo"):
            raise RuntimeError("se rompió")

        codigo = rec.informe_final(["2030"])

        assert codigo == 1, "el script tiene que salir con error para que se note en CI o a ojo"
        salida = capsys.readouterr().out
        assert "2030 · algo" in salida
        assert "se rompió" in salida

    def test_informe_final_devuelve_0_si_no_hubo_ninguna_falla(self, capsys):
        rec = validar.Recolector()
        with rec.bloque("2030 · algo"):
            pass

        codigo = rec.informe_final(["2030"])

        assert codigo == 0
        assert "VALIDACIÓN COMPLETA" in capsys.readouterr().out

    def test_los_omitidos_solos_no_hacen_fallar_la_corrida(self, capsys):
        # Un año sin un módulo de datos no es un error del proyecto.
        rec = validar.Recolector()
        with rec.bloque("2030 · depende de otra cosa"):
            rec.requiere(algo=None)

        assert rec.informe_final(["2030"]) == 0
        assert "VALIDACIÓN COMPLETA" in capsys.readouterr().out


def test_el_script_expone_las_funciones_que_usa_main():
    """Si alguna se renombra sin actualizar `main()`, esto lo detecta acá
    en vez de en una corrida real de varios minutos."""
    for nombre in ("validar_anio", "validar_notebook_builder", "main", "Recolector"):
        assert hasattr(validar, nombre), f"falta {nombre} en validar_con_datos_reales.py"


@pytest.mark.parametrize("funcion", ["_validar_fies", "_validar_empleo", "_validar_seguridad"])
def test_los_bloques_independientes_existen_como_funcion_propia(funcion):
    """FIES/Empleo/Seguridad se revisan siempre, incluso si todo lo demás
    falló — por eso viven en funciones aparte y no anidadas en el flujo
    principal."""
    assert hasattr(validar, funcion)
