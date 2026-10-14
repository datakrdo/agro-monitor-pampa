"""Rendimiento departamental a partir de features satelitales y de clima,
validado leave-one-campaign-out (LOCO): cada campaña se predice con un
modelo entrenado solo en las demás, y el promedio histórico del depto
también sale solo de las campañas de entrenamiento.

El modelo no predice el nivel de rendimiento (eso lo da el depto) sino su
desvío respecto del promedio histórico del depto, a partir del desvío de
cada feature: "esta campaña, ¿mejor o peor que lo normal acá?".
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from agro.anomalia import MIN_PUNTOS  # noqa: F401  (lo usan los .query("... @MIN_PUNTOS"))

FEATURES = ["integral", "pico", "doy_pico", "lluvia_mm", "dias_calor", "balance_mm", "tmax_media"]
MODELOS = {
    "ridge": make_pipeline(StandardScaler(), Ridge(alpha=10.0)),
    "hgb": HistGradientBoostingRegressor(
        max_depth=3, learning_rate=0.05, max_iter=150, random_state=0
    ),
}


def armar_tabla(features: pd.DataFrame, clima: pd.DataFrame, magyp: pd.DataFrame) -> pd.DataFrame:
    """Una fila por depto y campaña con FEATURES e `y` (rendimiento MAGyP, kg/ha).
    `magyp` ya filtrado al cultivo. Descarta deptos con menos de MIN_PUNTOS."""
    y = magyp[["depto_id", "campania", "rendimiento_kgxha"]].rename(
        columns={"rendimiento_kgxha": "y"}
    )
    t = features.merge(clima, on=["depto_id", "campania"]).merge(y, on=["depto_id", "campania"])
    return (
        t.dropna(subset=FEATURES + ["y"])
        .query("y > 0 and n_puntos >= @MIN_PUNTOS")
        .reset_index(drop=True)
    )


def loco(tabla: pd.DataFrame, modelo, cols: list[str] = FEATURES) -> pd.DataFrame:
    """Predicción fuera de muestra: depto_id, campania, y, base (promedio
    histórico del depto en las otras campañas) y pred."""
    salidas = []
    for camp in sorted(tabla["campania"].unique()):
        pred = _estimar(
            tabla[tabla["campania"] != camp], tabla[tabla["campania"] == camp], modelo, cols
        )
        if not pred.empty:
            salidas.append(pred)
    return pd.concat(salidas, ignore_index=True)


def _estimar(tr: pd.DataFrame, te: pd.DataFrame, modelo, cols: list[str]) -> pd.DataFrame:
    """Entrena en `tr` y estima `te`; `y` queda NaN si `te` no la trae."""
    mu = tr.groupby("depto_id")[cols + ["y"]].mean()
    te = te[te["depto_id"].isin(mu.index)]
    if te.empty or len(tr) < 10:
        return pd.DataFrame()
    m = clone(modelo).fit(
        tr[cols].to_numpy() - mu.loc[tr["depto_id"], cols].to_numpy(),
        tr["y"].to_numpy() - mu.loc[tr["depto_id"], "y"].to_numpy(),
    )
    base = mu.loc[te["depto_id"], "y"].to_numpy()
    pred = base + m.predict(te[cols].to_numpy() - mu.loc[te["depto_id"], cols].to_numpy())
    return pd.DataFrame(
        {
            "depto_id": te["depto_id"].to_numpy(),
            "campania": te["campania"].to_numpy(),
            "y": te["y"].to_numpy() if "y" in te else np.nan,
            "base": base,
            "pred": pred,
        }
    )


def pronosticar(
    tabla: pd.DataFrame,
    features: pd.DataFrame,
    clima: pd.DataFrame,
    modelo,
    cols: list[str] = FEATURES,
) -> pd.DataFrame:
    """Estima las campañas que tienen features y clima pero todavía no rinde
    MAGyP, entrenando con todas las de `tabla`. Mismas columnas que `loco`, con `y` NaN."""
    t = features.merge(clima, on=["depto_id", "campania"])
    t = (
        t[~t["campania"].isin(tabla["campania"])]
        .dropna(subset=cols)
        .query("n_puntos >= @MIN_PUNTOS")
    )
    return _estimar(tabla, t, modelo, cols)


def metricas(pred: pd.DataFrame) -> pd.DataFrame:
    """RMSE (kg/ha) y MAPE (%) del modelo y de la línea base, por campaña y total."""

    def calc(g):
        return pd.Series(
            {
                "rmse_modelo": np.sqrt(((g["y"] - g["pred"]) ** 2).mean()),
                "rmse_base": np.sqrt(((g["y"] - g["base"]) ** 2).mean()),
                "mape_modelo": ((g["y"] - g["pred"]).abs() / g["y"]).mean() * 100,
                "mape_base": ((g["y"] - g["base"]).abs() / g["y"]).mean() * 100,
                "n": len(g),
            }
        )

    por = pred.groupby("campania").apply(calc, include_groups=False)
    return pd.concat([por, calc(pred).rename("total").to_frame().T])


def resumen_validacion(pred: pd.DataFrame, umbral_mala: float = -0.10) -> dict:
    """Cifras de la validación de un modelo (salida de `loco`) para mostrar.

    La campaña con peor desvío medio contra la línea base (la sequía, si la hay)
    domina el RMSE total, así que se informa también la mejora sin ella.
    `precision_mala`: de lo que el modelo anticipa por debajo de `umbral_mala`
    contra la base, qué parte terminó realmente por debajo; `mala_era_buena`: qué
    parte terminó por encima de la base en la misma proporción.
    """
    t = pred.assign(real=pred["y"] / pred["base"] - 1, previsto=pred["pred"] / pred["base"] - 1)
    peor = t.groupby("campania")["real"].mean().idxmin()
    tot, sin = metricas(pred).loc["total"], metricas(pred[pred["campania"] != peor]).loc["total"]
    mala = t[t["previsto"] < umbral_mala]
    mejora = lambda m: 100 * (1 - m["rmse_modelo"] / m["rmse_base"])
    return {
        "n": int(tot["n"]),
        "n_campanias": int(t["campania"].nunique()),
        "n_deptos": int(t["depto_id"].nunique()),
        "rmse_modelo": float(tot["rmse_modelo"]),
        "rmse_base": float(tot["rmse_base"]),
        "mejora": float(mejora(tot)),
        "campania_peor": peor,
        "mejora_sin_peor": float(mejora(sin)),
        "acierto_signo": float(((t["previsto"] < 0) == (t["real"] < 0)).mean()),
        "n_mala": len(mala),
        "precision_mala": float((mala["real"] < umbral_mala).mean()),
        "mala_era_buena": float((mala["real"] > -umbral_mala).mean()),
    }
