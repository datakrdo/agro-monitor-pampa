import pandas as pd
import pytest

from agro.anomalia import (
    acierto_por_decada,
    anomalia_a_la_fecha,
    anomalias_por_decada,
)


def _curvas(valores_por_campania):
    filas = [
        {"depto_id": "A", "campania": c, "decada": i, "valor": v}
        for c, vs in valores_por_campania.items()
        for i, v in enumerate(vs)
    ]
    return pd.DataFrame(filas)


def test_anomalia_a_la_fecha_compara_misma_decada():
    curvas = _curvas(
        {
            "2021/2022": [1, 1, 1, 1],
            "2022/2023": [1, 1, 1, 1],
            "2023/2024": [1, 1, 1, 1],
            "2024/2025": [0.5, 0.5, 0.5],
        }
    )  # campaña en curso: 3 décadas
    r = anomalia_a_la_fecha(curvas, "2024/2025").iloc[0]
    assert r["decada"] == 2 and r["n_hist"] == 3
    assert (
        r["integral_actual"] == 1.5 and r["mediana_hist"] == 3.0
    )  # historia a la misma década, no a la 4ta
    assert r["anomalia_pct"] == -50 and r["percentil"] == 0


def test_anomalia_a_la_fecha_sin_historia_no_rompe():
    assert anomalia_a_la_fecha(_curvas({"2024/2025": [1, 1]}), "2024/2025").empty


def _curvas_y_pred():
    # Un depto, 3 campañas, 2 décadas: C0 por debajo de lo habitual, C1 igual, C2 por encima.
    curvas = pd.DataFrame(
        [
            {"depto_id": "A", "campania": c, "decada": d, "valor": v}
            for c, v in (("C0", 0.5), ("C1", 0.6), ("C2", 0.7))
            for d in (0, 1)
        ]
    )
    pred = pd.DataFrame(
        {"depto_id": "A", "campania": ["C0", "C1", "C2"], "y": [900, 1010, 1100], "base": 1000}
    )
    return curvas, pred


def test_acierto_por_decada_juzga_solo_las_anomalias_sobre_el_umbral():
    curvas, pred = _curvas_y_pred()
    a = acierto_por_decada(anomalias_por_decada(curvas), pred, umbral=5).set_index("decada")
    assert a.loc[1, "n"] == 3
    assert a.loc[1, "marcados"] == pytest.approx(
        2 / 3
    )  # C1 (anomalía 0%) es "normal" y no se juzga
    assert a.loc[1, "acierto"] == 1.0
    assert a.loc[1, "acierto_mala"] == 1.0 and a.loc[1, "acierto_buena"] == 1.0


def test_acierto_por_decada_cuenta_los_errores():
    curvas, pred = _curvas_y_pred()
    pred.loc[pred["campania"] == "C2", "y"] = 900  # C2 se ve mejor que lo habitual pero rindió peor
    a = acierto_por_decada(anomalias_por_decada(curvas), pred, umbral=5).set_index("decada")
    assert a.loc[1, "acierto"] == 0.5 and a.loc[1, "acierto_buena"] == 0.0
