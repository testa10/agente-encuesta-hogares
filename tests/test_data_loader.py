from encuesta_hogares.data_loader import fix_mojibake


def test_fix_mojibake_replaces_broken_char():
    assert fix_mojibake("Ba¦ados de Carrasco") == "Bañados de Carrasco"


def test_fix_mojibake_leaves_clean_text_untouched():
    assert fix_mojibake("Pocitos") == "Pocitos"


def test_fix_mojibake_ignores_non_string_values():
    assert fix_mojibake(None) is None
    assert fix_mojibake(42) == 42
