from encuesta_hogares import config
from encuesta_hogares.data_loader import fix_mojibake, load_empleo, load_victimizacion


def test_fix_mojibake_replaces_broken_char():
    assert fix_mojibake("Ba¦ados de Carrasco") == "Bañados de Carrasco"


def test_fix_mojibake_leaves_clean_text_untouched():
    assert fix_mojibake("Pocitos") == "Pocitos"


def test_fix_mojibake_ignores_non_string_values():
    assert fix_mojibake(None) is None
    assert fix_mojibake(42) == 42


def test_load_empleo_concatena_los_12_meses_y_renombra(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2030"
    carpeta.mkdir()
    encabezado = ",".join(config.EMPLEO_COLUMNS)
    for mes in range(1, 13):
        fila = f"1,1,{mes},MONTEVIDEO,1,30,2,Empleado,Formal,1. CB incompleto o menos,0,0,150.5"
        (carpeta / f"ECH_{mes:02d}_30.csv").write_text(f"{encabezado}\n{fila}\n")

    df = load_empleo(2030)

    assert len(df) == 12
    assert sorted(df["mes"].unique()) == list(range(1, 13))
    assert "condicion_actividad_cod" in df.columns
    assert "ponderador_empleo" in df.columns
    assert "edad" in df.columns


def test_load_victimizacion_agrega_departamento_por_join(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    carpeta = tmp_path / "2030"
    carpeta.mkdir()

    encabezado_v = ",".join(config.VICTIMIZACION_COLUMNS)
    fila_v = "1,1,1," + ",".join(["0"] * 18) + ",120.0"
    (carpeta / "ECH_VICTIMIZACION_S2_2030.csv").write_text(f"{encabezado_v}\n{fila_v}\n")

    for mes in range(7, 13):
        (carpeta / f"ECH_{mes:02d}_30.csv").write_text("ID,nom_dpto\n1,MONTEVIDEO\n")

    df = load_victimizacion(2030)

    assert len(df) == 1
    assert df.loc[0, "departamento"] == "MONTEVIDEO"
    assert "ponderador_victimizacion" in df.columns
