import numpy as np
import pandas as pd

from agro import rendimiento
from agro.rendimiento import MODELOS, loco, metricas

COLS = ["integral"]


def _tabla(seed=0):
    rng = np.random.default_rng(seed)
    filas = []
    for d in range(20):
        nivel, ndvi0 = 2000 + 100 * d, 8 + 0.1 * d
        for c in range(5):
            dev = rng.normal(0, 1)
            filas.append(
                {
                    "depto_id": f"D{d}",
                    "campania": f"C{c}",
                    "integral": ndvi0 + dev,
                    "y": nivel + 300 * dev,
                }
            )
    return pd.DataFrame(filas)


def test_loco_no_filtra_la_campania_de_test():
    t = _tabla()
    p1 = loco(t, MODELOS["ridge"], COLS)
    t2 = t.copy()
    t2.loc[t2["campania"] == "C2", "y"] += (
        5000  # cambiar el rinde de C2 no puede cambiar su predicción
    )
    p2 = loco(t2, MODELOS["ridge"], COLS)
    a, b = (p[p["campania"] == "C2"].sort_values("depto_id") for p in (p1, p2))
    assert np.allclose(a["pred"], b["pred"]) and np.allclose(a["base"], b["base"])


def test_modelo_le_gana_a_la_linea_base_si_hay_senal():
    m = metricas(loco(_tabla(), MODELOS["ridge"], COLS))
    assert m.loc["total", "rmse_modelo"] < m.loc["total", "rmse_base"]


def test_armar_tabla_une_y_descarta_faltantes_y_deptos_con_pocos_puntos():
    f = pd.DataFrame(
        {
            "depto_id": ["A", "B", "D"],
            "campania": "C",
            "n_puntos": [300, 300, 5],
            **{c: 1.0 for c in ["integral", "pico", "doy_pico"]},
        }
    )
    c = pd.DataFrame(
        {
            "depto_id": ["A", "B", "D"],
            "campania": "C",
            "lluvia_mm": 1.0,
            "dias_calor": 1,
            "balance_mm": 1.0,
            "tmax_media": 1.0,
        }
    )
    m = pd.DataFrame(
        {"depto_id": ["A", "B", "D"], "campania": "C", "rendimiento_kgxha": [3000, 0, 2500]}
    )
    t = rendimiento.armar_tabla(f, c, m)
    assert list(t["depto_id"]) == ["A"] and t["y"].iloc[0] == 3000


def test_resumen_validacion_separa_la_peor_campania():
    # C1 es una sequía: rinde la mitad de la base y el modelo lo anticipa a medias.
    pred = pd.DataFrame(
        {
            "depto_id": ["A", "B", "A", "B"],
            "campania": ["C0", "C0", "C1", "C1"],
            "y": [1010, 990, 500, 500],
            "base": [1000, 1000, 1000, 1000],
            "pred": [1000, 1000, 800, 800],
        }
    )
    r = rendimiento.resumen_validacion(pred)
    assert r["campania_peor"] == "C1" and r["n"] == 4 and r["n_campanias"] == 2
    assert (
        r["mejora"] > 0 and r["mejora_sin_peor"] < r["mejora"]
    )  # sin la sequía casi no hay qué mejorar
    assert r["n_mala"] == 2 and r["precision_mala"] == 1.0 and r["mala_era_buena"] == 0.0


def test_pronosticar_estima_solo_campanias_sin_rinde():
    t = _tabla()
    nueva = t[t["campania"] == "C0"].assign(campania="C9", n_puntos=999).drop(columns="y")
    p = rendimiento.pronosticar(t, nueva, nueva[["depto_id", "campania"]], MODELOS["ridge"], COLS)
    assert set(p["campania"]) == {"C9"} and len(p) == 20 and p["y"].isna().all()
    assert (
        rendimiento.pronosticar(
            t, t.assign(n_puntos=999), t[["depto_id", "campania"]], MODELOS["ridge"], COLS
        )
    ).empty
