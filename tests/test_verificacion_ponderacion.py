import ast

from encuesta_hogares import analysis, preprocessing, verificacion_ponderacion as vp, visualization

MODULOS = (analysis, preprocessing, visualization)


def test_toda_funcion_con_metodo_crudo_esta_en_la_allowlist():
    encontrados = [uso for modulo in MODULOS for uso in vp.usos_sin_revisar(modulo)]
    detalle = "\n".join(
        f"  - {u.modulo}.{u.funcion} (línea {u.linea}): usa .{u.metodo}() y no está en ALLOWLIST"
        for u in encontrados
    )
    assert not encontrados, (
        "Se encontraron funciones que calculan una estadística con un método "
        "sin ponderar (.mean()/.median()/.value_counts()) y no están "
        "documentadas en verificacion_ponderacion.ALLOWLIST:\n\n" + detalle +
        "\n\nSi es un caso legítimo (ej. opera sobre una tabla ya agregada, o "
        "cuenta unidades sin ponderador propio, como barrios), agregalo a "
        "ALLOWLIST con la razón. Si es un descuido, pondera la estadística "
        "por ponderador_hogar/ponderador_empleo/ponderador_fies según corresponda."
    )


def test_allowlist_no_tiene_entradas_obsoletas():
    obsoletas = vp.entradas_allowlist_obsoletas(*MODULOS)
    assert not obsoletas, (
        f"ALLOWLIST tiene funciones que ya no existen en {[m.__name__ for m in MODULOS]}: "
        f"{obsoletas} — revisar si se renombraron o se borraron, y limpiar la entrada."
    )


def test_usos_sin_revisar_detecta_una_funcion_no_listada():
    codigo = "def stat_nueva(df):\n    return df['x'].mean()\n"
    encontrados = vp._usos_en_arbol(ast.parse(codigo), "modulo_falso")

    assert len(encontrados) == 1
    assert encontrados[0].funcion == "stat_nueva"
    assert encontrados[0].metodo == "mean"


def test_usos_sin_revisar_no_marca_una_funcion_de_la_allowlist():
    codigo = "def grupos_con_muestra_chica(df, col):\n    return df[col].value_counts()\n"
    encontrados = vp._usos_en_arbol(ast.parse(codigo), "modulo_falso")

    assert encontrados == []
