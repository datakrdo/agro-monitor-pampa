"""Suavizado y fenología de series NDVI por década. Funciones puras.

Whittaker (Eilers 2003) rellena los huecos por nubes y sacude el ruido
sin ventanas ni parámetros de forma: minimiza la infidelidad + lambda por
la rugosidad (segunda diferencia). Los huecos (NaN) llevan peso 0.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse.linalg import spsolve


def whittaker(y: np.ndarray, lam: float = 2.0) -> np.ndarray:
    """Serie suavizada, sin NaN. Con < 3 valores válidos devuelve todo NaN."""
    y = np.asarray(y, dtype=float)
    w = ~np.isnan(y)
    if w.sum() < 3:
        return np.full_like(y, np.nan)
    n = len(y)
    D = sparse.diags([1.0, -2.0, 1.0], [0, 1, 2], shape=(n - 2, n))
    A = sparse.diags(w.astype(float)) + lam * (D.T @ D)
    return spsolve(A.tocsc(), np.where(w, y, 0.0))


def features_curva(fechas: pd.DatetimeIndex, suave: np.ndarray, umbral: float = 0.5) -> dict:
    """Integral, pico y fechas de cobertura/senescencia de una curva suavizada.
    Cobertura = primera década donde la curva pasa `umbral` de la amplitud
    (base = mínimo antes del pico); senescencia = última década por encima.
    No son siembra ni madurez: la ventana de extracción (nov-may en soja) no
    incluye la siembra y corta la senescencia."""
    if np.isnan(suave).all():
        return {
            "integral": np.nan,
            "pico": np.nan,
            "fecha_pico": pd.NaT,
            "cobertura": pd.NaT,
            "senescencia": pd.NaT,
        }
    i_pico = int(np.nanargmax(suave))
    base = np.nanmin(suave[: i_pico + 1])
    corte = base + umbral * (suave[i_pico] - base)
    por_encima = np.nonzero(suave >= corte)[0]
    return {
        "integral": float(np.nansum(suave)),
        "pico": float(suave[i_pico]),
        "fecha_pico": fechas[i_pico],
        "cobertura": fechas[por_encima[0]],
        "senescencia": fechas[por_encima[-1]],
    }


def curvas_punto(serie: pd.DataFrame, lam: float = 2.0, col: str = "NDVI") -> pd.DataFrame:
    """serie: punto_idx, fecha, `col` (todas las décadas de un depto y una
    campaña). Devuelve la matriz punto x fecha ya suavizada."""
    m = serie.pivot(index="punto_idx", columns="fecha", values=col).sort_index(axis=1)
    return pd.DataFrame(
        np.vstack([whittaker(r, lam) for r in m.to_numpy()]), index=m.index, columns=m.columns
    )


def features_depto(serie: pd.DataFrame, lam: float = 2.0, n_boot: int = 200, seed: int = 0) -> dict:
    """Features de un depto y campaña: mediana entre puntos de cada feature
    y IC 90% de la integral por bootstrap de puntos. Fechas como día del año."""
    curvas = curvas_punto(serie, lam)
    filas = pd.DataFrame([features_curva(curvas.columns, r) for r in curvas.to_numpy()]).dropna(
        subset=["integral"]
    )
    if filas.empty:
        return {}
    rng = np.random.default_rng(seed)
    integral = filas["integral"].to_numpy()
    boot = [np.median(rng.choice(integral, len(integral))) for _ in range(n_boot)]
    dia = lambda c: float(filas[c].dt.dayofyear.median())
    return {
        "integral": float(np.median(integral)),
        "integral_p5": float(np.percentile(boot, 5)),
        "integral_p95": float(np.percentile(boot, 95)),
        "pico": float(filas["pico"].median()),
        "doy_pico": dia("fecha_pico"),
        "doy_cobertura": dia("cobertura"),
        "doy_senescencia": dia("senescencia"),
        "n_puntos": len(filas),
    }


def curva_depto(serie: pd.DataFrame, lam: float = 2.0) -> pd.Series:
    """Curva del depto: mediana entre puntos de las curvas suavizadas, por fecha."""
    return curvas_punto(serie, lam).median()
