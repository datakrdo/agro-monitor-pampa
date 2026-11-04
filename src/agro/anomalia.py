"""Lógica pura de campaña y anomalía. Sin GEE, sin red — recibe y
devuelve DataFrames, así se testea con fixtures y corre en la app sin
depender de credenciales.
"""

from __future__ import annotations

import pandas as pd

MIN_PUNTOS = 30  # con menos píxeles de cultivo la mediana del depto es ruido
UMBRAL_ANOMALIA = 5.0  # %: por debajo de este desvío contra la mediana histórica la campaña se muestra como "normal"


def ventana_extraccion(cultivo_cfg: dict, anio_inicio: int) -> tuple[str, str]:
    """[inicio, fin) de la ventana de extracción satelital y de las features
    climáticas (ext_mes_* en cultivos.yaml), como texto YYYY-MM-DD."""
    ini = pd.Timestamp(year=anio_inicio, month=cultivo_cfg["ext_mes_inicio"], day=1)
    anio_fin = anio_inicio + (cultivo_cfg["ext_mes_fin"] <= cultivo_cfg["ext_mes_inicio"])
    fin = pd.Timestamp(year=anio_fin, month=cultivo_cfg["ext_mes_fin"], day=1)
    return ini.strftime("%Y-%m-%d"), fin.strftime("%Y-%m-%d")


def etiqueta_campania(anio_inicio: int) -> str:
    """Convención MAGyP: la campaña se nombra por año de siembra/año+1,
    incluso para cultivos que no cruzan el año calendario (ej. trigo
    2023/2024 = sembrado en 2023)."""
    return f"{anio_inicio}/{anio_inicio + 1}"


def anomalia_a_la_fecha(
    curvas: pd.DataFrame, campania: str, decada: int | None = None
) -> pd.DataFrame:
    """Integral acumulada hasta la `decada` (posición 0, 1, ... dentro de la
    ventana) de `campania` contra la misma década de las demás campañas.

    curvas: depto_id, campania, decada, valor (curva suavizada del depto).
    Sin `decada` usa la última disponible de cada depto en `campania`, que
    es la comparación "a hoy" en una campaña en curso. Devuelve por depto:
    integral_actual, mediana_hist, p10_hist, p90_hist, anomalia_pct,
    percentil (0-100) y n_hist (campañas de comparación).
    """
    df = curvas.sort_values(["depto_id", "campania", "decada"]).copy()
    df["acum"] = df.groupby(["depto_id", "campania"])["valor"].cumsum()
    filas = []
    for depto_id, g in df.groupby("depto_id"):
        actual = g[g["campania"] == campania]
        if actual.empty:
            continue
        d = actual["decada"].max() if decada is None else decada
        a = actual.loc[actual["decada"] == d, "acum"]
        hist = g[(g["campania"] != campania) & (g["decada"] == d)]["acum"]
        if a.empty or hist.empty:
            continue
        med = hist.median()
        filas.append(
            {
                "depto_id": depto_id,
                "decada": d,
                "integral_actual": a.iloc[0],
                "mediana_hist": med,
                "p10_hist": hist.quantile(0.1),
                "p90_hist": hist.quantile(0.9),
                "anomalia_pct": (a.iloc[0] - med) / med * 100 if med else float("nan"),
                "percentil": (hist <= a.iloc[0]).mean() * 100,
                "n_hist": len(hist),
            }
        )
    return pd.DataFrame(filas)


def anomalias_por_decada(curvas: pd.DataFrame) -> pd.DataFrame:
    """`anomalia_a_la_fecha` de cada campaña en cada década: una fila por
    depto, campaña y década, con la columna `campania`."""
    return pd.concat(
        [
            anomalia_a_la_fecha(curvas, c, d).assign(campania=c)
            for c in sorted(curvas["campania"].unique())
            for d in sorted(curvas["decada"].unique())
        ],
        ignore_index=True,
    )


def acierto_por_decada(
    anomalias: pd.DataFrame, pred: pd.DataFrame, umbral: float = UMBRAL_ANOMALIA
) -> pd.DataFrame:
    """¿Acertó la anomalía a la fecha el signo del rinde (por arriba o por
    debajo del promedio histórico del depto)? Por década, sobre todos los
    deptos y campañas con rinde oficial.

    pred: depto_id, campania, y, base (salida de `rendimiento.loco`).
    Devuelve por década: `marcados` (parte con |anomalía| > umbral; el resto
    es "normal" y no se juzga), `acierto` (sobre los marcados),
    `acierto_sin_umbral` (sobre todos; 0,5 es tirar una moneda), y
    `acierto_mala` / `acierto_buena` (sobre los marcados en cada sentido).
    """
    t = anomalias.merge(pred[["depto_id", "campania", "y", "base"]], on=["depto_id", "campania"])
    t["real"] = t["y"] / t["base"] - 1

    def calc(g):
        m, mala, buena = (
            g[g["anomalia_pct"].abs() > umbral],
            g[g["anomalia_pct"] < -umbral],
            g[g["anomalia_pct"] > umbral],
        )
        return pd.Series(
            {
                "n": len(g),
                "marcados": len(m) / len(g),
                "acierto": ((m["anomalia_pct"] < 0) == (m["real"] < 0)).mean(),
                "acierto_sin_umbral": ((g["anomalia_pct"] < 0) == (g["real"] < 0)).mean(),
                "acierto_mala": (mala["real"] < 0).mean(),
                "acierto_buena": (buena["real"] > 0).mean(),
            }
        )

    return t.groupby("decada").apply(calc, include_groups=False).reset_index()
