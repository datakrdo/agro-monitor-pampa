import numpy as np
import pandas as pd

from agro import fenologia


def _campana(n=15):
    # campana sintetica: campana de Gauss con pico en la posicion 8
    x = np.arange(n)
    return 0.2 + 0.6 * np.exp(-((x - 8) ** 2) / 12)


def test_whittaker_rellena_huecos_y_sigue_la_curva():
    real = _campana()
    y = real.copy()
    y[[4, 5, 11]] = np.nan
    s = fenologia.whittaker(y, lam=1.0)
    assert not np.isnan(s).any()
    assert np.abs(s - real).max() < 0.1
    assert s.argmax() == 8


def test_whittaker_con_pocos_datos_devuelve_nan():
    assert np.isnan(fenologia.whittaker(np.array([np.nan, 0.5, np.nan, np.nan]))).all()


def test_features_curva_pico_cobertura_senescencia():
    fechas = pd.date_range("2025-01-01", periods=15, freq="10D")
    f = fenologia.features_curva(fechas, _campana())
    assert f["fecha_pico"] == fechas[8]
    assert f["cobertura"] < f["fecha_pico"] < f["senescencia"]
    assert abs(f["pico"] - 0.8) < 1e-9


def test_features_depto_mediana_e_ic():
    fechas = pd.date_range("2025-01-01", periods=15, freq="10D")
    rng = np.random.default_rng(0)
    filas = [
        {"punto_idx": p, "fecha": f, "NDVI": v + rng.normal(0, 0.02)}
        for p in range(30)
        for f, v in zip(fechas, _campana())
    ]
    r = fenologia.features_depto(pd.DataFrame(filas))
    assert r["n_puntos"] == 30
    assert r["integral_p5"] <= r["integral"] <= r["integral_p95"]
    assert abs(r["pico"] - 0.8) < 0.1
