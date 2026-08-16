"""Que el informe no pueda decir un disparate.

Nace de una preocupación del dueño del proyecto: que un número no pueda
diferir de la realidad sin que nadie lo note. **No se trata de reproducir
los cálculos del INE** —la metodología de este proyecto puede diferir
legítimamente— sino de que un error grueso nunca llegue a un informe.

El punto ciego que cierra: hasta ahora los chequeos verificaban que un
porcentaje estuviera entre 0 y 100, y eso deja pasar casi cualquier error
real. Una tasa de desempleo de 45%, una pobreza de 0,14% (proporción
confundida con porcentaje) o una tasa de empleo mayor que la de actividad
son todas "porcentajes válidos" y todas imposibles.
"""

from encuesta_hogares import verificacion_plausibilidad as vp


class TestIdentidades:
    """Relaciones que se cumplen SIEMPRE, por definición. Una violación es
    un bug seguro, no una diferencia metodológica — y no dependen de
    ninguna cifra externa."""

    def test_el_empleo_no_puede_superar_a_la_actividad(self):
        hallazgos = vp.incoherencias({"tasa_actividad": 64.0, "tasa_empleo": 70.0})
        assert hallazgos, "los ocupados son un subconjunto de los activos"
        assert "tasa_empleo" == hallazgos[0].indicador

    def test_las_tres_tasas_tienen_que_cerrar_entre_si(self):
        # actividad 64, empleo 59.5 -> desempleo tiene que dar ~7.03
        hallazgos = vp.incoherencias({
            "tasa_actividad": 64.0, "tasa_empleo": 59.5, "tasa_desempleo": 20.0,
        })
        assert hallazgos, "un desempleo que no cierra con actividad y empleo es un bug"
        assert "denominador" in hallazgos[0].motivo

    def test_las_tres_tasas_reales_del_ine_cierran(self):
        # Cifras publicadas por el INE: actividad 64.4, empleo 59.5,
        # desempleo 7.6. Tienen que pasar sin observaciones.
        assert vp.incoherencias({
            "tasa_actividad": 64.4, "tasa_empleo": 59.5, "tasa_desempleo": 7.6,
        }) == []

    def test_la_indigencia_no_puede_superar_a_la_pobreza(self):
        hallazgos = vp.incoherencias({"pct_pobres": 12.0, "pct_indigentes": 20.0})
        assert hallazgos and hallazgos[0].indicador == "pct_indigentes"

    def test_la_inseguridad_severa_no_puede_superar_a_la_total(self):
        hallazgos = vp.incoherencias({
            "pct_inseguridad_alimentaria": 12.0, "pct_inseguridad_severa": 15.0,
        })
        assert hallazgos and hallazgos[0].indicador == "pct_inseguridad_severa"

    def test_no_inventa_problemas_con_cifras_coherentes(self):
        assert vp.incoherencias({
            "pct_pobres": 14.14, "pct_indigentes": 0.8,
            "pct_inseguridad_alimentaria": 11.95, "pct_inseguridad_severa": 2.1,
        }) == []


class TestPlausibilidad:
    def test_atrapa_una_proporcion_confundida_con_porcentaje(self):
        # El error clásico: 0.0745 en vez de 7.45.
        assert vp.fuera_de_rango("tasa_desempleo", 0.0745) is not None

    def test_atrapa_un_desempleo_disparatado(self):
        assert vp.fuera_de_rango("tasa_desempleo", 45.0) is not None

    def test_atrapa_un_calculo_que_dio_cero(self):
        # Un cruce vacío o una columna equivocada suelen dar 0.
        assert vp.fuera_de_rango("pct_pobres", 0.0) is not None

    def test_acepta_las_cifras_reales_de_este_proyecto(self):
        """Los valores que de verdad calcula el proyecto contra los datos
        del INE tienen que pasar — un falso positivo acá trabaría un
        informe correcto, que es peor que el problema que se quiere evitar."""
        reales = {
            "tasa_desempleo": 8.18,      # 2024
            "pct_pobres": 14.14,          # 2025
            "pct_inseguridad_alimentaria": 11.95,  # 2025
            "pct_con_internet": 89.1,     # 2025, Montevideo
            "pct_informalidad": 21.94,    # 2025, calculado desde f82
        }
        for indicador, valor in reales.items():
            assert vp.fuera_de_rango(indicador, valor) is None, (
                f"{indicador}={valor} es un valor real de este proyecto y no puede marcarse"
            )

    def test_acepta_las_cifras_publicadas_por_el_ine(self):
        publicadas = {
            "tasa_actividad": 64.4,
            "tasa_empleo": 59.5,
            "tasa_desempleo": 7.0,
            "pct_informalidad": 22.8,
        }
        for indicador, valor in publicadas.items():
            assert vp.fuera_de_rango(indicador, valor) is None

    def test_no_opina_sobre_un_indicador_sin_rango_definido(self):
        """Mejor no opinar que opinar mal: si nadie definió un rango, no se
        inventa uno."""
        assert vp.fuera_de_rango("indicador_que_no_existe", 12345.0) is None

    def test_ignora_un_valor_ausente(self):
        assert vp.fuera_de_rango("tasa_desempleo", None) is None


class TestRevisarJunta:
    def test_devuelve_las_dos_capas(self):
        hallazgos = vp.revisar({
            "tasa_actividad": 64.0, "tasa_empleo": 70.0,  # identidad rota
            "pct_pobres": 0.14,                            # además, disparate
        })
        indicadores = {h.indicador for h in hallazgos}
        assert "tasa_empleo" in indicadores
        assert "pct_pobres" in indicadores

    def test_una_corrida_sana_no_reporta_nada(self):
        assert vp.revisar({
            "tasa_actividad": 64.4, "tasa_empleo": 59.5, "tasa_desempleo": 7.6,
            "pct_pobres": 14.14, "pct_indigentes": 0.8,
        }) == []


def test_todo_rango_tiene_su_justificacion_escrita():
    """Un rango sin motivo es una opinión disfrazada de verificación."""
    for indicador, (minimo, maximo, razon) in vp.RANGOS.items():
        assert minimo < maximo, indicador
        assert len(razon) > 20, f"{indicador} no explica de dónde sale su rango"
